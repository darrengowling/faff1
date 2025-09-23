# UCL Auction Deployment Guide

## 🚀 **Quick Start Deployment**

### One-Command Deploy
```bash
# 1. Clone repository
git clone <repository-url>
cd ucl-auction

# 2. Configure environment (see Environment Setup below)
cp .env.production.template .env.production
# Edit .env.production with your settings

# 3. Deploy everything
./deploy.sh production deploy
```

That's it! Your application will be running at `http://localhost:8000`

---

## 🔧 **Environment Setup**

### Required Configuration

#### 1. Database Configuration
```bash
# MongoDB connection string
MONGO_URL=mongodb://username:password@host:port/database
MONGO_DATABASE_NAME=ucl_auction_prod
```

**Setup Options:**
- **Local MongoDB**: `mongodb://localhost:27017/ucl_auction_prod`
- **MongoDB Atlas**: `mongodb+srv://username:password@cluster.mongodb.net/ucl_auction_prod`
- **Docker MongoDB**: Included in docker-compose.yml

#### 2. JWT Configuration
```bash
# Generate secure secret (minimum 32 characters)
JWT_SECRET=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7 days
```

#### 3. Email Provider Setup

**Gmail Setup (Recommended)**:
1. Enable 2FA on Gmail account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Configure environment:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com
SMTP_FROM_NAME="UCL Auction"
```

**Other Email Providers**:
- **SendGrid**: `smtp.sendgrid.net:587`
- **Mailgun**: `smtp.mailgun.org:587`  
- **AWS SES**: `email-smtp.region.amazonaws.com:587`

#### 4. WebSocket & CORS Configuration
```bash
# Frontend URLs that can connect
WEBSOCKET_CORS_ORIGINS=["https://your-domain.com","http://localhost:3000"]
CORS_ORIGINS=["https://your-domain.com"]
FRONTEND_BASE_URL=https://your-domain.com
```

#### 5. Security Configuration
```bash
# Environment type
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security settings
SECURE_COOKIES=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

---

## 🐳 **Docker Deployment Options**

### Option 1: Docker Compose (Recommended)
```bash
# Start everything with one command
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything  
docker-compose down
```

### Option 2: Individual Containers
```bash
# Build application image
docker build -t ucl-auction .

# Run MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7.0

# Run application
docker run -d --name ucl-auction \
  --link mongodb:mongodb \
  -p 8000:8000 \
  -e MONGO_URL=mongodb://mongodb:27017/ucl_auction \
  ucl-auction
```

### Option 3: Kubernetes Deployment
```yaml
# See kubernetes/ directory for full K8s manifests
kubectl apply -f kubernetes/
```

---

## 🌐 **Production Deployment Options**

### Cloud Platform Deployment

#### **AWS ECS**
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t ucl-auction .
docker tag ucl-auction:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ucl-auction:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ucl-auction:latest

# Deploy with ECS task definition
aws ecs update-service --cluster ucl-auction --service ucl-auction-service --force-new-deployment
```

#### **Google Cloud Run**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ucl-auction
gcloud run deploy --image gcr.io/PROJECT-ID/ucl-auction --platform managed
```

#### **Azure Container Instances**
```bash
# Deploy to Azure
az container create \
  --resource-group ucl-auction-rg \
  --name ucl-auction \
  --image ucl-auction:latest \
  --ports 8000 \
  --environment-variables MONGO_URL=$MONGO_URL JWT_SECRET=$JWT_SECRET
```

#### **DigitalOcean App Platform**
```yaml
# app.yaml
name: ucl-auction
services:
- name: web
  source_dir: /
  github:
    repo: your-username/ucl-auction
    branch: main
  run_command: python backend/server.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: MONGO_URL
    value: ${MONGO_URL}
  - key: JWT_SECRET
    value: ${JWT_SECRET}
```

---

## 🔒 **SSL/HTTPS Setup**

### Option 1: Let's Encrypt (Free)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Custom SSL Certificate
```bash
# Add certificate files to ./ssl/
cp your-cert.pem ./ssl/cert.pem
cp your-key.pem ./ssl/key.pem

# Update nginx.conf to use SSL
# Certificates automatically mounted in container
```

---

## 📊 **Monitoring & Logging**

### Application Monitoring
```bash
# View live logs
docker-compose logs -f app

# Application metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

### Database Monitoring
```bash
# MongoDB status
docker-compose exec mongodb mongosh --eval "db.adminCommand('serverStatus')"

# Database size
docker-compose exec mongodb mongosh --eval "db.stats()"
```

### Log Files
```bash
# Application logs
tail -f ./logs/application.log

# Auction activity
tail -f ./logs/auction.log

# Admin actions
tail -f ./logs/admin.log

# Error logs
tail -f ./logs/error.log
```

---

## 🔄 **Backup & Recovery**

### Automated Backups
```bash
# Configure backup schedule in environment
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30

# Manual backup
./deploy.sh production backup
```

### Manual Database Backup
```bash
# Create backup
docker-compose exec mongodb mongodump --out /tmp/backup
docker cp ucl-auction-mongodb:/tmp/backup ./backups/$(date +%Y%m%d_%H%M%S)

# Restore backup
docker cp ./backups/20250101_020000/backup ucl-auction-mongodb:/tmp/
docker-compose exec mongodb mongorestore /tmp/backup
```

### Application Backup
```bash
# Backup application state
tar -czf ucl-auction-backup-$(date +%Y%m%d).tar.gz \
  .env.production \
  ./logs \
  ./backups \
  docker-compose.yml
```

---

## 🚨 **Troubleshooting**

### Common Issues

#### **Application Won't Start**
```bash
# Check logs
docker-compose logs app

# Common causes:
# 1. MongoDB not accessible
# 2. Environment variables missing
# 3. Port already in use

# Solutions:
docker-compose down
docker-compose up -d mongodb  # Start database first
sleep 10
docker-compose up -d app      # Then application
```

#### **Email Not Sending**
```bash
# Test SMTP connection
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('SMTP connection successful')
server.quit()
"

# Check application logs for email errors
docker-compose logs app | grep -i "email\|smtp"
```

#### **Database Connection Issues**
```bash
# Test MongoDB connection
docker-compose exec mongodb mongosh --eval "db.adminCommand('ismaster')"

# Check if MongoDB is running
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb
```

#### **WebSocket Connection Failed**
```bash
# Check CORS settings
# Ensure WEBSOCKET_CORS_ORIGINS includes your frontend URL

# Test WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/socket.io/
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Database performance
docker-compose exec mongodb mongosh --eval "db.currentOp()"

# Application memory usage
docker-compose exec app ps aux

# Disk space
df -h
```

---

## 🔧 **Maintenance Commands**

### Regular Maintenance
```bash
# Update application
./deploy.sh production update

# Clean up old resources
./deploy.sh production cleanup

# View application status
./deploy.sh production status

# Restart services
./deploy.sh production restart
```

### Database Maintenance
```bash
# Compact database
docker-compose exec mongodb mongosh --eval "db.runCommand({compact: 'users'})"

# Rebuild indexes
docker-compose exec mongodb mongosh --eval "db.users.reIndex()"

# Database statistics
docker-compose exec mongodb mongosh --eval "db.stats()"
```

---

## 📞 **Support & Resources**

### Getting Help
- **Documentation**: See README.md for detailed setup
- **Logs**: Check `./logs/` directory for detailed error information
- **Health Check**: `curl http://localhost:8000/health`
- **Database**: Connect via `docker-compose exec mongodb mongosh`

### Useful Commands
```bash
# Quick status check
curl -s http://localhost:8000/health | jq

# Database connection test
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# View all environment variables
docker-compose exec app env | grep -E "MONGO|JWT|SMTP"

# Container resource usage
docker-compose exec app cat /proc/meminfo

# Application version
curl -s http://localhost:8000/version
```

### Emergency Procedures
```bash
# Emergency stop
docker-compose down

# Emergency rollback
./deploy.sh production rollback

# Emergency backup
docker-compose exec mongodb mongodump --gzip --archive > emergency-backup-$(date +%Y%m%d_%H%M%S).gz

# Reset to clean state
docker-compose down -v  # WARNING: Destroys all data
docker system prune -a
./deploy.sh production deploy
```

---

## ✅ **Deployment Checklist**

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Email provider tested
- [ ] SSL certificates ready (if using HTTPS)
- [ ] Domain DNS configured
- [ ] Backup strategy planned

### Post-Deployment
- [ ] Health check passes
- [ ] Email magic links working
- [ ] WebSocket connections working
- [ ] Database accessible
- [ ] Admin panel accessible
- [ ] Monitoring configured
- [ ] Backups scheduled

### Production Readiness
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Log rotation configured
- [ ] Monitoring alerts configured
- [ ] Backup restoration tested
- [ ] Load testing completed
- [ ] Security scan completed

**🎉 Your UCL Auction application is ready for production!**