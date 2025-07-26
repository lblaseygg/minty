# 🚀 AWS Deployment Guide for Minty

This guide will help you deploy the Minty trading platform to AWS for free using the AWS Free Tier.

## 📋 Prerequisites

- AWS Account (Free Tier eligible)
- Basic knowledge of AWS services
- Git installed locally
- SSH key pair (for EC2 access)

## 🆓 Free Tier Benefits

- **EC2**: 750 hours/month of t2.micro instances
- **RDS**: 750 hours/month of db.t3.micro (MySQL)
- **S3**: 5GB storage
- **Route 53**: 50 hosted zones
- **CloudFront**: 1TB data transfer

## 🏗️ Architecture Overview

```
Internet → Route 53 → CloudFront → S3 (Frontend)
                    ↓
                EC2 (Backend) → RDS (MySQL)
```

## 📦 Step 1: Prepare Your Application

### 1.1 Update Configuration
```bash
# Clone your repository
git clone https://github.com/yourusername/minty.git
cd minty

# Update environment variables for production
cp .env.example .env
```

Edit `.env` file:
```env
DATABASE_TYPE=mysql
MYSQL_USER=minty_user
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=your-rds-endpoint.region.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_DATABASE=minty_db
JWT_SECRET_KEY=your_very_secure_secret_key_here
FLASK_ENV=production
DEBUG=False
```

### 1.2 Create Production Requirements
```bash
# Create production requirements
cat > requirements-prod.txt << EOF
flask==3.0.2
sqlalchemy==2.0.28
pymysql==1.1.0
cryptography==42.0.5
werkzeug==3.0.1
python-dotenv==1.0.1
yfinance==0.2.36
pandas==2.2.1
numpy
scikit-learn
requests
ta
flask-jwt-extended==4.6.0
flask-cors==4.0.0
gunicorn==21.2.0
EOF
```

## 🗄️ Step 2: Set Up RDS Database

### 2.1 Create RDS Instance
1. Go to AWS RDS Console
2. Click "Create database"
3. Choose "Standard create"
4. Select "MySQL"
5. Choose "Free tier" template
6. Configure:
   - **DB instance identifier**: `minty-db`
   - **Master username**: `minty_admin`
   - **Master password**: `your_secure_password`
   - **DB instance class**: `db.t3.micro`
   - **Storage**: 20 GB (free tier)
   - **Multi-AZ deployment**: No (free tier)
7. Click "Create database"

### 2.2 Configure Security Group
1. Go to EC2 → Security Groups
2. Find the RDS security group
3. Edit inbound rules:
   - Type: MySQL/Aurora
   - Port: 3306
   - Source: Custom (your EC2 security group)

## 🖥️ Step 3: Launch EC2 Instance

### 3.1 Create EC2 Instance
1. Go to EC2 Console
2. Click "Launch instances"
3. Configure:
   - **Name**: `minty-server`
   - **AMI**: Ubuntu 22.04 LTS
   - **Instance type**: t2.micro
   - **Key pair**: Create or select existing
   - **Security group**: Create new
     - SSH (22): Your IP
     - HTTP (80): Anywhere
     - HTTPS (443): Anywhere
4. Launch instance

### 3.2 Configure Security Group
```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx git mysql-client -y
```

## 🔧 Step 4: Deploy Application

### 4.1 Set Up Application
```bash
# Clone repository
git clone https://github.com/yourusername/minty.git
cd minty

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements-prod.txt

# Set up environment
cp .env.example .env
nano .env  # Edit with production settings
```

### 4.2 Configure Database
```bash
# Connect to RDS and create database
mysql -h your-rds-endpoint -u minty_admin -p

# In MySQL:
CREATE DATABASE minty_db;
CREATE USER 'minty_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON minty_db.* TO 'minty_user'@'%';
FLUSH PRIVILEGES;
EXIT;

# Set up tables
python3 setup_xampp_database.py
```

### 4.3 Configure Nginx
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/minty

# Add this configuration:
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend static files
    location / {
        root /home/ubuntu/minty/frontend;
        try_files $uri $uri/ /landing.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}

# Enable site
sudo ln -s /etc/nginx/sites-available/minty /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4.4 Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/minty.service

# Add this content:
[Unit]
Description=Minty Trading App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/minty
Environment="PATH=/home/ubuntu/minty/venv/bin"
ExecStart=/home/ubuntu/minty/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 backend.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Start service
sudo systemctl daemon-reload
sudo systemctl enable minty
sudo systemctl start minty
```

## 🌐 Step 5: Set Up Domain & SSL

### 5.1 Configure Route 53
1. Go to Route 53 Console
2. Create hosted zone for your domain
3. Update nameservers with your domain registrar
4. Create A record pointing to your EC2 instance

### 5.2 Set Up SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Step 6: Monitoring & Logs

### 6.1 Set Up CloudWatch
```bash
# Install CloudWatch agent
sudo apt install amazon-cloudwatch-agent -y

# Configure monitoring
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### 6.2 Log Management
```bash
# Create log rotation
sudo nano /etc/logrotate.d/minty

# Add this content:
/home/ubuntu/minty/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload minty
    endscript
}
```

## 🔒 Step 7: Security Hardening

### 7.1 Configure Firewall
```bash
# Set up UFW
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 7.2 Regular Updates
```bash
# Create update script
nano ~/update.sh

# Add this content:
#!/bin/bash
sudo apt update && sudo apt upgrade -y
cd /home/ubuntu/minty
git pull
source venv/bin/activate
pip install -r requirements-prod.txt
sudo systemctl restart minty
sudo systemctl restart nginx

# Make executable
chmod +x ~/update.sh

# Add to crontab for weekly updates
crontab -e
# Add this line:
0 2 * * 0 /home/ubuntu/update.sh
```

## 📈 Step 8: Performance Optimization

### 8.1 Frontend Optimization
```bash
# Enable Nginx caching
sudo nano /etc/nginx/sites-available/minty

# Add to server block:
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 8.2 Backend Optimization
```bash
# Optimize Gunicorn settings
sudo nano /etc/systemd/system/minty.service

# Update ExecStart:
ExecStart=/home/ubuntu/minty/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 --max-requests 1000 --max-requests-jitter 100 backend.app:app
```

## 💰 Cost Breakdown (Free Tier)

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| EC2 t2.micro | 750 hours | $0 |
| RDS db.t3.micro | 750 hours | $0 |
| S3 | 5GB | $0 |
| Route 53 | 1 hosted zone | $0 |
| CloudFront | 1TB transfer | $0 |
| **Total** | | **$0** |

## 🚨 Important Notes

1. **Free Tier Limits**: Monitor usage to avoid charges
2. **Backup Strategy**: Set up automated backups
3. **Monitoring**: Use CloudWatch for performance monitoring
4. **Security**: Regularly update and patch systems
5. **Scaling**: Plan for growth beyond free tier

## 🔧 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   ```bash
   # Check RDS security group
   # Verify connection string
   mysql -h your-rds-endpoint -u minty_user -p
   ```

2. **Application Not Starting**
   ```bash
   # Check logs
   sudo journalctl -u minty -f
   
   # Check service status
   sudo systemctl status minty
   ```

3. **Nginx Issues**
   ```bash
   # Test configuration
   sudo nginx -t
   
   # Check error logs
   sudo tail -f /var/log/nginx/error.log
   ```

## 📞 Support

For issues with this deployment guide:
- Check AWS documentation
- Review application logs
- Monitor CloudWatch metrics
- Consider AWS support plans for production use

---

**Happy Deploying! 🚀**

Your Minty trading platform should now be live at `https://your-domain.com` 