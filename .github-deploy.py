#!/usr/bin/env python3
"""
Mini-Kuber GitHub Actions Replacement
Complete CI/CD pipeline in Python - replaces complex workflow YAML

This file replaces .github/workflows/deploy.yml entirely.
Run with: python .github-deploy.py

Features:
- Automatic testing on PRs
- Branch-based deployments
- Security scanning
- Documentation updates
- Release automation
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitHubActions:
    """GitHub Actions environment utilities"""
    
    @staticmethod
    def is_github_actions() -> bool:
        return os.getenv('GITHUB_ACTIONS') == 'true'
    
    @staticmethod
    def get_event() -> str:
        return os.getenv('GITHUB_EVENT_NAME', 'unknown')
    
    @staticmethod
    def get_branch() -> str:
        return os.getenv('GITHUB_REF_NAME', 'main')
    
    @staticmethod
    def get_commit() -> str:
        return os.getenv('GITHUB_SHA', 'unknown')[:7]
    
    @staticmethod
    def get_repo() -> str:
        return os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
    
    @staticmethod
    def is_pr() -> bool:
        return GitHubActions.get_event() == 'pull_request'
    
    @staticmethod
    def is_main_branch() -> bool:
        return GitHubActions.get_branch() in ['main', 'master']
    
    @staticmethod
    def set_output(name: str, value: str):
        """Set GitHub Actions output"""
        if GitHubActions.is_github_actions():
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write(f"{name}={value}\n")
    
    @staticmethod
    def log_group(title: str):
        """Create collapsible log group"""
        if GitHubActions.is_github_actions():
            print(f"::group::{title}")
        else:
            print(f"📋 {title}")
    
    @staticmethod
    def end_group():
        """End log group"""
        if GitHubActions.is_github_actions():
            print("::endgroup::")


class TestRunner:
    """Run tests and validations"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
    
    def run_python_tests(self) -> bool:
        """Test Python templates and examples"""
        print("🐍 Testing Python templates...")
        
        # Test mini-kuber.py imports and basic functionality
        try:
            result = subprocess.run([
                sys.executable, '-c', 
                """
import sys
sys.path.append('.')
from mini_kuber import Deployment, Service, deploy
print('✅ mini-kuber.py imports successfully')

# Test basic functionality
app = Deployment('test', 'nginx:latest')
service = Service('test-svc', app)
print('✅ Basic resource creation works')

# Test deployment (dry run)
success = deploy(app, service, dry_run=True, apply=False)
print(f'✅ Deployment test: {success}')
"""
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"❌ Python test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Python test error: {e}")
            return False
    
    def run_javascript_tests(self) -> bool:
        """Test JavaScript templates"""
        print("🟨 Testing JavaScript templates...")
        
        try:
            # Check if Node.js is available
            subprocess.run(['node', '--version'], capture_output=True, check=True)
            
            # Test mini-kuber.js
            result = subprocess.run([
                'node', '-e',
                """
try {
    const { Deployment, Service, deploy } = require('./mini-kuber.js');
    console.log('✅ mini-kuber.js imports successfully');
    
    // Test basic functionality
    const app = new Deployment('test', {image: 'nginx:latest'});
    const service = new Service('test-svc', app);
    console.log('✅ Basic resource creation works');
    
    // Test deployment (dry run)
    const success = deploy(app, service, {dryRun: true, apply: false});
    console.log('✅ Deployment test works');
    
} catch (error) {
    console.error('❌ JavaScript test failed:', error.message);
    process.exit(1);
}
"""
            ], capture_output=True, text=True, cwd=self.root_dir)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"❌ JavaScript test failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("⚠️ Node.js not found, skipping JavaScript tests")
            return True
        except Exception as e:
            print(f"❌ JavaScript test error: {e}")
            return False
    
    def run_example_tests(self) -> bool:
        """Test example files"""
        print("📖 Testing examples...")
        
        examples_dir = self.root_dir / 'examples'
        if not examples_dir.exists():
            print("⚠️ No examples directory found")
            return True
        
        success = True
        
        # Test Python examples
        for example_file in examples_dir.glob('*.py'):
            try:
                result = subprocess.run([
                    sys.executable, str(example_file)
                ], capture_output=True, text=True, cwd=self.root_dir)
                
                if result.returncode == 0:
                    print(f"✅ {example_file.name} works")
                else:
                    print(f"❌ {example_file.name} failed: {result.stderr}")
                    success = False
                    
            except Exception as e:
                print(f"❌ Error testing {example_file.name}: {e}")
                success = False
        
        # Test JavaScript examples
        for example_file in examples_dir.glob('*.js'):
            try:
                result = subprocess.run([
                    'node', str(example_file)
                ], capture_output=True, text=True, cwd=self.root_dir)
                
                if result.returncode == 0:
                    print(f"✅ {example_file.name} works")
                else:
                    print(f"❌ {example_file.name} failed: {result.stderr}")
                    success = False
                    
            except FileNotFoundError:
                print(f"⚠️ Skipping {example_file.name} (Node.js not available)")
            except Exception as e:
                print(f"❌ Error testing {example_file.name}: {e}")
                success = False
        
        return success
    
    def run_security_scan(self) -> bool:
        """Basic security scanning"""
        print("🔒 Running security scan...")
        
        # Check for common security issues
        issues = []
        
        # Scan Python files for potential issues
        for py_file in self.root_dir.rglob('*.py'):
            try:
                content = py_file.read_text()
                
                # Check for hardcoded secrets
                if re.search(r'password\s*=\s*["\'][^"\']{8,}["\']', content, re.IGNORECASE):
                    issues.append(f"Potential hardcoded password in {py_file}")
                
                if re.search(r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', content, re.IGNORECASE):
                    issues.append(f"Potential hardcoded API key in {py_file}")
                
                # Check for shell injection risks
                if 'shell=True' in content:
                    issues.append(f"Shell=True usage in {py_file} (potential security risk)")
                    
            except Exception:
                pass  # Skip files that can't be read
        
        # Scan JavaScript files
        for js_file in self.root_dir.rglob('*.js'):
            try:
                content = js_file.read_text()
                
                if re.search(r'password\s*:\s*["\'][^"\']{8,}["\']', content, re.IGNORECASE):
                    issues.append(f"Potential hardcoded password in {js_file}")
                    
            except Exception:
                pass
        
        if issues:
            print("⚠️ Security issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ No security issues detected")
            return True
    
    def validate_documentation(self) -> bool:
        """Validate documentation is up to date"""
        print("📚 Validating documentation...")
        
        required_files = [
            'README.md',
            'docs/getting-started.md'
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                print(f"❌ Missing required documentation: {file_path}")
                return False
            
            # Check if file is not empty
            if full_path.stat().st_size < 100:
                print(f"❌ Documentation file too short: {file_path}")
                return False
        
        print("✅ Documentation validation passed")
        return True
    
    def run_all_tests(self) -> bool:
        """Run complete test suite"""
        GitHubActions.log_group("Running Mini-Kuber Test Suite")
        
        tests = [
            ("Python Templates", self.run_python_tests),
            ("JavaScript Templates", self.run_javascript_tests),
            ("Examples", self.run_example_tests),
            ("Security Scan", self.run_security_scan),
            ("Documentation", self.validate_documentation)
        ]
        
        results = {}
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"Running {test_name}...")
            print('='*50)
            
            try:
                result = test_func()
                results[test_name] = result
                
                if result:
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
                    all_passed = False
                    
            except Exception as e:
                print(f"💥 {test_name} CRASHED: {e}")
                results[test_name] = False
                all_passed = False
        
        GitHubActions.end_group()
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST RESULTS SUMMARY")
        print('='*60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<20} {status}")
        
        print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed


class Deployer:
    """Handle deployments and releases"""
    
    def __init__(self):
        self.branch = GitHubActions.get_branch()
        self.commit = GitHubActions.get_commit()
        self.repo = GitHubActions.get_repo()
    
    def should_deploy(self) -> bool:
        """Determine if deployment should happen"""
        # Deploy only on main branch, not on PRs
        return GitHubActions.is_main_branch() and not GitHubActions.is_pr()
    
    def create_release_if_tagged(self) -> bool:
        """Create GitHub release if this is a tag push"""
        try:
            # Check if this is a tag
            ref = os.getenv('GITHUB_REF', '')
            if not ref.startswith('refs/tags/'):
                return True  # Not a tag, that's fine
            
            tag = ref.replace('refs/tags/', '')
            print(f"🏷️ Tag detected: {tag}")
            
            # Generate changelog from commits (simplified)
            changelog = self.generate_changelog()
            
            # Create release notes
            release_notes = f"""
# Mini-Kuber {tag}

## What's Changed
{changelog}

## Installation

### Python
```bash
curl -O https://raw.githubusercontent.com/{self.repo}/main/mini-kuber.py
```

### JavaScript
```bash  
curl -O https://raw.githubusercontent.com/{self.repo}/main/mini-kuber.js
```

## Quick Start
Check out the [examples](examples/) and [documentation](docs/getting-started.md).
"""
            
            print(f"📝 Generated release notes for {tag}")
            GitHubActions.set_output('release_tag', tag)
            GitHubActions.set_output('release_notes', release_notes)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Release creation failed: {e}")
            return False
    
    def generate_changelog(self) -> str:
        """Generate simple changelog from recent commits"""
        try:
            result = subprocess.run([
                'git', 'log', '--oneline', '-10', '--pretty=format:- %s'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return "- Various improvements and bug fixes"
                
        except Exception:
            return "- Various improvements and bug fixes"
    
    def update_documentation(self) -> bool:
        """Update documentation with latest examples"""
        print("📚 Updating documentation...")
        
        try:
            # Could add logic here to auto-update README with new examples
            # For now, just validate it exists and is recent
            readme_path = Path('README.md')
            if readme_path.exists():
                print("✅ README.md is present")
                return True
            else:
                print("❌ README.md missing")
                return False
                
        except Exception as e:
            print(f"❌ Documentation update failed: {e}")
            return False


def main():
    """Main CI/CD pipeline"""
    print("🚀 Mini-Kuber CI/CD Pipeline Starting...")
    print("="*60)
    print(f"Event: {GitHubActions.get_event()}")
    print(f"Branch: {GitHubActions.get_branch()}")
    print(f"Commit: {GitHubActions.get_commit()}")
    print(f"Repository: {GitHubActions.get_repo()}")
    print(f"Is PR: {GitHubActions.is_pr()}")
    print("="*60)
    
    # Always run tests
    GitHubActions.log_group("Testing Phase")
    tester = TestRunner()
    tests_passed = tester.run_all_tests()
    GitHubActions.end_group()
    
    if not tests_passed:
        print("❌ Tests failed - stopping pipeline")
        GitHubActions.set_output('tests_passed', 'false')
        sys.exit(1)
    
    GitHubActions.set_output('tests_passed', 'true')
    
    # For pull requests, only run tests
    if GitHubActions.is_pr():
        print("✅ Pull request validation completed successfully")
        print("💡 Merge to main branch to trigger deployment")
        return
    
    # Deployment phase (only on main branch)
    deployer = Deployer()
    
    if deployer.should_deploy():
        GitHubActions.log_group("Deployment Phase")
        
        # Update documentation
        doc_success = deployer.update_documentation()
        
        # Handle releases
        release_success = deployer.create_release_if_tagged()
        
        if doc_success and release_success:
            print("✅ Deployment phase completed successfully")
            GitHubActions.set_output('deployed', 'true')
        else:
            print("⚠️ Deployment phase completed with warnings")
            GitHubActions.set_output('deployed', 'partial')
        
        GitHubActions.end_group()
    else:
        print("ℹ️ Skipping deployment (not main branch)")
        GitHubActions.set_output('deployed', 'false')
    
    print("\n🎉 Pipeline completed successfully!")
    
    # Summary for GitHub Actions
    if GitHubActions.is_github_actions():
        print("\n📊 Pipeline Summary:")
        print(f"Tests: {'✅ PASSED' if tests_passed else '❌ FAILED'}")
        print(f"Branch: {GitHubActions.get_branch()}")
        print(f"Commit: {GitHubActions.get_commit()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)