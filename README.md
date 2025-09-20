# Mini-Kuber

Stop fighting YAML. Use real code for Kubernetes.

## The Problem

```yaml
# Traditional Kubernetes YAML (50+ lines of complexity)
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
  type: ClusterIP
```

## The Solution

```python
# Mini-Kuber Python (3 lines of intelligent code)
app = Deployment("my-app", image="nginx:latest", replicas=3, port=80)
service = Service("my-app-service", app, port=80)
deploy(app, service)
```

```javascript
// Mini-Kuber JavaScript (3 lines of intelligent code)
const app = deployment("my-app", {image: "nginx:latest", replicas: 3, port: 80});
const service = serviceFor(app, {port: 80});
deploy(app, service);
```

## Why Mini-Kuber?

- **90% Less Code**: Replace verbose YAML with intelligent, readable code
- **Auto-Healing**: Built-in monitoring and self-recovery
- **Real Logic**: Use if/else, loops, functions - impossible in YAML
- **Type Safety**: Catch errors before deployment, not after
- **Version Control**: Proper diff, merge, and code review
- **Copy-Paste Ready**: No framework to learn, just copy and adapt

## Quick Start

### Option 1: Python

1. Copy `mini-kuber.py` to your project
2. Modify for your needs:

```python
from mini_kuber import *

# Your application
web_app = Deployment(
    name="webapp", 
    image="myapp:latest", 
    replicas=3,
    port=8080,
    env={"DATABASE_URL": "postgres://..."}
)

database = StatefulSet(
    name="postgres",
    image="postgres:13",
    port=5432,
    storage="10Gi"
)

# Deploy everything
deploy(web_app, database, serviceFor(web_app), serviceFor(database))
```

### Option 2: JavaScript

1. Copy `mini-kuber.js` to your project
2. Modify for your needs:

```javascript
import { deployment, service, deploy } from './mini-kuber.js';

// Your application  
const webApp = deployment("webapp", {
    image: "myapp:latest",
    replicas: 3,
    port: 8080,
    env: {DATABASE_URL: "postgres://..."}
});

const database = statefulSet("postgres", {
    image: "postgres:13", 
    port: 5432,
    storage: "10Gi"
});

// Deploy everything
deploy(webApp, database, service(webApp), service(database));
```

## Examples

- **[Simple Web App](examples/webapp.py)** - Basic deployment with service
- **[Database Stack](examples/database.py)** - Persistent storage and secrets
- **[Microservices](examples/microservices.js)** - Multiple services communication
- **[Auto-Scaling](examples/autoscaling.py)** - Dynamic scaling based on load
- **[GitHub Actions CI/CD](examples/github-actions.py)** - Replace complex workflows

## Real-World Benefits

### Before (YAML Hell)
- 47 files, 2,340 lines of configuration
- 3 hours to add a new service
- Copy-paste errors break production
- No code reuse possible

### After (Mini-Kuber)
- 5 files, 180 lines of intelligent code
- 10 minutes to add a new service  
- Type checking prevents errors
- Functions, loops, conditions - real programming

## Migration from YAML

```python
# Convert existing YAML to Mini-Kuber
from tools.yaml_converter import convert

convert("my-deployment.yaml")  # Generates mini-kuber equivalent
```

## Contributing

1. Keep it simple - complexity is the enemy
2. Real examples over documentation
3. Copy-paste ready code only
4. Test on real Kubernetes clusters

## License

MIT - Use it, modify it, share it.

## Support

- **Issues**: GitHub Issues for bugs and questions
- **Discussions**: GitHub Discussions for ideas and help
- **Examples**: Check `/examples` folder for real use cases

---

**Stop writing YAML. Start writing code.**
