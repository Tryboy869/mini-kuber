#!/usr/bin/env python3
"""
GitHub Actions CI/CD Pipeline using Mini-Kuber
Replace complex workflow YAML with intelligent Python code

This example shows how Mini-Kuber can even replace GitHub Actions workflows
for Kubernetes deployments with intelligent, testable code.
"""

import os
import sys
from pathlib import Path

# Add mini-kuber to path if running as standalone
sys.path.append(str(Path(__file__).parent.parent))
from mini_kuber import *

class GitHubEnvironment:
    """GitHub Actions environment detection and utilities"""
    
    @staticmethod
    def is_github_actions():
        return os.getenv('GITHUB_ACTIONS') == 'true'
    
    @staticmethod
    def get_branch():
        return os.getenv('GITHUB_REF_NAME', 'main')
    
    @staticmethod
    def get_commit_sha():
        return os.getenv('GITHUB_SHA', 'unknown')[:7]
    
    @staticmethod
    def get_repo():
        return os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
    
    @staticmethod
    def is_main_branch():
        return GitHubEnvironment.get_branch() in ['main', 'master']
    
    @staticmethod
    def is_pull_request():
        return os.getenv('GITHUB_EVENT_NAME') == 'pull_request'


def create_deployment_config(branch: str, commit_sha: str) -> dict:
    """
    Smart deployment configuration based on git context
    This is impossible to do cleanly in YAML!
    """
    
    # Base configuration
    config = {
        'replicas': 1,
        'resources': 'small',
        'namespace': 'development',
        'domain': 'dev.example.com'
    }
    
    # Branch-specific logic (impossible in GitHub Actions YAML)
    if branch == 'main':
        config.update({
            'replicas': 3,
            'resources': 'production',
            'namespace': 'production',
            'domain': 'api.example.com'
        })
    elif branch == 'staging':
        config.update({
            'replicas': 2,
            'resources': 'medium',
            'namespace': 'staging', 
            'domain': 'staging.example.com'
        })
    elif branch.startswith('feature/'):
        # Dynamic feature branch deployments
        feature_name = branch.replace('feature/', '').replace('/', '-')[:20]
        config.update({
            'namespace': f'feature-{feature_name}',
            'domain': f'{feature_name}.dev.example.com',
            'temporary': True,
            'ttl': '7d'  # Auto-cleanup after 7 days
        })
    
    # Add git metadata to all resources
    config['labels'] = {
        'git.branch': branch,
        'git.commit': commit_sha,
        'deployed.by': 'mini-kuber-ci',
        'deployed.at': str(int(time.time()))
    }
    
    return config


def get_resource_specs(env: str):
    """
    Environment-specific resource allocation
    Much cleaner than multiple YAML files!
    """
    specs = {
        'small': {
            'cpu_request': '100m', 'memory_request': '128Mi',
            'cpu_limit': '200m', 'memory_limit': '256Mi'
        },
        'medium': {
            'cpu_request': '200m', 'memory_request': '256Mi', 
            'cpu_limit': '500m', 'memory_limit': '512Mi'
        },
        'production': {
            'cpu_request': '500m', 'memory_request': '512Mi',
            'cpu_limit': '1000m', 'memory_limit': '1Gi'
        }
    }
    return specs.get(env, specs['small'])


def create_application_stack(app_name: str, image: str, config: dict):
    """
    Create complete application stack with intelligent defaults
    """
    resources_spec = get_resource_specs(config['resources'])
    
    # Main application
    app = Deployment(
        name=app_name,
        image=image,
        replicas=config['replicas'],
        port=8080,
        namespace=config['namespace'],
        env={
            'NODE_ENV': 'production' if config['namespace'] == 'production' else 'development',
            'DATABASE_URL': f"postgres://db.{config['namespace']}.svc.cluster.local:5432/app",
            'REDIS_URL': f"redis://redis.{config['namespace']}.svc.cluster.local:6379",
            'BRANCH': GitHubEnvironment.get_branch(),
            'COMMIT': GitHubEnvironment.get_commit_sha()
        },
        **resources_spec
    )
    
    # Add git labels
    app.labels.update(config['labels'])
    
    # Service
    service = serviceFor(app, service_type="ClusterIP")
    
    # Ingress for external access
    ingress = create_ingress(app_name, config['domain'], app, config['namespace'])
    
    resources = [app, service, ingress]
    
    # Auto-scaling for non-development environments
    if config['namespace'] != 'development':
        hpa = autoscaleFor(app, 
            min_replicas=config['replicas'],
            max_replicas=config['replicas'] * 3,
            cpu_percent=70
        )
        resources.append(hpa)
    
    # Temporary namespace cleanup for feature branches
    if config.get('temporary'):
        cleanup_job = create_cleanup_job(config['namespace'], config['ttl'])
        resources.append(cleanup_job)
    
    return resources


def create_ingress(name: str, domain: str, app: Deployment, namespace: str):
    """Create Ingress for external access"""
    ingress_yaml = {
        'apiVersion': 'networking.k8s.io/v1',
        'kind': 'Ingress',
        'metadata': {
            'name': f'{name}-ingress',
            'namespace': namespace,
            'labels': app.labels,
            'annotations': {
                'kubernetes.io/ingress.class': 'nginx',
                'cert-manager.io/cluster-issuer': 'letsencrypt-prod',
                'nginx.ingress.kubernetes.io/ssl-redirect': 'true'
            }
        },
        'spec': {
            'tls': [{
                'hosts': [domain],
                'secretName': f'{name}-tls'
            }],
            'rules': [{
                'host': domain,
                'http': {
                    'paths': [{
                        'path': '/',
                        'pathType': 'Prefix',
                        'backend': {
                            'service': {
                                'name': f'{app.name}-service',
                                'port': {'number': 80}
                            }
                        }
                    }]
                }
            }]
        }
    }
    
    # Create a generic resource for ingress
    class Ingress(Resource):
        def __init__(self, yaml_data):
            super().__init__(yaml_data['kind'], yaml_data['metadata']['name'], 
                           yaml_data['metadata']['namespace'])
            self._yaml_data = yaml_data
        
        def to_yaml(self):
            return self._yaml_data
    
    return Ingress(ingress_yaml)


def create_cleanup_job(namespace: str, ttl: str):
    """Create cleanup job for temporary deployments"""
    # Convert TTL to seconds (simplified)
    ttl_seconds = {'1d': 86400, '7d': 604800, '30d': 2592000}.get(ttl, 604800)
    
    cleanup_yaml = {
        'apiVersion': 'batch/v1',
        'kind': 'CronJob',
        'metadata': {
            'name': f'cleanup-{namespace}',
            'namespace': 'default'  # Cleanup job runs in default namespace
        },
        'spec': {
            'schedule': '0 2 * * *',  # Run at 2 AM daily
            'jobTemplate': {
                'spec': {
                    'template': {
                        'spec': {
                            'serviceAccountName': 'namespace-cleaner',
                            'containers': [{
                                'name': 'cleaner',
                                'image': 'bitnami/kubectl:latest',
                                'command': ['/bin/sh'],
                                'args': [
                                    '-c',
                                    f'''
                                    if [ $(($(date +%s) - {ttl_seconds})) -gt $(kubectl get ns {namespace} -o jsonpath="{{.metadata.creationTimestamp}}" | xargs -I{{}} date -d {{}} +%s) ]; then
                                        echo "Deleting expired namespace {namespace}"
                                        kubectl delete namespace {namespace}
                                    else
                                        echo "Namespace {namespace} not yet expired"
                                    fi
                                    '''
                                ]
                            }],
                            'restartPolicy': 'OnFailure'
                        }
                    }
                }
            }
        }
    }
    
    class CronJob(Resource):
        def __init__(self, yaml_data):
            super().__init__(yaml_data['kind'], yaml_data['metadata']['name'], 
                           yaml_data['metadata']['namespace'])
            self._yaml_data = yaml_data
        
        def to_yaml(self):
            return self._yaml_data
    
    return CronJob(cleanup_yaml)


def deploy_database_if_needed(namespace: str):
    """Deploy database only if it doesn't exist"""
    try:
        # Check if database already exists
        import subprocess
        result = subprocess.run(['kubectl', 'get', 'statefulset', 'postgres', '-n', namespace],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"📦 Database already exists in {namespace}")
            return []
        
    except FileNotFoundError:
        pass  # kubectl not available, proceed with deployment
    
    print(f"📦 Creating database in {namespace}")
    
    # Database deployment
    db_resources = database(
        name="postgres",
        image="postgres:13",
        options={
            'storage': '20Gi',
            'namespace': namespace,
            'env': {
                'POSTGRES_DB': 'app',
                'POSTGRES_USER': 'app',
                'POSTGRES_PASSWORD': 'secure-password-123'
            }
        }
    )
    
    # Redis cache
    redis = Deployment(
        name="redis",
        image="redis:7",
        port=6379,
        namespace=namespace,
        replicas=1
    )
    
    redis_service = serviceFor(redis)
    
    return db_resources + [redis, redis_service]


def run_tests():
    """
    Run tests before deployment
    This kind of logic is awkward in GitHub Actions YAML
    """
    print("🧪 Running tests...")
    
    # Unit tests
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Tests failed!")
            print(result.stdout)
            print(result.stderr)
            return False
        
        print("✅ All tests passed!")
        return True
        
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True


def main():
    """
    Main CI/CD pipeline logic
    This replaces complex GitHub Actions workflow YAML!
    """
    
    print("🚀 Mini-Kuber CI/CD Pipeline")
    print("=" * 50)
    
    # Get deployment context
    branch = GitHubEnvironment.get_branch()
    commit_sha = GitHubEnvironment.get_commit_sha()
    repo = GitHubEnvironment.get_repo()
    is_pr = GitHubEnvironment.is_pull_request()
    
    print(f"📋 Branch: {branch}")
    print(f"📋 Commit: {commit_sha}")
    print(f"📋 Repository: {repo}")
    print(f"📋 Is PR: {is_pr}")
    
    # Skip deployment for PRs (just run tests)
    if is_pr:
        print("🔍 Pull Request detected - running tests only")
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Run tests first
    if not run_tests():
        print("❌ Tests failed, aborting deployment")
        sys.exit(1)
    
    # Create deployment configuration
    config = create_deployment_config(branch, commit_sha)
    print(f"📋 Target namespace: {config['namespace']}")
    print(f"📋 Domain: {config['domain']}")
    print(f"📋 Replicas: {config['replicas']}")
    
    # Build image tag from repo and commit
    repo_name = repo.split('/')[-1]
    image_tag = f"ghcr.io/{repo.lower()}:{commit_sha}"
    
    print(f"📋 Image: {image_tag}")
    
    # Create application stack
    app_resources = create_application_stack(repo_name, image_tag, config)
    
    # Create database if needed
    db_resources = deploy_database_if_needed(config['namespace'])
    
    # Deploy everything
    all_resources = app_resources + db_resources
    
    print(f"\n🚀 Deploying {len(all_resources)} resources...")
    
    # Deploy with error handling
    try:
        success = deploy(*all_resources, dry_run=False)
        
        if success:
            print(f"✅ Deployment successful!")
            print(f"🌐 Application available at: https://{config['domain']}")
            
            # Set GitHub Actions output
            if GitHubEnvironment.is_github_actions():
                with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                    f.write(f"deployment_url=https://{config['domain']}\n")
                    f.write(f"namespace={config['namespace']}\n")
                    f.write(f"commit={commit_sha}\n")
        else:
            print("❌ Deployment failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()