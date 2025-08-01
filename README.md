# Pinterest Agent Platform

# See Backend and Frontend READMEs for architecture notes

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key
- Pinterest Account Credentials
- Proxy Server (optional)

### Local Deployment

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pinterest-agent-platform
   ```

2. **Configure environment variables**
   ```bash
   cd deployment
   cp env.backend.sample .env.backend
   cp env.frontend.sample .env.frontend
   ```

3. **Edit the environment files**
   ```bash
   # Edit backend environment
   nano .env.backend
   ```
   
   **Required variables:**
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   PIN_PASSWORD=your-pinterest-password-here
   PROXY_PASSWORD=your-proxy-password-here
   ```

4. **Start the application**
   ```bash
   cd ..
   docker compose up -d
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### EC2 Deployment

#### Option 1: Manual Deployment

1. **Launch EC2 Instance**
   - **AMI**: Ubuntu 22.04 LTS
   - **Instance Type**: t3a.medium (playwright is resource intensive)
   - **Storage**: 20GB gp3
   - **Security Group**: Open ports 22 (SSH), 80 (HTTP), 8000 (API)

2. **Security Group Configuration**
   ```
   Type        Protocol    Port    Source
   SSH         TCP         22      0.0.0.0/0 (or your IP)
   HTTP        TCP         80      0.0.0.0/0
   Custom TCP  TCP         8000    0.0.0.0/0
   ```

3. **SSH into your instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

4. **Install Docker and Docker Compose**
   ```bash
   # Update system
   sudo apt-get update && sudo apt-get upgrade -y
   
   # Install Docker
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
   
   # Add user to docker group
   sudo usermod -aG docker ubuntu
   ```

5. **Clone and setup the application**
   ```bash
   git clone <your-repo-url>
   cd pinterest-agent-platform
   ```

6. **Configure environment variables**
   ```bash
   cd deployment
   cp env.backend.sample .env.backend
   cp env.frontend.sample .env.frontend
   
   # Edit with your credentials
   sudo nano .env.backend
   sudo nano .env.frontend
   ```

7. **Update frontend environment**
   ```bash
   # In .env.frontend, set:
   NEXT_PUBLIC_API_URL=http://your-ec2-ip:8000
   ```

8. **Start the application**
   ```bash
   cd ..
   docker compose up -d
   ```

9. **Access your application**
   - Frontend: http://your-ec2-ip
   - Backend API: http://your-ec2-ip:8000
   - API Docs: http://your-ec2-ip:8000/docs

#### Option 2: Automated Deployment with User Data Script

1. **Prepare the User Data Script**
   ```bash
   # Update the repository URL in the user data script
   nano deployment/ec2_user_data.sh
   ```
   
   Change this line:
   ```bash
   git clone https://github.com/yourusername/pinterest-agent-platform.git .
   ```
   
   To your actual repository URL.

2. **Launch EC2 Instance with User Data**
   ```bash
   aws ec2 run-instances \
     --image-id ami-09ac0b140f63d3458 \
     --count 1 \
     --instance-type t3a.medium \
     --key-name your-key-name \
     --security-group-ids sg-your-security-group \
     --user-data file://deployment/ec2_user_data.sh \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PinterestAgentPlatform}]' \
     --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20,VolumeType=gp3}'
   ```

3. **Wait for Initial Setup**
   The user data script will automatically:
   - Install Docker and Docker Compose
   - Clone your repository
   - Create environment files
   - Build and start the application

4. **SSH in and Configure**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   cd /opt/app/deployment
   
   # Edit environment files with your credentials
   sudo nano .env.backend
   sudo nano .env.frontend
   ```
5. **Build and Start Docker Services**
   ```bash
   cd /opt/app
   # Build all services
   docker compose build
   # Start services in detached mode
   docker compose up -d
   ```

6. **Access your application**
   - Frontend: http://your-ec2-ip
   - Backend API: http://your-ec2-ip:8000
   - API Docs: http://your-ec2-ip:8000/docs

**Note**: The user data script provides a faster deployment but still requires manual configuration of API keys and credentials after the initial setup.

## 📁 Project Structure

```
pinterest-agent-platform/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── pyproject.toml      # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # Next.js frontend
│   ├── src/                # Source code
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Frontend container
├── deployment/             # Deployment files
│   ├── docker-compose.yml  # Service orchestration
│   ├── backend.Dockerfile  # Production backend build
│   ├── frontend.Dockerfile # Production frontend build
│   └── .env.*             # Environment files
└── docker-compose.yml      # Main compose file
```

## 🔧 Services

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 80 | Next.js web application |
| **Backend** | 8000 | FastAPI REST API |
| **Worker** | - | Celery background tasks |
| **Redis** | 6379 | Message broker |
| **MongoDB** | 27017 | Database |


### Common Issues

**1. Frontend can't connect to backend (CORS error)**
- Ensure `NEXT_PUBLIC_API_URL` in `.env.frontend` points to the correct backend URL
- Check that CORS_ORIGINS in `.env.backend` includes your frontend URL

**2. WebSocket connection issues**
- Verify the WebSocket URL in frontend code points to the correct backend
- Check that the backend is running and accessible

**3. High CPU usage**
- Consider upgrading to a larger instance type (t3a.medium or higher)
- Monitor resource usage with `docker stats`

**4. Services not starting**
- Check logs: `docker compose logs`
- Verify environment variables are set correctly
- Ensure all required API keys are configured



