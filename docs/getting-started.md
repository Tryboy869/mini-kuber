# Getting Started with Mini-Kuber

Stop writing YAML. Start writing code.

## Quick Setup (30 seconds)

### Option 1: Python
1. Copy `mini-kuber.py` to your project
2. Create your deployment:

```python
from mini_kuber import *

# Your app in 3 lines
app = Deployment("my-app", image="nginx:latest", replicas=3)
service = serviceFor(app, service_type="LoadBalancer")
deploy(app, service)
```

### Option 2: JavaScript  
1. Copy `mini-kuber.js` to your project
2. Create your deployment:

```javascript
const { deployment, serviceFor, deploy } = require('./mini-kuber.js');

// Your app in 3 lines
const app = deployment("my-app", {image: "nginx:latest", replicas: 3});
const service = serviceFor(app, {type: "LoadBalancer"});
deploy(app, service);
```

## Prerequisites

- `kubectl` installed and configured
- Access to a Kubernetes cluster
- Python 3.7+ or Node.js 14+ (depending on your choice)

**Python dependencies:**
```bash
pip install pyyaml  # Only dependency needed
```

**JavaScript dependencies:**
```bash
npm install js-yaml  # Only dependency needed
```

## Your First Deployment

### Simple Web App

```python
# webapp.py
from mini_kuber import *

# Create a complete web application
resources = webApp(
    name="my-website",
    image="nginx:latest", 
    replicas=2,
    auto_scale=True
)

# Deploy to cluster
deploy(*resources)
```

Run it:
```bash
python webapp.py
```

### With Database

```python  
# fullstack.py
from mini_kuber import *

# Web application
web = webApp("frontend", "myapp:latest", replicas=3)

# Database
db = database("postgres", "postgres:13", storage="20Gi", 
              env={"POSTGRES_DB": "myapp"})

# Deploy everything
deploy(*(web + db))
```

## Core Concepts

### Resources
Mini-Kuber provides simple classes for Kubernetes resources:

- **Deployment**: Your application containers
- **Service**: Network access to your app  
- **StatefulSet**: Databases and stateful apps
- **ConfigMap**: Configuration data
- **Secret**: Sensitive data
- **HorizontalPodAutoscaler**: Auto-scaling

### Smart Functions
Utility functions that do the thinking for you:

- `serviceFor(app)` - Creates service for deployment
- `autoscaleFor(app)` - Adds auto-scaling
- `webApp(name, image)` - Complete web app with service
- `database(name, image)` - Stateful database setup

### Environment Logic
Unlike YAML, you can use real programming:

```python
# Different config per environment
if environment == "production":
    replicas = 5
    resources = "large"  
else:
    replicas = 1
    resources = "small"

app = Deployment(name, image, replicas=replicas)
```

## Examples by Use Case

### Static Website
```python
# Just a static site with CDN
app = Deployment("website", "nginx:latest", replicas=2)
service = serviceFor(app, service_type="LoadBalancer")
deploy(app, service)
```

### API Server
```python
# API with database and caching  
api = Deployment("api", "myapi:latest", replicas=3, port=8080)
db = database("postgres", "postgres:13")
cache = Deployment("redis", "redis:7", replicas=1)

deploy(api, serviceFor(api), *db, cache, serviceFor(cache))
```

### Microservices
```javascript
// Multiple connected services
const frontend = deployment("frontend", {image: "frontend:latest"});
const api = deployment("api", {image: "api:latest", port: 8080});  
const db = statefulSet("database", {image: "postgres:13"});

deploy(
    frontend, serviceFor(frontend, {type: "LoadBalancer"}),
    api, serviceFor(api),
    db, serviceFor(db)
);
```

## Advanced Features

### Auto-Scaling
```python
# Scales between 2-10 pods based on CPU
app = Deployment("app", "myapp:latest", replicas=2)
hpa = autoscaleFor(app, min_replicas=2, max_replicas=10, cpu_percent=70)
deploy(app, serviceFor(app), hpa)
```

### Configuration Management  
```python
# Separate config from code
config = ConfigMap("app-config", {
    "database.url": "postgres://db:5432/app",
    "log.level": "info"
})

secrets = Secret("app-secrets", {
    "api.key": "secret-key-123",
    "db.password": "ultra-secure-password"  
})

deploy(app, config, secrets)
```

### Health Checks
```python
# Built-in health monitoring
app = Deployment("app", "myapp:latest", 
                health_check="/health",
                readiness_check="/ready")
```

## Real vs YAML Comparison

### Before: YAML Hell
```yaml
# deployment.yaml (35+ lines)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app  
    spec:
      containers:
      - name: my-app
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m  
            memory: 512Mi
---
# service.yaml (15+ lines)
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

### After: Mini-Kuber Magic
```python
# app.py (3 lines)
app = Deployment("my-app", "nginx:latest", replicas=3)  
service = serviceFor(app, service_type="LoadBalancer")
deploy(app, service)
```

**Result**: 50+ lines → 3 lines (95% reduction)

## Best Practices

### 1. Keep It Simple
```python
# Good: Clear and readable
app = webApp("api", "myapi:latest", replicas=3)

# Bad: Over-complicated  
app = Deployment("api", "myapi:latest", replicas=3, port=8080, 
                env={"A": "1", "B": "2"}, cpu_request="100m", 
                memory_request="128Mi", cpu_limit="500m")
```

### 2. Use Smart Functions
```python
# Good: Let Mini-Kuber do the work
resources = webApp("frontend", "react:latest", auto_scale=True)

# Bad: Manual resource creation
app = Deployment(...)
service = Service(...)  
hpa = HorizontalPodAutoscaler(...)
```

### 3. Environment-Specific Logic
```python
# Good: Real programming logic
def create_app(env):
    config = {
        "development": {"replicas": 1, "debug": True},
        "production": {"replicas": 5, "debug": False}
    }[env]
    
    return webApp("app", "myapp:latest", **config)

# Bad: Multiple YAML files for each environment  
```

### 4. Version Your Infrastructure
```python
# Good: Infrastructure as real code
def deploy_v2():
    # New feature flag
    return webApp("app", "myapp:v2", feature_flags={"new_ui": True})
    
# Bad: Manual YAML management
```

## Troubleshooting

### "kubectl not found"
Install kubectl: https://kubernetes.io/docs/tasks/tools/

### "ModuleNotFoundError: pyyaml"  
```bash
pip install pyyaml
```

### "Permission denied"
Check cluster access:
```bash
kubectl get nodes
```

### "Deployment failed"
Check resources:
```bash
kubectl get pods
kubectl describe pod <pod-name>
```

## Migration from YAML

### Automatic Conversion
Use the built-in converter:
```python
from tools.yaml_converter import convert
convert("my-deployment.yaml")  # Outputs mini-kuber equivalent
```

### Manual Migration
1. Identify your YAML resources
2. Find equivalent Mini-Kuber classes
3. Replace configuration with Python/JavaScript
4. Test deployment
5. Delete old YAML files

### Common Patterns

| YAML | Mini-Kuber |
|------|------------|
| `kind: Deployment` | `Deployment()` |
| `kind: Service` | `serviceFor()` |
| `kind: StatefulSet` | `database()` or `StatefulSet()` |
| `kind: ConfigMap` | `ConfigMap()` |
| `kind: Secret` | `Secret()` |

## Need Help?

- Check `/examples` folder for real use cases
- Look at existing deployments: `kubectl get all`
- Test with `dry_run=True` first
- Start simple, add complexity gradually

**Remember**: Mini-Kuber is just Python/JavaScript. If you can code, you can deploy to Kubernetes.

---

**Ready to deploy?** Copy a template, modify it, and run it. Your YAML days are over.