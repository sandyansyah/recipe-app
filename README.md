# Recipe AI App - Complete Deployment Guide

Panduan lengkap deployment aplikasi Flask Recipe AI dari setup server hingga production.

## 📋 Table of Contents

- [Server Setup](#server-setup)
- [Install Dependencies](#install-dependencies)
- [Web Server Setup](#web-server-setup)
- [Flask Application Deploy](#flask-application-deploy)
- [Domain & SSL Setup](#domain--ssl-setup)
- [Troubleshooting](#troubleshooting)
- [GitHub Integration](#github-integration)
- [Development Workflow](#development-workflow)

---

## 🖥️ Server Setup

### 1. Initial Server Access
```bash
# SSH ke server
ssh root@ip public
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

### 1. Create Application Directory
```bash
# Create directory structure
sudo mkdir -p /var/www/recipe-app
sudo chown $USER:$USER /var/www/recipe-app
cd /var/www/recipe-app

# Create folder structure
mkdir -p templates static logic
```

### 2. Upload Application Files
```
/var/www/recipe-app/
├── app.py                 # Main Flask application
├── logic/
│   ├── __init__.py
│   ├── ai.py             # AI recommendation engine
│   ├── home.py           # Home page logic
│   ├── resep.py          # Recipe data handler
│   └── model.json        # Recipe database
├── templates/
│   ├── ai.html           # AI assistant page
│   ├── home.html         # Home page
│   └── resep.html        # Recipe listing page
└── static/
    └── style.css         # Application styles
```

### 3. Setup Python Virtual Environment
```bash
cd /var/www/recipe-app

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install flask pandas scikit-learn nltk numpy joblib
```

### 4. Setup NLTK Data
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

### 5. Train AI Model
```bash
# Fix path issues in ai.py and resep.py
# Change from: os.path.join('logic', 'model.json')
# To: os.path.join(os.path.dirname(__file__), 'model.json')

# Train the AI model
cd logic
python3 ai.py
# Should output: "NLM model trained and saved successfully."
```

### 6. Configure Nginx Reverse Proxy
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

### 7. Run Flask Application
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
2. Pilih domain `domain.com`
3. DNS Management
4. Tambah A record:
   - **Type:** A
   - **Name:** rpl
   - **Value:** ip public
   - **TTL:** 300

### 2. Test Domain (wait 5-15 minutes)
```bash
# Test domain resolution
ping rpl.domain.com

# Test website
curl -H "Host: rpl.domain.com" localhost
```

### 3. SSL Certificate (Optional)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Setup SSL
sudo certbot --nginx -d rpl.domain.com
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
# In ai.py and resep.py, change:
DATA_PATH = os.path.join('logic', 'model.json')
# To:
DATA_PATH = os.path.join(os.path.dirname(__file__), 'model.json')
```

#### 4. Missing Packages
```bash
# Install missing packages
pip install flask pandas scikit-learn nltk numpy joblib

# For zip utility
apt install zip unzip -y
```

---

## 📚 GitHub Integration

### 1. Create GitHub Repository
1. **GitHub.com** → Create new repository
2. **Name:** `recipe-app`
3. **Public** repository
4. **Don't** check "Add README file"

### 2. Setup Git Configuration
```bash
# Configure Git
git config --global user.name "sandyansyah"
git config --global user.email "sandyansyah356@gmail.com"
```

### 3. Initialize Git Repository
```bash
cd /var/www/recipe-app

# Initialize git
git init
git add .
git commit -m "Initial commit - Flask Recipe AI App"
git branch -M main

# Add remote repository
git remote add origin https://github.com/sandyansyah/recipe-app.git

# Push to GitHub
git push -u origin main
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

### 1. Update Code from Local to Server
```bash
# On local computer
git add .
git commit -m "Update description"
git push origin main

# On server
cd /var/www/recipe-app
git pull origin main

# Restart Flask
pkill -f "python3 app.py"
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
```

### 2. Update Code Directly on Server
```bash
# Edit files on server
nano app.py

# Commit and push
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

# Pull latest code
git pull origin main

# Restart Flask
pkill -f "python3 app.py"
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

### 1. Recipe AI Assistant
- **Natural Language Processing** untuk parsing ingredients
- **TF-IDF Vectorization** untuk recipe matching
- **Cosine Similarity** untuk recommendations
- **Interactive UI** dengan real-time suggestions

### 2. Recipe Database
- **JSON-based** recipe storage
- **Indonesian recipes** (Nasi Goreng, Mie Goreng, dll)
- **Ingredient matching** algorithm
- **Scalable architecture** untuk tambah recipes

### 3. Web Interface
- **Responsive design** dengan modern CSS
- **Multi-page structure** (Home, Recipes, AI)
- **Interactive ingredients selector**
- **Real-time recipe recommendations**

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

# Kill proses Flask yang sedang berjalan
pkill -f "python3 app.py"

# Masuk ke direktori aplikasi
cd /var/www/recipe-app

# Aktifkan virtual environment
source venv/bin/activate

# Jalankan ulang Flask
nohup python3 app.py > flask.log 2>&1 &


### Flask App Management
```bash
# Check Flask process
ps aux | grep python3

# View Flask logs
tail -f flask.log

# Restart Flask manually
pkill -f "python3 app.py"
cd /var/www/recipe-app
source venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
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
# GitHub to Server Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Server dengan akses SSH/root
- Git terinstall di server
- Python 3.x dan virtual environment
- Repository GitHub sudah di-clone ke server

## 📋 Standard Deployment Workflow

### 1. Persiapan Awal (Sekali Setup)
```bash
# Clone repository
git clone https://github.com/username/repository-name.git
cd repository-name

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Deployment Rutin

#### Method A: Safe Pull (Recommended)
```bash
# Masuk ke direktori project
cd /var/www/recipe-app

# Stop aplikasi yang berjalan
pkill -f "python3 app.py"

# Backup perubahan lokal (jika ada)
git stash push -m "backup before pull $(date)"

# Pull update terbaru
git pull origin main

# Aktifkan virtual environment
source venv/bin/activate

# Install/update dependencies jika ada perubahan
pip install -r requirements.txt

# Test aplikasi
python3 app.py

# Jika test OK, jalankan di background
nohup python3 app.py > flask.log 2>&1 &
```

#### Method B: Force Pull (Jika Ada Konflik)
```bash
# Stop aplikasi
pkill -f "python3 app.py"

# Force reset ke versi remote (HATI-HATI: hapus local changes)
git fetch origin
git reset --hard origin/main
git clean -fd

# Aktifkan venv dan install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart aplikasi
nohup python3 app.py > flask.log 2>&1 &
```

## 🔧 Troubleshooting Common Issues

### Issue 1: Merge Conflicts
**Error:** `<<<<<<< HEAD`, `=======`, `>>>>>>> commit_hash`

**Solution:**
```bash
# Method 1: Abort dan reset
git merge --abort
git reset --hard origin/main

# Method 2: Manual resolve (untuk advanced users)
nano [conflicted_file]  # Edit dan hapus conflict markers
git add .
git commit -m "Resolve merge conflicts"
```

### Issue 2: Module Not Found
**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Install missing module
pip install [module_name]

# Atau install semua dari requirements
pip install -r requirements.txt

# Update requirements.txt
pip freeze > requirements.txt
```

### Issue 3: Permission Denied
**Error:** `Permission denied`

**Solution:**
```bash
# Ganti ownership ke user yang benar
sudo chown -R $USER:$USER /var/www/recipe-app

# Atau jalankan dengan sudo (not recommended)
sudo git pull origin main
```

### Issue 4: Flask Not Starting
**Error:** `Exit 1` atau aplikasi crash

**Solution:**
```bash
# Check error log
cat flask.log

# Test manual untuk lihat error
python3 app.py

# Check syntax file utama
python3 -m py_compile app.py
```

## 📁 Project Structure Recommendations

```
/var/www/recipe-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── flask.log             # Application logs
├── README.md             # This documentation
├── .gitignore            # Git ignore rules
├── logic/                # Application logic
│   ├── __init__.py
│   ├── home.py
│   ├── ai.py
│   └── diskusi.py
├── templates/            # HTML templates
├── static/               # CSS, JS, images
└── venv/                # Virtual environment (di .gitignore)
```

## 🔄 Git Configuration untuk Smooth Deployment

### Setup Git Config (Sekali saja)
```bash
# Set merge strategy
git config pull.rebase false
git config merge.ours.driver true

# Set user info
git config user.name "Server Deployment"
git config user.email "deploy@server.com"

# Auto cleanup
git config fetch.prune true
```

### .gitignore Recommendations
```gitignore
# Virtual Environment
venv/
env/

# Python Cache
__pycache__/
*.pyc
*.pyo

# Logs
*.log
flask.log

# Environment Variables
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

## 🚦 Deployment Checklist

### Pre-Deployment
- [ ] Code sudah di-commit dan push ke GitHub
- [ ] Dependencies sudah di-update di requirements.txt
- [ ] Environment variables sudah di-set
- [ ] Database migration (jika ada) sudah dijalankan

### Deployment Process
- [ ] Stop aplikasi yang berjalan
- [ ] Backup perubahan lokal (jika ada)
- [ ] Pull code terbaru dari GitHub
- [ ] Install/update dependencies
- [ ] Test aplikasi secara manual
- [ ] Restart aplikasi di background
- [ ] Verify aplikasi berjalan dengan benar

### Post-Deployment
- [ ] Check logs untuk error
- [ ] Test endpoint utama
- [ ] Monitor performance
- [ ] Backup database (jika ada)

## 🔧 Useful Commands

### Monitoring
```bash
# Check running processes
ps aux | grep python3

# Check port usage
netstat -tlnp | grep :5000

# Monitor logs real-time
tail -f flask.log

# Check disk space
df -h
```

### Maintenance
```bash
# Clear logs
> flask.log

# Update system packages (Ubuntu)
sudo apt update && sudo apt upgrade

# Clean pip cache
pip cache purge

# Remove unused packages
pip autoremove
```

## 🚨 Emergency Recovery

### Jika Aplikasi Rusak Total
```bash
# 1. Backup current state
cp -r /var/www/recipe-app /var/www/recipe-app-backup-$(date +%Y%m%d)

# 2. Fresh clone
rm -rf /var/www/recipe-app
git clone https://github.com/username/repository-name.git /var/www/recipe-app
cd /var/www/recipe-app

# 3. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Restore data (jika ada)
cp /var/www/recipe-app-backup-*/user.json ./

# 5. Start application
nohup python3 app.py > flask.log 2>&1 &
```

## 📞 Support Information

- **Repository:** https://github.com/username/repository-name
- **Server Path:** `/var/www/recipe-app`
- **Log File:** `/var/www/recipe-app/flask.log`
- **Port:** 5000 (default Flask)

## 📝 Notes

- Selalu backup sebelum deployment ke production
- Test di environment staging dulu sebelum production
- Monitor logs setelah deployment
- Gunakan branching strategy untuk development
- Setup CI/CD untuk automation (GitHub Actions, etc.)

---

**Last Updated:** $(date)  
**Version:** 1.0  
**Maintainer:** Development Team
---

## 🌐 Access URLs

- **Website:** http://47.84.58.176
- **Subdomain:** http://aii.sandykaa.com (after DNS propagation)
- **GitHub Repository:** https://github.com/sandyansyah/recipe-app
- **Server SSH:** `ssh root@47.84.58.176`

---

## 📝 Notes

1. **Security:** Consider using environment variables for sensitive data
2. **Backup:** Regular GitHub commits serve as backup
3. **Monitoring:** Monitor server resources to prevent memory issues
4. **SSL:** Implement HTTPS for production use
5. **Domain:** DNS propagation takes 5-15 minutes

---

## 🎉 Deployment Complete!

Aplikasi Flask Recipe AI berhasil di-deploy dengan:
- ✅ Server Ubuntu 22.04 LTS di Alibaba Cloud ECS
- ✅ Nginx reverse proxy configuration
- ✅ Flask application dengan AI recommendations
- ✅ Custom subdomain setup
- ✅ GitHub integration untuk version control
- ✅ Automated deployment workflow

**Happy Coding!** 🚀
