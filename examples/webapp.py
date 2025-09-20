#!/usr/bin/env python3
"""
Simple Web Application Example
Shows how to replace complex YAML with 10 lines of Python

BEFORE (Traditional YAML approach):
- deployment.yaml: 35 lines
- service.yaml: 15 lines  
- ingress.yaml: 20 lines
- hpa.yaml: 15 lines
Total: 85+ lines across 4 files

AFTER (Mini-Kuber approach):
- webapp.py: 10 lines
Total: 10 lines in 1 file
"""

import sys
from pathlib import Path

# Import mini-kuber (assumes mini-kuber.py is in parent directory)
sys.path.append(str(Path(__file__).parent.parent))
from mini_kuber import *

# Your web application - dead simple
def create_webapp():
    # Web application deployment
    app = Deployment(
        name="my-webapp",
        image="nginx:latest",
        replicas=3,
        port=80,
        env={
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "info"
        }
    )
    
    # Service to expose the app
    service = serviceFor(app, service_type="LoadBalancer")
    
    # Auto-scaling based on CPU usage
    autoscaler = autoscaleFor(app, min_replicas=2, max_replicas=10, cpu_percent=70)
    
    return [app, service, autoscaler]

def create_webapp_with_database():
    """Complete web app with database - still super simple"""
    
    # Web application
    web_resources = create_webapp()
    
    # Database 
    db_resources = database(
        name="webapp-db",
        image="postgres:13",
        storage="20Gi",
        env={
            "POSTGRES_DB": "webapp",
            "POSTGRES_USER": "webapp_user", 
            "POSTGRES_PASSWORD": "secure_password_123"
        }
    )
    
    # Configuration
    config = ConfigMap("webapp-config", {
        "database.url": "postgres://webapp-db-service:5432/webapp",
        "app.debug": "false",
        "app.workers": "4"
    })
    
    return web_resources + db_resources + [config]

if __name__ == "__main__":
    print("🌐 Creating simple web application...")
    
    # Option 1: Just web app
    # resources = create_webapp()
    
    # Option 2: Web app + database (uncomment to use)
    resources = create_webapp_with_database()
    
    print(f"📦 Created {len(resources)} resources")
    
    # Deploy to cluster (uncomment when ready)
    # deploy(*resources)
    
    # Show what would be deployed
    deploy(*resources, dry_run=True)
    
    print("\n💡 To deploy to your cluster:")
    print("   1. Make sure kubectl is configured")
    print("   2. Comment out the dry_run=True line")
    print("   3. Uncomment the deploy(*resources) line")
    print("   4. Run: python webapp.py")