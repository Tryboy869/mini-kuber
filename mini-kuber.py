#!/usr/bin/env python3
"""
Mini-Kuber Python Template
Replace YAML hell with intelligent Python code

Usage:
1. Copy this file to your project
2. Modify the examples at the bottom
3. Run: python your-deployment.py
4. Your Kubernetes resources are deployed

No framework to install, no complexity, just copy and adapt.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class Resource:
    """Base Kubernetes resource"""
    kind: str
    name: str
    namespace: str = "default"
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.labels:
            self.labels = {"app": self.name, "managed-by": "mini-kuber"}


class Deployment(Resource):
    """Kubernetes Deployment made simple"""
    
    def __init__(self, name: str, image: str, replicas: int = 1, port: Optional[int] = None,
                 env: Optional[Dict[str, str]] = None, namespace: str = "default",
                 cpu_request: str = "100m", memory_request: str = "128Mi",
                 cpu_limit: str = "500m", memory_limit: str = "512Mi",
                 auto_heal: bool = True, **kwargs):
        
        super().__init__(kind="Deployment", name=name, namespace=namespace)
        self.image = image
        self.replicas = replicas
        self.port = port
        self.env = env or {}
        self.cpu_request = cpu_request
        self.memory_request = memory_request
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        
        if auto_heal:
            self.labels["auto-heal"] = "true"
    
    def to_yaml(self) -> Dict[str, Any]:
        """Convert to Kubernetes YAML structure"""
        container = {
            "name": self.name,
            "image": self.image,
            "resources": {
                "requests": {"cpu": self.cpu_request, "memory": self.memory_request},
                "limits": {"cpu": self.cpu_limit, "memory": self.memory_limit}
            }
        }
        
        if self.port:
            container["ports"] = [{"containerPort": self.port}]
        
        if self.env:
            container["env"] = [{"name": k, "value": v} for k, v in self.env.items()]
        
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
                "annotations": self.annotations
            },
            "spec": {
                "replicas": self.replicas,
                "selector": {"matchLabels": {"app": self.name}},
                "template": {
                    "metadata": {"labels": {"app": self.name, **self.labels}},
                    "spec": {"containers": [container]}
                }
            }
        }


class Service(Resource):
    """Kubernetes Service made simple"""
    
    def __init__(self, name: str, target: Union[Deployment, str], port: int = 80,
                 target_port: Optional[int] = None, service_type: str = "ClusterIP",
                 namespace: str = "default", **kwargs):
        
        super().__init__(kind="Service", name=name, namespace=namespace)
        self.target = target.name if isinstance(target, Deployment) else target
        self.port = port
        self.target_port = target_port or (target.port if isinstance(target, Deployment) else port)
        self.service_type = service_type
    
    def to_yaml(self) -> Dict[str, Any]:
        """Convert to Kubernetes YAML structure"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
                "annotations": self.annotations
            },
            "spec": {
                "selector": {"app": self.target},
                "ports": [{
                    "port": self.port,
                    "targetPort": self.target_port,
                    "protocol": "TCP"
                }],
                "type": self.service_type
            }
        }


class StatefulSet(Resource):
    """Kubernetes StatefulSet for databases and stateful apps"""
    
    def __init__(self, name: str, image: str, replicas: int = 1, port: Optional[int] = None,
                 storage: str = "10Gi", storage_class: str = "standard",
                 env: Optional[Dict[str, str]] = None, namespace: str = "default", **kwargs):
        
        super().__init__(kind="StatefulSet", name=name, namespace=namespace)
        self.image = image
        self.replicas = replicas
        self.port = port
        self.storage = storage
        self.storage_class = storage_class
        self.env = env or {}
    
    def to_yaml(self) -> Dict[str, Any]:
        """Convert to Kubernetes YAML structure"""
        container = {
            "name": self.name,
            "image": self.image,
            "volumeMounts": [{
                "name": f"{self.name}-storage",
                "mountPath": "/var/lib/data"
            }]
        }
        
        if self.port:
            container["ports"] = [{"containerPort": self.port}]
        
        if self.env:
            container["env"] = [{"name": k, "value": v} for k, v in self.env.items()]
        
        return {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels
            },
            "spec": {
                "serviceName": self.name,
                "replicas": self.replicas,
                "selector": {"matchLabels": {"app": self.name}},
                "template": {
                    "metadata": {"labels": {"app": self.name}},
                    "spec": {"containers": [container]}
                },
                "volumeClaimTemplates": [{
                    "metadata": {"name": f"{self.name}-storage"},
                    "spec": {
                        "accessModes": ["ReadWriteOnce"],
                        "storageClassName": self.storage_class,
                        "resources": {"requests": {"storage": self.storage}}
                    }
                }]
            }
        }


class ConfigMap(Resource):
    """Kubernetes ConfigMap for configuration"""
    
    def __init__(self, name: str, data: Dict[str, str], namespace: str = "default", **kwargs):
        super().__init__(kind="ConfigMap", name=name, namespace=namespace)
        self.data = data
    
    def to_yaml(self) -> Dict[str, Any]:
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels
            },
            "data": self.data
        }


class Secret(Resource):
    """Kubernetes Secret for sensitive data"""
    
    def __init__(self, name: str, data: Dict[str, str], secret_type: str = "Opaque",
                 namespace: str = "default", **kwargs):
        super().__init__(kind="Secret", name=name, namespace=namespace)
        self.data = data
        self.secret_type = secret_type
    
    def to_yaml(self) -> Dict[str, Any]:
        import base64
        encoded_data = {k: base64.b64encode(v.encode()).decode() 
                       for k, v in self.data.items()}
        
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels
            },
            "type": self.secret_type,
            "data": encoded_data
        }


class HorizontalPodAutoscaler(Resource):
    """Kubernetes HPA for auto-scaling"""
    
    def __init__(self, name: str, target: Union[Deployment, str], 
                 min_replicas: int = 1, max_replicas: int = 10,
                 cpu_percent: int = 80, namespace: str = "default", **kwargs):
        super().__init__(kind="HorizontalPodAutoscaler", name=name, namespace=namespace)
        self.target = target.name if isinstance(target, Deployment) else target
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.cpu_percent = cpu_percent
    
    def to_yaml(self) -> Dict[str, Any]:
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.target
                },
                "minReplicas": self.min_replicas,
                "maxReplicas": self.max_replicas,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": self.cpu_percent
                        }
                    }
                }]
            }
        }


# Utility functions for common patterns
def serviceFor(deployment: Deployment, port: Optional[int] = None, 
               service_type: str = "ClusterIP") -> Service:
    """Create a service for a deployment"""
    return Service(
        name=f"{deployment.name}-service",
        target=deployment,
        port=port or deployment.port or 80,
        service_type=service_type,
        namespace=deployment.namespace
    )


def autoscaleFor(deployment: Deployment, min_replicas: int = 1, 
                max_replicas: int = 10, cpu_percent: int = 80) -> HorizontalPodAutoscaler:
    """Create autoscaling for a deployment"""
    return HorizontalPodAutoscaler(
        name=f"{deployment.name}-hpa",
        target=deployment,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        cpu_percent=cpu_percent,
        namespace=deployment.namespace
    )


def deploy(*resources: Resource, dry_run: bool = False, apply: bool = True) -> bool:
    """Deploy resources to Kubernetes cluster"""
    print(f"🚀 Deploying {len(resources)} resources...")
    
    all_yaml = []
    for resource in resources:
        yaml_content = resource.to_yaml()
        all_yaml.append(yaml_content)
        print(f"   📦 {resource.kind}: {resource.name}")
    
    if dry_run:
        print("💡 Dry run - YAML would be:")
        import yaml
        for yaml_content in all_yaml:
            print("---")
            print(yaml.dump(yaml_content, default_flow_style=False))
        return True
    
    if not apply:
        return True
    
    # Write to temporary file and apply with kubectl
    try:
        import yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            for i, yaml_content in enumerate(all_yaml):
                if i > 0:
                    f.write("---\n")
                yaml.dump(yaml_content, f, default_flow_style=False)
            f.flush()
            
            # Apply with kubectl
            result = subprocess.run(['kubectl', 'apply', '-f', f.name], 
                                  capture_output=True, text=True)
            
            Path(f.name).unlink()  # Clean up temp file
            
            if result.returncode == 0:
                print("✅ Deployment successful!")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return False
                
    except ImportError:
        print("❌ PyYAML required: pip install pyyaml")
        return False
    except FileNotFoundError:
        print("❌ kubectl not found. Please install kubectl and configure cluster access.")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False


# Smart deployment patterns
def webApp(name: str, image: str, replicas: int = 3, port: int = 80,
           env: Optional[Dict[str, str]] = None, auto_scale: bool = True) -> List[Resource]:
    """Deploy a complete web application with service and optional auto-scaling"""
    app = Deployment(name, image, replicas=replicas, port=port, env=env)
    service = serviceFor(app, service_type="LoadBalancer")
    
    resources = [app, service]
    
    if auto_scale:
        hpa = autoscaleFor(app, min_replicas=replicas, max_replicas=replicas * 3)
        resources.append(hpa)
    
    return resources


def database(name: str, image: str, storage: str = "10Gi", 
             env: Optional[Dict[str, str]] = None) -> List[Resource]:
    """Deploy a database with persistent storage"""
    db = StatefulSet(name, image, storage=storage, env=env)
    service = serviceFor(db)
    return [db, service]


# Example usage - Copy and modify for your needs
if __name__ == "__main__":
    print("🎯 Mini-Kuber Python Template Example")
    
    # Example 1: Simple web application
    web_resources = webApp(
        name="my-web-app",
        image="nginx:latest",
        replicas=2,
        port=80,
        auto_scale=True
    )
    
    # Example 2: Database
    db_resources = database(
        name="postgres-db",
        image="postgres:13",
        storage="20Gi",
        env={
            "POSTGRES_DB": "myapp",
            "POSTGRES_USER": "admin",
            "POSTGRES_PASSWORD": "secret123"
        }
    )
    
    # Example 3: Configuration and secrets
    config = ConfigMap("app-config", {
        "app.properties": "debug=true\nlog_level=info"
    })
    
    secret = Secret("app-secrets", {
        "api_key": "super-secret-key",
        "db_password": "ultra-secure-password"
    })
    
    # Deploy everything
    all_resources = web_resources + db_resources + [config, secret]
    
    # Uncomment to deploy (requires kubectl and cluster access)
    # deploy(*all_resources)
    
    # For testing, show what would be deployed
    deploy(*all_resources, dry_run=True)