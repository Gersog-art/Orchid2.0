#!/bin/bash

# Integration script for OWASP Juice Shop
echo "Integrating Orchid Agent with Juice Shop..."

# Check if Juice Shop is installed
if [ ! -d "node_modules" ]; then
    echo "Error: Juice Shop not found. Run this script from Juice Shop directory."
    exit 1
fi

# Install Orchid agent dependencies
npm install amqplib prom-client uuid

# Backup original app.js
cp app.js app.js.backup

# Create agent directory
mkdir -p orchid-agent

# Create agent middleware
cat > orchid-agent/middleware.js << 'AGENTEOF'
const amqp = require('amqplib');
const { v4: uuidv4 } = require('uuid');
const { register, collectDefaultMetrics } = require('prom-client');

// Prometheus metrics
collectDefaultMetrics();

class OrchidAgent {
    constructor(config) {
        this.config = config;
        this.connection = null;
        this.channel = null;
        this.initialized = false;
    }
    
    async init() {
        try {
            // Connect to RabbitMQ
            this.connection = await amqp.connect({
                hostname: this.config.rabbitmqHost,
                port: this.config.rabbitmqPort,
                username: this.config.rabbitmqUser,
                password: this.config.rabbitmqPass
            });
            
            this.channel = await this.connection.createChannel();
            await this.channel.assertExchange('raw.traffic', 'direct', { durable: true });
            
            this.initialized = true;
            console.log('Orchid Agent connected to RabbitMQ');
        } catch (error) {
            console.error('Failed to initialize Orchid Agent:', error);
        }
    }
    
    async logRequest(req, res, next) {
        if (!this.initialized) {
            return next();
        }
        
        const startTime = Date.now();
        const requestId = uuidv4();
        
        // Capture request data
        const requestData = {
            request_id: requestId,
            timestamp: new Date().toISOString(),
            source: 'juice-shop',
            source_ip: req.ip || req.connection.remoteAddress,
            request: {
                method: req.method,
                url: req.originalUrl || req.url,
                headers: req.headers,
                params: req.params,
                query: req.query,
                body: req.body,
                cookies: req.cookies
            },
            metadata: {
                user_agent: req.get('User-Agent'),
                content_type: req.get('Content-Type'),
                content_length: req.get('Content-Length') || 0
            }
        };
        
        // Store original end function
        const originalEnd = res.end;
        
        res.end = async (chunk, encoding) => {
            // Restore original function
            res.end = originalEnd;
            
            // Call original function
            const result = originalEnd.call(res, chunk, encoding);
            
            // Add response data
            requestData.response = {
                status_code: res.statusCode,
                headers: res.getHeaders(),
                response_time: Date.now() - startTime
            };
            
            // Send to RabbitMQ
            try {
                await this.channel.publish(
                    'raw.traffic',
                    'juice-shop',
                    Buffer.from(JSON.stringify(requestData)),
                    { persistent: true }
                );
            } catch (error) {
                console.error('Failed to send request data:', error);
            }
            
            return result;
        };
        
        next();
    }
    
    async blockIP(ip) {
        // Implement IP blocking logic
        console.log(`Blocking IP: ${ip}`);
        // This could use iptables, nginx config, or in-memory blocking
    }
    
    async unblockIP(ip) {
        // Implement IP unblocking logic
        console.log(`Unblocking IP: ${ip}`);
    }
}

// Create and export agent instance
const agent = new OrchidAgent({
    rabbitmqHost: process.env.RABBITMQ_HOST || 'localhost',
    rabbitmqPort: process.env.RABBITMQ_PORT || 5672,
    rabbitmqUser: process.env.RABBITMQ_USER || 'guest',
    rabbitmqPass: process.env.RABBITMQ_PASS || 'guest'
});

module.exports = agent;
AGENTEOF

# Create integration patch for app.js
cat > orchid-agent/patch.js << 'PATCHEOF'
// Orchid Agent Integration
const orchidAgent = require('./middleware');

// Initialize agent (async)
orchidAgent.init().catch(console.error);

// Apply middleware to all routes
app.use((req, res, next) => {
    orchidAgent.logRequest(req, res, next);
});

// Add admin endpoint for Orchid actions
app.post('/api/orchid/action', (req, res) => {
    const { action, ip, incidentId } = req.body;
    
    switch (action) {
        case 'block':
            orchidAgent.blockIP(ip);
            res.json({ success: true, message: `IP ${ip} blocked` });
            break;
        case 'unblock':
            orchidAgent.unblockIP(ip);
            res.json({ success: true, message: `IP ${ip} unblocked` });
            break;
        default:
            res.status(400).json({ error: 'Invalid action' });
    }
});

// Add metrics endpoint
app.get('/orchid-metrics', async (req, res) => {
    res.set('Content-Type', 'text/plain');
    res.send(await require('prom-client').register.metrics());
});
PATCHEOF

echo "Integration files created. Please manually apply the patch to app.js."
echo "Add the following line to your app.js after express initialization:"
echo "require('./orchid-agent/patch');"
