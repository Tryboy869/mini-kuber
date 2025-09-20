#!/usr/bin/env node

/**
 * Mini-Kuber JavaScript Template
 * Replace YAML hell with intelligent JavaScript code
 * 
 * Usage:
 * 1. Copy this file to your project
 * 2. Modify the examples at the bottom
 * 3. Run: node your-deployment.js
 * 4. Your Kubernetes resources are deployed
 * 
 * No framework to install, no complexity, just copy and adapt.
 */

const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

class Resource {
    constructor(kind, name, namespace = 'default') {
        this.kind = kind;
        this.name = name;
        this.namespace = namespace;
        this.labels = { app: name, 'managed-by': 'mini-kuber' };
        this.annotations = {};
    }
}

class Deployment extends Resource {
    /**
     * Kubernetes Deployment made simple
     */
    constructor(name, options = {}) {
        super('Deployment', name, options.namespace || 'default');
        
        this.image = options.image || 'nginx:latest';
        this.replicas = options.replicas || 1;
        this.port = options.port;
        this.env = options.env || {};
        this.cpuRequest = options.cpuRequest || '100m';
        this.memoryRequest = options.memoryRequest || '128Mi';
        this.cpuLimit = options.cpuLimit || '500m';
        this.memoryLimit = options.memoryLimit || '512Mi';
        
        if (options.autoHeal !== false) {
            this.labels['auto-heal'] = 'true';
        }
    }
    
    toYAML() {
        const container = {
            name: this.name,
            image: this.image,
            resources: {
                requests: { cpu: this.cpuRequest, memory: this.memoryRequest },
                limits: { cpu: this.cpuLimit, memory: this.memoryLimit }
            }
        };
        
        if (this.port) {
            container.ports = [{ containerPort: this.port }];
        }
        
        if (Object.keys(this.env).length > 0) {
            container.env = Object.entries(this.env).map(([name, value]) => ({
                name, value: String(value)
            }));
        }
        
        return {
            apiVersion: 'apps/v1',
            kind: 'Deployment',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels,
                annotations: this.annotations
            },
            spec: {
                replicas: this.replicas,
                selector: { matchLabels: { app: this.name } },
                template: {
                    metadata: { labels: { app: this.name, ...this.labels } },
                    spec: { containers: [container] }
                }
            }
        };
    }
}

class Service extends Resource {
    /**
     * Kubernetes Service made simple
     */
    constructor(name, target, options = {}) {
        super('Service', name, options.namespace || 'default');
        
        this.target = typeof target === 'string' ? target : target.name;
        this.port = options.port || 80;
        this.targetPort = options.targetPort || (target.port || this.port);
        this.type = options.type || 'ClusterIP';
    }
    
    toYAML() {
        return {
            apiVersion: 'v1',
            kind: 'Service',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels,
                annotations: this.annotations
            },
            spec: {
                selector: { app: this.target },
                ports: [{
                    port: this.port,
                    targetPort: this.targetPort,
                    protocol: 'TCP'
                }],
                type: this.type
            }
        };
    }
}

class StatefulSet extends Resource {
    /**
     * Kubernetes StatefulSet for databases and stateful apps
     */
    constructor(name, options = {}) {
        super('StatefulSet', name, options.namespace || 'default');
        
        this.image = options.image;
        this.replicas = options.replicas || 1;
        this.port = options.port;
        this.storage = options.storage || '10Gi';
        this.storageClass = options.storageClass || 'standard';
        this.env = options.env || {};
    }
    
    toYAML() {
        const container = {
            name: this.name,
            image: this.image,
            volumeMounts: [{
                name: `${this.name}-storage`,
                mountPath: '/var/lib/data'
            }]
        };
        
        if (this.port) {
            container.ports = [{ containerPort: this.port }];
        }
        
        if (Object.keys(this.env).length > 0) {
            container.env = Object.entries(this.env).map(([name, value]) => ({
                name, value: String(value)
            }));
        }
        
        return {
            apiVersion: 'apps/v1',
            kind: 'StatefulSet',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels
            },
            spec: {
                serviceName: this.name,
                replicas: this.replicas,
                selector: { matchLabels: { app: this.name } },
                template: {
                    metadata: { labels: { app: this.name } },
                    spec: { containers: [container] }
                },
                volumeClaimTemplates: [{
                    metadata: { name: `${this.name}-storage` },
                    spec: {
                        accessModes: ['ReadWriteOnce'],
                        storageClassName: this.storageClass,
                        resources: { requests: { storage: this.storage } }
                    }
                }]
            }
        };
    }
}

class ConfigMap extends Resource {
    /**
     * Kubernetes ConfigMap for configuration
     */
    constructor(name, data, options = {}) {
        super('ConfigMap', name, options.namespace || 'default');
        this.data = data;
    }
    
    toYAML() {
        return {
            apiVersion: 'v1',
            kind: 'ConfigMap',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels
            },
            data: this.data
        };
    }
}

class Secret extends Resource {
    /**
     * Kubernetes Secret for sensitive data
     */
    constructor(name, data, options = {}) {
        super('Secret', name, options.namespace || 'default');
        this.data = data;
        this.type = options.type || 'Opaque';
    }
    
    toYAML() {
        const encodedData = {};
        for (const [key, value] of Object.entries(this.data)) {
            encodedData[key] = Buffer.from(String(value)).toString('base64');
        }
        
        return {
            apiVersion: 'v1',
            kind: 'Secret',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels
            },
            type: this.type,
            data: encodedData
        };
    }
}

class HorizontalPodAutoscaler extends Resource {
    /**
     * Kubernetes HPA for auto-scaling
     */
    constructor(name, target, options = {}) {
        super('HorizontalPodAutoscaler', name, options.namespace || 'default');
        
        this.target = typeof target === 'string' ? target : target.name;
        this.minReplicas = options.minReplicas || 1;
        this.maxReplicas = options.maxReplicas || 10;
        this.cpuPercent = options.cpuPercent || 80;
    }
    
    toYAML() {
        return {
            apiVersion: 'autoscaling/v2',
            kind: 'HorizontalPodAutoscaler',
            metadata: {
                name: this.name,
                namespace: this.namespace,
                labels: this.labels
            },
            spec: {
                scaleTargetRef: {
                    apiVersion: 'apps/v1',
                    kind: 'Deployment',
                    name: this.target
                },
                minReplicas: this.minReplicas,
                maxReplicas: this.maxReplicas,
                metrics: [{
                    type: 'Resource',
                    resource: {
                        name: 'cpu',
                        target: {
                            type: 'Utilization',
                            averageUtilization: this.cpuPercent
                        }
                    }
                }]
            }
        };
    }
}

// Utility functions for common patterns
function serviceFor(deployment, options = {}) {
    return new Service(
        `${deployment.name}-service`,
        deployment,
        {
            port: options.port || deployment.port || 80,
            type: options.type || 'ClusterIP',
            namespace: deployment.namespace,
            ...options
        }
    );
}

function deploy(...resources) {
    const options = resources[resources.length - 1];
    const actualResources = typeof options === 'object' && options.dryRun !== undefined 
        ? resources.slice(0, -1) 
        : resources;
    const dryRun = options && options.dryRun;
    const apply = options && options.apply !== false;

    console.log(`🚀 Deploying ${actualResources.length} resources...`);
    
    const allYAML = [];
    for (const resource of actualResources) {
        const yamlContent = resource.toYAML();
        allYAML.push(yamlContent);
        console.log(`   📦 ${resource.kind}: ${resource.name}`);
    }
    
    if (dryRun) {
        console.log('💡 Dry run - YAML would be:');
        const yaml = require('js-yaml');
        for (const yamlContent of allYAML) {
            console.log('---');
            console.log(yaml.dump(yamlContent));
        }
        return true;
    }
    
    if (!apply) {
        return true;
    }
    
    try {
        const yaml = require('js-yaml');
        const tempFile = path.join(require('os').tmpdir(), `mini-kuber-${Date.now()}.yaml`);
        
        let yamlString = '';
        for (let i = 0; i < allYAML.length; i++) {
            if (i > 0) yamlString += '---\n';
            yamlString += yaml.dump(allYAML[i]);
        }
        
        fs.writeFileSync(tempFile, yamlString);
        
        try {
            execSync(`kubectl apply -f ${tempFile}`, { stdio: 'inherit' });
            console.log('✅ Deployment successful!');
            return true;
        } finally {
            fs.unlinkSync(tempFile);
        }
        
    } catch (error) {
        if (error.message.includes('js-yaml')) {
            console.log('❌ js-yaml required: npm install js-yaml');
        } else if (error.message.includes('kubectl')) {
            console.log('❌ kubectl not found. Please install kubectl and configure cluster access.');
        } else {
            console.log(`❌ Deployment error: ${error.message}`);
        }
        return false;
    }
}

// Smart deployment patterns
function webApp(name, image, options = {}) {
    const replicas = options.replicas || 3;
    const port = options.port || 80;
    const autoScale = options.autoScale !== false;
    
    const app = new Deployment(name, { 
        image, 
        replicas, 
        port, 
        env: options.env,
        namespace: options.namespace 
    });
    
    const service = serviceFor(app, { type: 'LoadBalancer' });
    const resources = [app, service];
    
    if (autoScale) {
        const hpa = autoscaleFor(app, {
            minReplicas: replicas,
            maxReplicas: replicas * 3
        });
        resources.push(hpa);
    }
    
    return resources;
}

function database(name, image, options = {}) {
    const db = new StatefulSet(name, {
        image,
        storage: options.storage || '10Gi',
        env: options.env,
        port: options.port,
        namespace: options.namespace
    });
    
    const service = serviceFor(db);
    return [db, service];
}

// Factory functions for cleaner syntax
function deployment(name, options) {
    return new Deployment(name, options);
}

function service(name, target, options) {
    return new Service(name, target, options);
}

function statefulSet(name, options) {
    return new StatefulSet(name, options);
}

function configMap(name, data, options) {
    return new ConfigMap(name, data, options);
}

function secret(name, data, options) {
    return new Secret(name, data, options);
}

function hpa(name, target, options) {
    return new HorizontalPodAutoscaler(name, target, options);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Deployment,
        Service,
        StatefulSet,
        ConfigMap,
        Secret,
        HorizontalPodAutoscaler,
        serviceFor,
        autoscaleFor,
        deploy,
        webApp,
        database,
        deployment,
        service,
        statefulSet,
        configMap,
        secret,
        hpa
    };
}

// Example usage - Copy and modify for your needs
if (require.main === module) {
    console.log('🎯 Mini-Kuber JavaScript Template Example');
    
    // Example 1: Simple web application
    const webResources = webApp('my-web-app', 'nginx:latest', {
        replicas: 2,
        port: 80,
        autoScale: true
    });
    
    // Example 2: Database
    const dbResources = database('postgres-db', 'postgres:13', {
        storage: '20Gi',
        env: {
            POSTGRES_DB: 'myapp',
            POSTGRES_USER: 'admin',
            POSTGRES_PASSWORD: 'secret123'
        }
    });
    
    // Example 3: Configuration and secrets
    const config = configMap('app-config', {
        'app.properties': 'debug=true\nlog_level=info'
    });
    
    const appSecret = secret('app-secrets', {
        api_key: 'super-secret-key',
        db_password: 'ultra-secure-password'
    });
    
    // Deploy everything
    const allResources = [...webResources, ...dbResources, config, appSecret];
    
    // Uncomment to deploy (requires kubectl and cluster access)
    // deploy(...allResources);
    
    // For testing, show what would be deployed
    deploy(...allResources, { dryRun: true });
}
            ...options
        }
    );
}

function autoscaleFor(deployment, options = {}) {
    return new HorizontalPodAutoscaler(
        `${deployment.name}-hpa`,
        deployment,
        {
            minReplicas: options.minReplicas || 1,
            maxReplicas: options.maxReplicas || 10,
            cpuPercent: options.cpuPercent || 80,
            namespace: deployment.namespace,