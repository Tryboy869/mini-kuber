#!/usr/bin/env node

/**
 * Microservices Architecture Example
 * Shows how to deploy multiple connected services with Mini-Kuber
 * 
 * BEFORE (Traditional approach):
 * - 15+ YAML files 
 * - Complex service discovery configuration
 * - Manual port management
 * - No business logic possible
 * 
 * AFTER (Mini-Kuber approach):
 * - 1 JavaScript file
 * - Intelligent service connections
 * - Dynamic configuration
 * - Real programming logic
 */

// Import mini-kuber (assumes mini-kuber.js is in same directory)
const { Deployment, Service, ConfigMap, Secret, deploy, serviceFor } = require('../mini-kuber.js');

class MicroserviceArchitecture {
    constructor(namespace = 'microservices') {
        this.namespace = namespace;
        this.services = [];
        this.configs = [];
        this.secrets = [];
    }
    
    // Frontend service
    createFrontend() {
        const frontend = new Deployment('frontend', {
            image: 'nginx:latest',
            replicas: 2,
            port: 80,
            namespace: this.namespace,
            env: {
                'API_GATEWAY_URL': 'http://api-gateway-service:8080',
                'ENVIRONMENT': 'production'
            }
        });
        
        const frontendService = serviceFor(frontend, { 
            type: 'LoadBalancer',
            port: 80 
        });
        
        this.services.push(frontend, frontendService);
        return this;
    }
    
    // API Gateway - routes requests to microservices
    createApiGateway() {
        const gateway = new Deployment('api-gateway', {
            image: 'nginx:latest', // Would be your API gateway image
            replicas: 3,
            port: 8080,
            namespace: this.namespace,
            env: {
                'USER_SERVICE_URL': 'http://user-service:3001',
                'ORDER_SERVICE_URL': 'http://order-service:3002',
                'PAYMENT_SERVICE_URL': 'http://payment-service:3003',
                'INVENTORY_SERVICE_URL': 'http://inventory-service:3004'
            }
        });
        
        const gatewayService = serviceFor(gateway);
        
        this.services.push(gateway, gatewayService);
        return this;
    }
    
    // User management microservice
    createUserService() {
        const userService = new Deployment('user-service', {
            image: 'node:16', // Would be your user service image
            replicas: 2,
            port: 3001,
            namespace: this.namespace,
            env: {
                'DATABASE_URL': 'postgres://user-db-service:5432/users',
                'REDIS_URL': 'redis://redis-service:6379',
                'JWT_SECRET': 'user-jwt-secret-key'
            }
        });
        
        const service = serviceFor(userService);
        
        this.services.push(userService, service);
        return this;
    }
    
    // Order processing microservice
    createOrderService() {
        const orderService = new Deployment('order-service', {
            image: 'node:16', // Would be your order service image  
            replicas: 3, // More replicas for high-traffic service
            port: 3002,
            namespace: this.namespace,
            env: {
                'DATABASE_URL': 'postgres://order-db-service:5432/orders',
                'PAYMENT_SERVICE_URL': 'http://payment-service:3003',
                'INVENTORY_SERVICE_URL': 'http://inventory-service:3004',
                'RABBITMQ_URL': 'amqp://rabbitmq-service:5672'
            }
        });
        
        const service = serviceFor(orderService);
        
        this.services.push(orderService, service);
        return this;
    }
    
    // Payment processing microservice
    createPaymentService() {
        const paymentService = new Deployment('payment-service', {
            image: 'node:16', // Would be your payment service image
            replicas: 2,
            port: 3003,
            namespace: this.namespace,
            env: {
                'DATABASE_URL': 'postgres://payment-db-service:5432/payments',
                'STRIPE_SECRET_KEY': 'stripe-secret-key',
                'ENCRYPTION_KEY': 'payment-encryption-key'
            },
            // Higher resource limits for security-critical service
            cpuRequest: '200m',
            memoryRequest: '256Mi',
            cpuLimit: '500m',
            memoryLimit: '512Mi'
        });
        
        const service = serviceFor(paymentService);
        
        this.services.push(paymentService, service);
        return this;
    }
    
    // Inventory management microservice
    createInventoryService() {
        const inventoryService = new Deployment('inventory-service', {
            image: 'node:16', // Would be your inventory service image
            replicas: 2,
            port: 3004,
            namespace: this.namespace,
            env: {
                'DATABASE_URL': 'postgres://inventory-db-service:5432/inventory',
                'REDIS_URL': 'redis://redis-service:6379'
            }
        });
        
        const service = serviceFor(inventoryService);
        
        this.services.push(inventoryService, service);
        return this;
    }
    
    // Shared database cluster
    createDatabases() {
        // User database
        const userDb = new StatefulSet('user-db', {
            image: 'postgres:13',
            port: 5432,
            storage: '10Gi',
            namespace: this.namespace,
            env: {
                'POSTGRES_DB': 'users',
                'POSTGRES_USER': 'user_service',
                'POSTGRES_PASSWORD': 'secure_user_password'
            }
        });
        
        // Order database
        const orderDb = new StatefulSet('order-db', {
            image: 'postgres:13',
            port: 5432,
            storage: '20Gi', // Orders need more storage
            namespace: this.namespace,
            env: {
                'POSTGRES_DB': 'orders',
                'POSTGRES_USER': 'order_service',
                'POSTGRES_PASSWORD': 'secure_order_password'
            }
        });
        
        // Payment database
        const paymentDb = new StatefulSet('payment-db', {
            image: 'postgres:13',
            port: 5432,
            storage: '15Gi',
            namespace: this.namespace,
            env: {
                'POSTGRES_DB': 'payments',
                'POSTGRES_USER': 'payment_service',
                'POSTGRES_PASSWORD': 'secure_payment_password'
            }
        });
        
        // Inventory database
        const inventoryDb = new StatefulSet('inventory-db', {
            image: 'postgres:13',
            port: 5432,
            storage: '10Gi',
            namespace: this.namespace,
            env: {
                'POSTGRES_DB': 'inventory',
                'POSTGRES_USER': 'inventory_service',
                'POSTGRES_PASSWORD': 'secure_inventory_password'
            }
        });
        
        // Create services for databases
        const dbServices = [
            serviceFor(userDb),
            serviceFor(orderDb),
            serviceFor(paymentDb),
            serviceFor(inventoryDb)
        ];
        
        this.services.push(userDb, orderDb, paymentDb, inventoryDb, ...dbServices);
        return this;
    }
    
    // Shared cache and message queue
    createSharedServices() {
        // Redis for caching
        const redis = new Deployment('redis', {
            image: 'redis:7',
            port: 6379,
            replicas: 1,
            namespace: this.namespace,
            env: {
                'REDIS_PASSWORD': 'redis_secure_password'
            }
        });
        
        // RabbitMQ for message queuing
        const rabbitmq = new Deployment('rabbitmq', {
            image: 'rabbitmq:3-management',
            port: 5672,
            replicas: 1,
            namespace: this.namespace,
            env: {
                'RABBITMQ_DEFAULT_USER': 'admin',
                'RABBITMQ_DEFAULT_PASS': 'rabbitmq_password'
            }
        });
        
        const redisService = serviceFor(redis);
        const rabbitmqService = serviceFor(rabbitmq);
        
        // Management interface for RabbitMQ
        const rabbitmqMgmt = new Service('rabbitmq-mgmt', rabbitmq, {
            port: 15672,
            namespace: this.namespace
        });
        
        this.services.push(redis, rabbitmq, redisService, rabbitmqService, rabbitmqMgmt);
        return this;
    }
    
    // Create configuration for all services
    createConfiguration() {
        const globalConfig = new ConfigMap('microservices-config', {
            'service.timeout': '30s',
            'log.level': 'info',
            'metrics.enabled': 'true',
            'tracing.enabled': 'true',
            'health.check.interval': '10s'
        });
        
        // Secrets for sensitive data
        const secrets = new Secret('microservices-secrets', {
            'jwt_secret': 'super-secret-jwt-key-for-auth',
            'stripe_secret': 'sk_test_your_stripe_secret_key',
            'encryption_key': 'advanced-encryption-key-256-bit',
            'database_master_password': 'ultra-secure-master-db-password'
        });
        
        this.configs.push(globalConfig);
        this.secrets.push(secrets);
        return this;
    }
    
    // Build the complete architecture
    build() {
        return this
            .createFrontend()
            .createApiGateway()
            .createUserService()
            .createOrderService()
            .createPaymentService()
            .createInventoryService()
            .createDatabases()
            .createSharedServices()
            .createConfiguration();
    }
    
    // Get all resources for deployment
    getAllResources() {
        return [...this.services, ...this.configs, ...this.secrets];
    }
    
    // Deploy everything with intelligent staging
    async deployWithStaging() {
        console.log('🏗️  Deploying microservices architecture...');
        
        // Stage 1: Infrastructure (databases, cache, queues)
        const infrastructure = this.services.filter(service => 
            ['user-db', 'order-db', 'payment-db', 'inventory-db', 'redis', 'rabbitmq'].includes(service.name) ||
            service.name.includes('-service') && !service.name.includes('user-service')
        );
        
        console.log('📦 Stage 1: Deploying infrastructure...');
        const infraSuccess = deploy(...infrastructure, ...this.configs, ...this.secrets);
        
        if (!infraSuccess) {
            console.log('❌ Infrastructure deployment failed');
            return false;
        }
        
        // Wait for databases to be ready
        console.log('⏳ Waiting for databases to be ready...');
        await this.waitForServices(['user-db-service', 'order-db-service', 'payment-db-service', 'inventory-db-service']);
        
        // Stage 2: Core services
        const coreServices = this.services.filter(service => 
            ['user-service', 'payment-service', 'inventory-service'].includes(service.name) ||
            service.name.includes('-service') && ['user', 'payment', 'inventory'].some(name => service.name.includes(name))
        );
        
        console.log('📦 Stage 2: Deploying core services...');
        const coreSuccess = deploy(...coreServices);
        
        if (!coreSuccess) {
            console.log('❌ Core services deployment failed');
            return false;
        }
        
        // Stage 3: Dependent services
        const dependentServices = this.services.filter(service => 
            ['order-service', 'api-gateway', 'frontend'].includes(service.name) ||
            service.name.includes('-service') && ['order', 'api-gateway', 'frontend'].some(name => service.name.includes(name))
        );
        
        console.log('📦 Stage 3: Deploying dependent services...');
        const dependentSuccess = deploy(...dependentServices);
        
        return dependentSuccess;
    }
    
    // Utility method to wait for services to be ready
    async waitForServices(serviceNames, timeoutMs = 60000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeoutMs) {
            try {
                // In a real implementation, this would check service health
                console.log(`⏳ Checking readiness of ${serviceNames.join(', ')}...`);
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                // Simplified: assume services are ready after 5 seconds
                console.log('✅ Services ready');
                return true;
                
            } catch (error) {
                console.log('⏳ Services not ready yet, waiting...');
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        throw new Error('Timeout waiting for services to be ready');
    }
}

// Smart deployment patterns
function createEcommerceStack() {
    return new MicroserviceArchitecture('ecommerce').build();
}

function createSocialMediaStack() {
    return new MicroserviceArchitecture('social')
        .createFrontend()
        .createApiGateway()
        .createUserService()
        // Add social-specific services
        .createConfiguration();
}

// Example usage
if (require.main === module) {
    console.log('🏪 Creating E-commerce Microservices Architecture');
    
    // Create complete microservices architecture
    const architecture = createEcommerceStack();
    const allResources = architecture.getAllResources();
    
    console.log(`📊 Architecture Summary:`);
    console.log(`   Total resources: ${allResources.length}`);
    console.log(`   Services: ${allResources.filter(r => r.kind === 'Deployment').length}`);
    console.log(`   Databases: ${allResources.filter(r => r.kind === 'StatefulSet').length}`);
    console.log(`   Network: ${allResources.filter(r => r.kind === 'Service').length}`);
    console.log(`   Config: ${allResources.filter(r => r.kind === 'ConfigMap').length}`);
    
    // Show what would be deployed
    deploy(...allResources, { dryRun: true });
    
    console.log(`\n💡 To deploy this architecture:`);
    console.log(`   1. Uncomment the deployment code below`);
    console.log(`   2. Make sure kubectl is configured`);
    console.log(`   3. Run: node microservices.js`);
    
    // Uncomment to deploy (requires kubectl and cluster access)
    // architecture.deployWithStaging();
}