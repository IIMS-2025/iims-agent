# Deployment Guide - Sales Analytics Assistant

This guide helps you deploy the ChatGPT-like Sales Analytics Assistant for production use.

## 🚀 Quick Start

### Prerequisites

- **Node.js** v18+ and npm v8+
- **Python** 3.10+
- **OpenAI API Key** (required)
- **Backend Inventory API** running (default: http://localhost:8000)

### 1. Environment Setup

```bash
# Clone/download the project
cd iims-agent

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Environment Variables:**

```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
BASE_URL=http://localhost:8000
X_TENANT_ID=11111111-1111-1111-1111-111111111111
```

### 2. One-Command Setup

```bash
# Start everything (Python venv + Node.js server)
./start.sh
```

This script will:

- ✅ Create Python virtual environment
- ✅ Install all dependencies (Python + Node.js)
- ✅ Test the tools
- ✅ Build TypeScript
- ✅ Start the ChatGPT-like server

### 3. Verify Installation

```bash
# Test health endpoint
curl http://localhost:3000/health

# Test chat functionality
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales trends",
    "session_id": "test_123"
  }'
```

## 🧪 Testing

### Test Individual Python Tools

```bash
source venv/bin/activate
python test_runner.py
```

### Test Complete Chat Flow

```bash
source venv/bin/activate
python test_chat.py
```

### Test Server with Demo Script

```bash
# Start server first: ./start.sh
# Then in another terminal:
./demo.sh
```

### Run Integration Tests

```bash
npm test
```

## 🔧 Manual Setup (if start.sh fails)

### Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Test tools
python test_runner.py
```

### Node.js Server

```bash
# Install Node dependencies
npm install

# Build TypeScript
npm run build

# Start server
npm start

# Or development mode
npm run dev
```

## 📊 Usage Examples

### Basic Chat Examples

```bash
# Sales trends
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales trends for last month",
    "session_id": "user_123"
  }'

# Product performance
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which menu items sell the most?",
    "session_id": "user_123"
  }'

# Sales forecasting
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Predict Kerala Burger sales for next 30 days",
    "session_id": "user_123"
  }'

# Period comparison
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare this month vs last month revenue",
    "session_id": "user_123"
  }'
```

### Streaming Response

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze all sales data and give insights",
    "session_id": "user_123",
    "stream": true
  }'
```

### Session Management

```bash
# Get conversation history
curl http://localhost:3000/chat/user_123/history

# Clear session
curl -X DELETE http://localhost:3000/chat/user_123
```

## 🏗️ Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile (create this for production)
FROM node:18-slim

WORKDIR /app

# Install Python for LangGraph
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Copy package files
COPY package*.json ./
COPY requirements.txt ./

# Install Node dependencies
RUN npm ci --production

# Create Python virtual environment
RUN python3 -m venv venv
RUN ./venv/bin/pip install -r requirements.txt

# Copy application code
COPY . .

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "start"]
```

### Environment Variables for Production

```env
NODE_ENV=production
PORT=3000
OPENAI_API_KEY=sk-prod-key-here
BASE_URL=https://api.your-inventory-system.com
X_TENANT_ID=your-production-tenant-id
ENABLE_STREAMING=true
SESSION_TTL_SECONDS=3600
REDIS_URL=redis://prod-redis:6379
CORS_ORIGIN=https://your-frontend.com
```

### Redis Session Storage (Optional)

```bash
# Install Redis for production session storage
docker run -d --name redis -p 6379:6379 redis:alpine

# Update .env
REDIS_URL=redis://localhost:6379
```

## 🔒 Security Checklist

### Production Security Settings

- ✅ Set strong CORS origins (not `*`)
- ✅ Use HTTPS in production
- ✅ Rate limit API endpoints
- ✅ Validate all file uploads
- ✅ Never log API keys
- ✅ Use helmet for security headers
- ✅ Set proper session TTL

### Monitoring & Logging

```javascript
// Add to production
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});
```

## 🚨 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**

```bash
# Check environment
echo $OPENAI_API_KEY

# Set in .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

**"Unable to connect to inventory system"**

```bash
# Check if backend API is running
curl http://localhost:8000/api/v1/inventory

# Update BASE_URL in .env if needed
BASE_URL=http://your-backend-host:8000
```

**Python import errors**

```bash
# Reinstall in virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**TypeScript compilation errors**

```bash
# Clean and rebuild
npm run clean
npm run build
```

### Debug Mode

```bash
# Start with debug logging
NODE_ENV=development npm run dev

# Check session analytics (dev only)
curl http://localhost:3000/analytics/sessions
```

## 📈 Performance Optimization

### Production Optimizations

- Use Redis for session storage (not in-memory)
- Enable response compression
- Set up connection pooling for database calls
- Cache analytics results for 5-10 minutes
- Use cluster mode for multiple CPU cores

### Scaling Considerations

- Load balancer for multiple server instances
- Separate Redis cluster for sessions
- Database read replicas for analytics queries
- CDN for static assets

## 🔄 Updates & Maintenance

### Updating Dependencies

```bash
# Python dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Node.js dependencies
npm update
```

### Monitoring Health

```bash
# Check server health
curl http://localhost:3000/health

# Monitor session count
curl http://localhost:3000/analytics/sessions
```

## 🎯 Next Steps

After successful deployment:

1. **Frontend Integration**: Connect to your React/Vue frontend
2. **Analytics Dashboard**: Build charts using the chart data endpoints
3. **User Authentication**: Add user management and role-based access
4. **Advanced Analytics**: Implement custom forecasting models
5. **Mobile App**: Create mobile interface for the chat API

## 📞 Support

### Logs Location

- **Server logs**: Console output (use PM2/Docker logs in production)
- **Session data**: In-memory (or Redis in production)
- **Error logs**: Console + optional file logging

### Health Monitoring

- **Server**: `GET /health`
- **Sessions**: `GET /analytics/sessions` (dev only)
- **API connectivity**: Monitor backend API calls in logs

### Performance Metrics

- Response time per chat message
- Tool execution time
- Session memory usage
- API call frequency and success rates
