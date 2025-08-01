# Pinterest AI Agent - Deployment Guide

This guide will help you deploy the Pinterest AI Agent stack on a single Ubuntu 22.04 EC2 instance.

## 🚀 Quick Start

### 1. Launch EC2 Instance

**Instance Configuration:**
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: t3.micro (1 vCPU, 1 GB RAM)
- **Storage**: 8 GB gp3 (minimum)
- **Security Group**: Open ports 22 (SSH), 80 (HTTP), 8000 (API)

**Security Group Rules:**
```
Type        Protocol    Port    Source
SSH         TCP         22      0.0.0.0/0 (or your IP)
HTTP        TCP         80      0.0.0.0/0
Custom TCP  TCP         8000    0.0.0.0/0
```

### 2. Configure Environment Variables

SSH into your instance and set up the environment:

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Navigate to deployment directory
cd /opt/app/deployment

# Copy and edit environment files
cp env.backend.sample .env.backend
cp env.frontend.sample .env.frontend

# Edit backend environment (REQUIRED)
nano .env.backend
```

**Required Environment Variables:**
```bash
# OpenAI API Key (Required)
OPENAI_API_KEY=sk-your-actual-openai-api-key

# Pinterest Account Password (Required)
PIN_PASSWORD=your-pinterest-password

# Proxy Password (Required)
PROXY_PASSWORD=your-proxy-password
```

### 3. Deploy the Stack

```bash
# Start the full application stack
docker compose up -d --build

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Access Your Application

- **Frontend**: `http://your-ec2-public-ip`
- **Backend API**: `http://your-ec2-public-ip:8000`
- **API Documentation**: `http://your-ec2-public-ip:8000/docs`

## 📁 Deployment Structure

```
deployment/
├── docker-compose.yml          # Main orchestration file
├── backend.Dockerfile          # Backend container build
├── frontend.Dockerfile         # Frontend container build
├── seed_pinterest_accounts.py  # Database seeding script
├── pinterest_accounts.sample.json  # Sample account data
├── env.backend.sample          # Backend environment template
├── env.frontend.sample         # Frontend environment template
├── ec2_user_data.sh           # EC2 bootstrap script
└── README.md                  # This file
```

## 🔧 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 80 | Next.js web application |
| **Backend** | 8000 | FastAPI REST API |
| **Worker** | - | Celery background tasks |
| **Redis** | 6379 | Message broker |
| **MongoDB** | 27017 | Database |

## 🛠️ Management Commands

### View Service Status
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
```

### Restart Services
```bash
# All services
docker compose restart

# Specific service
docker compose restart backend
```

### Stop Services
```bash
docker compose down
```

### Update and Redeploy
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
```

## 🔍 Troubleshooting

### Check Service Health
```bash
# Check if all services are running
docker compose ps

# Check service health
docker compose exec backend curl -f http://localhost:8000/health
docker compose exec frontend curl -f http://localhost:80
```

### View Resource Usage
```bash
# Check container resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

### Common Issues

**1. Services not starting:**
```bash
# Check logs for errors
docker compose logs

# Check if ports are available
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000
```

**2. Database connection issues:**
```bash
# Check MongoDB logs
docker compose logs mongodb

# Test MongoDB connection
docker compose exec backend python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://admin:password123@mongodb:27017/pinterest_agent?authSource=admin')
print(client.admin.command('ping'))
"
```

**3. Redis connection issues:**
```bash
# Check Redis logs
docker compose logs redis

# Test Redis connection
docker compose exec redis redis-cli ping
```

## 🔐 Security Considerations

### Environment Variables
- Never commit actual passwords to version control
- Use strong, unique passwords for Pinterest accounts
- Consider using AWS Secrets Manager for production

### Network Security
- Restrict security group access to your IP only
- Use HTTPS in production (add SSL certificate)
- Consider using AWS Application Load Balancer

### Data Persistence
- MongoDB and Redis data are stored in Docker volumes
- Consider backing up volumes regularly
- For production, use AWS RDS for MongoDB

## 📊 Monitoring

### Basic Monitoring
```bash
# Check service status
docker compose ps

# Monitor resource usage
docker stats

# Check application logs
docker compose logs -f
```

### Health Checks
- Backend: `http://your-ip:8000/health`
- Frontend: `http://your-ip/`
- API Docs: `http://your-ip:8000/docs`

## 🚀 Production Considerations

For production deployments, consider:

1. **Scaling**: Use larger instance types (t3.small or t3.medium)
2. **Load Balancing**: Add AWS Application Load Balancer
3. **SSL**: Configure HTTPS with Let's Encrypt or AWS Certificate Manager
4. **Monitoring**: Add CloudWatch monitoring and logging
5. **Backup**: Set up automated database backups
6. **Security**: Use AWS Secrets Manager for sensitive data

## 📞 Support

If you encounter issues:

1. Check the logs: `docker compose logs -f`
2. Verify environment variables are set correctly
3. Ensure all required ports are open in security group
4. Check instance has sufficient resources

## 🔄 Updates

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart services
docker compose down
docker compose up -d --build

# Verify services are healthy
docker compose ps
``` 