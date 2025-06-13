# Recipe AI App - Complete Deployment Guide

Panduan lengkap deployment aplikasi Flask Recipe AI dari setup server hingga production.

## 🌟 Repository Information

**GitHub Repository:** https://github.com/sandyansyah/recipe-app/

### 📥 Quick Clone & Setup

```bash
# Clone repository
git clone https://github.com/sandyansyah/recipe-app.git
cd recipe-app

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup NLTK data
python3 -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords') 
nltk.download('wordnet')
"

# Run application
python3 app.py
```

**Local Access:** http://localhost:5000

---

## 📋 Table of Contents

- [Repository Information](#-repository-information)
- [Server Setup](#-server-setup)
- [Install Dependencies](#-install-dependencies)
- [Web Server Setup](#-web-server-setup)
- [Flask Application Deploy](#-flask-application-deploy)
- [Domain & SSL Setup](#-domain--ssl-setup)
- [Troubleshooting](#-troubleshooting)
- [GitHub Integration](#-github-integration)
- [Development Workflow](#-development-workflow)

---

## 🖥️ Server Setup

### 1. Initial Server Access
```bash
# SSH ke server
ssh root@47.84.58.176
```

### 2. System Update
```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Handle configuration prompts:
# - SSH config: pilih "keep the local version currently installed"
# - Service restart: pilih "Ok" untuk restart semua services
```

---

## 📦 Install Dependencies

### 1. Install Basic Tools
```bash
# Install essential packages
sudo apt install python3 python3-pip python3-venv nginx git -y
```

### 2. Install Web Server
```bash
# Install dan start Nginx
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 3. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 22    # SSH
sudo ufw enable
```

---

## 🌐 Web Server Setup

### 1. Test Basic Nginx
```bash
# Test web server
curl localhost
# Should return "Welcome to nginx!" page
```

### 2. Check Public Access
- Browser: `http://47.84.58.176`
- Should display nginx welcome page

---

## 🚀 Flask Application Deploy

### 1. Clone Repository to Server
```bash
# Create directory and clone
sudo mkdir -p /var/www/
cd /var/www/

# Clone from GitHub
git clone https://github.com/sandyansyah/recipe-app.git
sudo mv recipe-app recipe-app
sudo chown -R $USER:$USER /var/www/recipe-app
cd /var/www/recipe-app
```

### 2. Setup Python Virtual Environment
```bash
cd /var/www/recipe-app

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies from requirements.txt
pip install -r requirements.txt
```

### 3. Setup NLTK Data
```bash
# Download required NLTK data
python3 -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords') 
nltk.download('wordnet')
nltk.download('punkt_tab')
"
```

### 4. Train AI Model
```bash
# Train the AI model
cd logic
python3 ai.py
# Should output: "NLM model trained and saved successfully."
cd ..
```

### 5. Configure Nginx Reverse Proxy
```bash
# Edit Nginx configuration
sudo nano /etc/nginx/sites-available/default
```

Replace content with:
```nginx
server {
    listen 80;
    server_name 47.84.58.176 aii.sandykaa.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/recipe-app/static;
        expires 30d;
    }
}
```

```bash
# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Run Flask Application
```bash
cd /var/www/recipe-app
source venv/bin/activate

# Run in background
nohup python3 app.py > flask.log 2>&1 &

# Check if running
ps aux | grep python3
```

---

## 🌍 Domain & SSL Setup

### 1. DNS Configuration (Domainesia)
1. Login ke panel Domainesia
2. Pilih domain `sandykaa.com`
3. DNS Management
4. Tambah A record:
   - **Type:** A
   - **Name:** aii
   - **Value:** 47.84.58.176
   - **TTL:** 300

### 2. Test Domain (wait 5-15 minutes)
```bash
# Test domain resolution
ping aii.sandykaa.com

# Test website
curl -H "Host: aii.sandykaa.com" localhost
```

### 3. SSL Certificate (Optional)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Setup SSL
sudo certbot --nginx -d aii.sandykaa.com
```

---

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 1. SSH Connection Lost
**Cause:** Server memory overload or firewall issues

**Solution:**
```bash
# Via VNC console (Alibaba Cloud)
# Check SSH service
systemctl status ssh
systemctl restart ssh

# Check firewall
ufw status
ufw allow 22
```

#### 2. Flask App Killed by System
**Cause:** Memory constraints

**Solution:**
```bash
# Create systemd service
sudo nano /etc/systemd/system/flask-app.service
```

```ini
[Unit]
Description=Flask Recipe App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/recipe-app
Environment=PATH=/var/www/recipe-app/venv/bin
ExecStart=/var/www/recipe-app/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable flask-app
sudo systemctl start flask-app
```

#### 3. Import Errors
**Cause:** Incorrect path handling

**Solution:**
```python
# In ai.py and other files, make sure paths are correct
# Check that all files are properly uploaded
```

#### 4. Missing Packages
```bash
# Install missing packages
pip install -r requirements.txt

# For zip utility
apt install zip unzip -y
```

---

## 📚 GitHub Integration

### 1. Repository Already Created
Repository sudah tersedia di: https://github.com/sandyansyah/recipe-app/

### 2. Setup Git Configuration (Jika diperlukan)
```bash
# Configure Git
git config --global user.name "sandyansyah"
git config --global user.email "sandyansyah356@gmail.com"
```

### 3. Update Repository (Jika ada perubahan)
```bash
cd /var/www/recipe-app

# Add changes
git add .
git commit -m "Update deployment configuration"

# Push to GitHub
git push origin main
```

### 4. Authentication Setup
1. **GitHub** → Settings → Developer settings
2. **Personal access tokens** → Tokens (classic)
3. **Generate new token (classic)**
4. **Scopes:** Select `repo`
5. **Copy token** for authentication

**When prompted:**
- **Username:** `sandyansyah`
- **Password:** [Personal Access Token]

---

## 🔄 Development Workflow

### 1. Update Code from GitHub to Server
```bash
# On server
cd /var/www/recipe-app

# Stop current Flask app
pkill -f "python3 app.py"

# Pull latest changes
git pull origin main

# Restart Flask
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
```

### 2. Update Code Directly on Server
```bash
# Edit files on server
nano app.py

# Commit and push changes
git add .
git commit -m "Fix bug description"
git push origin main

# Restart Flask
pkill -f "python3 app.py"
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
```

### 3. Automated Update Script
```bash
# Create update script
nano /var/www/update-app.sh
```

```bash
#!/bin/bash
cd /var/www/recipe-app

# Stop Flask
pkill -f "python3 app.py"

# Pull latest code
git pull origin main

# Restart Flask
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &

echo "App updated and restarted!"
```

```bash
# Make executable
chmod +x /var/www/update-app.sh

# Use script
/var/www/update-app.sh
```

---

## 📊 Application Features

### 1. Multi-Chain Web3 Authentication
- **Ethereum** support (MetaMask, OKX, Coinbase, WalletConnect)
- **Solana** support (Phantom, Solflare, Backpack)
- **Cross-chain** user management
- **Wallet statistics** and analytics

### 2. Recipe AI Assistant
- **Natural Language Processing** untuk parsing ingredients
- **TF-IDF Vectorization** untuk recipe matching
- **Cosine Similarity** untuk recommendations
- **Interactive UI** dengan real-time suggestions

### 3. Encrypted Chat System
- **CryptSan encryption** dengan AES-256-CBC
- **Shared group key** untuk diskusi komunitas
- **Hash verification** untuk message integrity
- **Multi-user** encrypted messaging

### 4. Recipe Database
- **JSON-based** recipe storage
- **Indonesian recipes** (Nasi Goreng, Mie Goreng, dll)
- **Ingredient matching** algorithm
- **Scalable architecture** untuk tambah recipes

---

## 🔧 Useful Commands

### Server Management
```bash
# Check server status
free -h                    # Memory usage
df -h                      # Disk usage
top                        # Process monitor
systemctl status nginx     # Nginx status
systemctl status flask-app # Flask service status
```

### Flask App Management
```bash
# Kill running Flask process
pkill -f "python3 app.py"

# Go to app directory
cd /var/www/recipe-app

# Activate virtual environment
source venv/bin/activate

# Restart Flask
nohup python3 app.py > flask.log 2>&1 &

# Check Flask process
ps aux | grep python3

# View Flask logs
tail -f flask.log
```

### Git Management
```bash
# Check git status
git status

# View commit history
git log --oneline

# Check remote repository
git remote -v

# Force pull (discard local changes)
git reset --hard origin/main
git pull origin main
```

---

## 🚦 Quick Deployment Checklist

### Pre-Deployment
- [ ] Repository sudah di-clone: `git clone https://github.com/sandyansyah/recipe-app.git`
- [ ] Dependencies sudah di-install: `pip install -r requirements.txt`
- [ ] NLTK data sudah di-download
- [ ] AI model sudah di-train

### Deployment Process
- [ ] Nginx sudah dikonfigurasi
- [ ] Flask app berjalan di port 5000
- [ ] Domain sudah di-setup (aii.sandykaa.com)
- [ ] SSL certificate (optional)

### Post-Deployment
- [ ] Test semua fitur (Home, AI, Diskusi)
- [ ] Test Web3 authentication
- [ ] Test encrypted chat
- [ ] Monitor logs untuk error

---

## 🚨 Emergency Commands

### Jika Aplikasi Tidak Jalan
```bash
# Stop semua proses Python
sudo pkill -f python3

# Masuk ke direktori aplikasi
cd /var/www/recipe-app

# Test manual untuk lihat error
python3 app.py

# Jika OK, jalankan di background
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
```

### Jika Repository Bermasalah
```bash
# Backup current state
cp -r /var/www/recipe-app /var/www/recipe-app-backup-$(date +%Y%m%d)

# Fresh clone
rm -rf /var/www/recipe-app
git clone https://github.com/sandyansyah/recipe-app.git /var/www/recipe-app
cd /var/www/recipe-app

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start application
nohup python3 app.py > flask.log 2>&1 &
```

---

## 🌐 Access URLs

- **Website:** http://47.84.58.176
- **Custom Domain:** http://aii.sandykaa.com (after DNS propagation)
- **GitHub Repository:** https://github.com/sandyansyah/recipe-app/
- **Server SSH:** `ssh root@47.84.58.176`

---

## 📋 Dependencies (requirements.txt)

```txt
# Web Framework
Flask==2.3.3
Werkzeug==2.3.7

# Data Science & Machine Learning
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
joblib==1.3.2

# Natural Language Processing
nltk==3.8.1

# Cryptography
cryptography==41.0.4

# Additional utilities
python-dotenv==1.0.0
```

---

## 📝 Notes

1. **Security:** Environment variables untuk sensitive data sudah diimplementasi
2. **Backup:** Regular GitHub commits serve as backup
3. **Monitoring:** Monitor server resources untuk mencegah memory issues
4. **SSL:** HTTPS sudah bisa diimplementasi dengan Let's Encrypt
5. **Domain:** DNS propagation membutuhkan 5-15 menit

---

## 🎉 Deployment Complete!

Aplikasi Flask Recipe AI berhasil di-deploy dengan:
- ✅ Server Ubuntu 22.04 LTS di Alibaba Cloud ECS
- ✅ Nginx reverse proxy configuration
- ✅ Flask application dengan AI recommendations
- ✅ Multi-chain Web3 authentication (Ethereum & Solana)
- ✅ Encrypted chat system dengan CryptSan
- ✅ Custom subdomain setup (aii.sandykaa.com)
- ✅ GitHub integration untuk version control
- ✅ Automated deployment workflow

**Repository:** https://github.com/sandyansyah/recipe-app/

**Happy Coding!** 🚀
