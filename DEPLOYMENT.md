# 🌐 Deploy EconGame to the Internet - Complete Guide

## Table of Contents
1. [Get a Domain Name](#1-get-a-domain-name)
2. [Choose a Hosting Platform](#2-choose-hosting-platforms)
3. [Deploy Step-by-Step](#3-deployment-guides)
4. [Connect Your Domain](#4-connect-your-domain)
5. [Add User Authentication](#5-user-authentication-setup)
6. [Production Security](#6-production-security)
7. [Email Setup (Password Reset)](#7-email-setup-for-password-reset)

---

## 1. Get a Domain Name

### Cheap Domain Providers

**Best Budget Options:**

| Provider | Price | Notes |
|----------|-------|-------|
| **Namecheap** | $8-15/year | Recommended, easy to use |
| **Porkbun** | $7-12/year | Very cheap, good service |
| **Google Domains** | $12/year | Clean interface |
| **GoDaddy** | $12-20/year | Famous but more expensive |
| **Cloudflare Registrar** | $8-10/year | At-cost pricing |

### How to Buy:
1. Go to **Namecheap.com** (or any provider above)
2. Search for your desired name: `econgame.com`, `play-econ.com`, etc.
3. Add to cart and checkout
4. You now own the domain! 🎉

**Tip:** `.com` domains are most trusted, but `.net`, `.io`, `.gg` are also good for games.

---

## 2. Choose Hosting Platforms

### Option A: **PythonAnywhere** (Easiest, Free Tier!)

**Pros:**
- ✅ **Free tier available**
- ✅ Python-specific, easy setup
- ✅ Built-in MySQL database
- ✅ HTTPS included
- ✅ No credit card needed for free

**Cons:**
- ❌ Limited on free tier (1 app, slow)
- ❌ Free tier needs renewal every 3 months

**Price:** 
- Free (limited)
- $5/month (Hacker plan - good for small games)

**Best for:** Beginners, testing, small groups

---

### Option B: **Heroku** (Popular, Free Tier Ending)

**Pros:**
- ✅ Very popular
- ✅ Git-based deployment
- ✅ Auto-scaling
- ✅ HTTPS included

**Cons:**
- ❌ Free tier discontinued (Nov 2022)
- ❌ $7/month minimum now

**Price:** $7+/month

**Best for:** Startups, scaling apps

---

### Option C: **Railway.app** (Modern, Easy)

**Pros:**
- ✅ $5 free credit/month
- ✅ Very modern interface
- ✅ Git deployment
- ✅ Automatic HTTPS
- ✅ PostgreSQL database included

**Cons:**
- ❌ Limited free credit

**Price:** $5 free/month, then $0.000463/GB-hour

**Best for:** Modern developers, small-medium apps

---

### Option D: **DigitalOcean** (Full Control)

**Pros:**
- ✅ Full server control
- ✅ Cheap ($6/month droplet)
- ✅ Powerful
- ✅ Can host multiple apps

**Cons:**
- ❌ Requires Linux knowledge
- ❌ Manual setup

**Price:** $6/month for smallest server

**Best for:** Advanced users, full control

---

### Option E: **Render.com** (Modern, Free Tier)

**Pros:**
- ✅ Free tier available
- ✅ Easy deployment
- ✅ Auto HTTPS
- ✅ PostgreSQL included

**Cons:**
- ❌ Free tier spins down after inactivity (slow start)

**Price:** Free tier, $7/month for persistent

**Best for:** Side projects, portfolio

---

## 3. Deployment Guides

### 🎯 RECOMMENDED: Deploy to PythonAnywhere (Easiest)

#### Step 1: Sign Up
1. Go to **pythonanywhere.com**
2. Click "Start running Python online in less than a minute"
3. Create free account

#### Step 2: Upload Your Code
1. Go to "Files" tab
2. Create folder: `/home/yourusername/econgame`
3. Upload all your files:
   - `app_auth.py`
   - `templates/` folder
   - `static/` folder
   - `requirements.txt`

#### Step 3: Install Dependencies
1. Go to "Consoles" tab
2. Start a "Bash" console
3. Run:
```bash
cd econgame
pip3 install --user flask
```

#### Step 4: Configure Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Choose "Python 3.10"
5. Set these:
   - **Source code:** `/home/yourusername/econgame`
   - **Working directory:** `/home/yourusername/econgame`
   - **WSGI file:** Click to edit, replace with:

```python
import sys
path = '/home/yourusername/econgame'
if path not in sys.path:
    sys.path.append(path)

from app_auth import app as application
```

6. Click "Reload" at top
7. Visit: `yourusername.pythonanywhere.com`

#### Step 5: Connect Custom Domain
1. Upgrade to paid plan ($5/month)
2. In "Web" tab, add your domain: `econgame.com`
3. Go to your domain registrar (Namecheap)
4. Add these DNS records:

```
Type: CNAME
Host: www
Value: yourusername.pythonanywhere.com

Type: A
Host: @
Value: (IP provided by PythonAnywhere)
```

5. Wait 10-60 minutes for DNS to propagate
6. Visit `econgame.com` - it works! 🎉

---

### 🚀 Deploy to Railway.app (Modern)

#### Step 1: Prepare Your Code
1. Create `.gitignore`:
```
__pycache__/
*.pyc
game_data/
.env
```

2. Create `Procfile`:
```
web: gunicorn app_auth:app
```

3. Add to `requirements.txt`:
```
Flask>=3.0.0
gunicorn>=21.0.0
```

#### Step 2: Deploy
1. Go to **railway.app**
2. Sign in with GitHub
3. Click "New Project"
4. Choose "Deploy from GitHub repo"
5. Select your repo
6. Railway auto-detects Python and deploys!

#### Step 3: Add Domain
1. In Railway project, go to "Settings"
2. Click "Generate Domain" (free subdomain)
3. OR click "Custom Domain" and add your purchased domain
4. Update DNS at your registrar:
```
Type: CNAME
Host: @
Value: (provided by Railway)
```

---

### 💻 Deploy to DigitalOcean (Advanced)

#### Step 1: Create Droplet
1. Go to **digitalocean.com**
2. Create account, add payment
3. Create Droplet:
   - **Image:** Ubuntu 22.04
   - **Plan:** Basic $6/month
   - **Datacenter:** Nearest to you
4. Create and note the IP address

#### Step 2: Connect & Setup
```bash
# SSH into your server
ssh root@YOUR_IP

# Update system
apt update && apt upgrade -y

# Install Python
apt install python3 python3-pip python3-venv nginx -y

# Create app directory
mkdir /var/www/econgame
cd /var/www/econgame

# Upload your files (use FileZilla or scp)
# Then:
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
```

#### Step 3: Configure Gunicorn
Create `/etc/systemd/system/econgame.service`:
```ini
[Unit]
Description=EconGame
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/econgame
Environment="PATH=/var/www/econgame/venv/bin"
ExecStart=/var/www/econgame/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 app_auth:app

[Install]
WantedBy=multi-user.target
```

```bash
systemctl start econgame
systemctl enable econgame
```

#### Step 4: Configure Nginx
Create `/etc/nginx/sites-available/econgame`:
```nginx
server {
    listen 80;
    server_name econgame.com www.econgame.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/econgame /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 5: Add SSL (HTTPS)
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d econgame.com -d www.econgame.com
```

#### Step 6: Point Domain
In your domain registrar:
```
Type: A
Host: @
Value: YOUR_DROPLET_IP

Type: A
Host: www
Value: YOUR_DROPLET_IP
```

---

## 4. Connect Your Domain

### At Your Domain Registrar (Namecheap Example)

1. Log into Namecheap
2. Go to "Domain List"
3. Click "Manage" next to your domain
4. Go to "Advanced DNS"

**For PythonAnywhere:**
```
Type: CNAME
Host: www
Value: yourusername.pythonanywhere.com
TTL: Automatic

Type: A Record
Host: @
Value: (IP from PythonAnywhere)
TTL: Automatic
```

**For Railway/Render:**
```
Type: CNAME
Host: @
Value: (provided by platform)
TTL: Automatic

Type: CNAME
Host: www  
Value: (provided by platform)
TTL: Automatic
```

**For DigitalOcean/Own Server:**
```
Type: A Record
Host: @
Value: YOUR_SERVER_IP
TTL: Automatic

Type: A Record
Host: www
Value: YOUR_SERVER_IP
TTL: Automatic
```

### Wait for DNS Propagation
- Usually takes 10-60 minutes
- Can take up to 48 hours
- Check status at: **whatsmydns.net**

---

## 5. User Authentication Setup

### Using the Auth Version

Your `app_auth.py` is ready to go! It includes:

✅ **Registration** - New users create accounts  
✅ **Login/Logout** - Session management  
✅ **Password Hashing** - Secure (PBKDF2 + SHA-256)  
✅ **Password Reset** - With reset codes  
✅ **Email Support** - Ready for SMTP integration  

### Current Status (Development)
- ✅ Username/password login works
- ✅ Passwords are hashed securely
- ⚠️ Password reset codes shown on screen (not emailed)
- ⚠️ Need to configure SMTP for email

---

## 6. Production Security

### Essential Security Steps

#### 1. Use Environment Variables
Create `.env` file:
```env
SECRET_KEY=your-super-secret-random-key-here
FLASK_ENV=production
DATABASE_URL=your-database-url-if-using-postgres
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Update `app_auth.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
```

Install: `pip install python-dotenv`

#### 2. Disable Debug Mode
In `app_auth.py`, change:
```python
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

#### 3. Use HTTPS
- PythonAnywhere: Auto HTTPS
- Railway/Render: Auto HTTPS
- DigitalOcean: Use Certbot (shown above)

#### 4. Rate Limiting (Prevent Abuse)
```bash
pip install flask-limiter
```

Add to `app_auth.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ... existing code
```

#### 5. Database Migration (Optional but Recommended)
For production with many users, switch from JSON to PostgreSQL:

```bash
pip install psycopg2-binary flask-sqlalchemy
```

This prevents data loss and improves performance.

---

## 7. Email Setup for Password Reset

### Option A: Gmail SMTP (Free, Easy)

1. Enable 2-Factor Auth on Google Account
2. Generate App Password:
   - Google Account → Security → 2-Step Verification → App Passwords
   - Create app password, save it

3. Update `app_auth.py`:
```python
import smtplib
from email.mime.text import MIMEText
import os

def send_reset_email(to_email, reset_code, username):
    """Send password reset email"""
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USERNAME')
    smtp_pass = os.environ.get('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_pass:
        return False  # SMTP not configured
    
    subject = "EconGame - Password Reset"
    reset_link = f"https://yourdomain.com/reset-password?code={reset_code}"
    
    body = f"""
    Hi {username},
    
    You requested a password reset for your EconGame account.
    
    Click here to reset your password:
    {reset_link}
    
    Or use this code: {reset_code}
    
    This code expires in 1 hour.
    
    If you didn't request this, ignore this email.
    
    - EconGame Team
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# Update forgot_password route:
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    # ... existing code to find username...
    
    # Generate reset code
    reset_code = secrets.token_urlsafe(16)
    
    # Save to database
    resets = load_password_resets()
    resets[reset_code] = {
        'username': username,
        'email': email,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
    }
    save_password_resets(resets)
    
    # Send email
    if send_reset_email(email, reset_code, username):
        return jsonify({
            'success': True,
            'message': 'Password reset email sent! Check your inbox.'
        })
    else:
        # Fallback for development
        return jsonify({
            'success': True,
            'message': 'Email not configured. Reset code: ' + reset_code
        })
```

### Option B: SendGrid (Free 100 emails/day)

1. Sign up at **sendgrid.com**
2. Create API key
3. Install: `pip install sendgrid`
4. Use SendGrid's API instead of SMTP

---

## 8. Quick Deployment Comparison

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| **PythonAnywhere** | ⭐ Easy | Free - $5/mo | Beginners |
| **Railway.app** | ⭐⭐ Medium | $5 credit/mo | Modern apps |
| **Render.com** | ⭐⭐ Medium | Free - $7/mo | Side projects |
| **Heroku** | ⭐⭐ Medium | $7/mo | Established apps |
| **DigitalOcean** | ⭐⭐⭐⭐ Hard | $6/mo | Full control |

---

## 9. Post-Deployment Checklist

After deploying, test these:

- [ ] Can visit domain without errors
- [ ] HTTPS works (shows lock icon)
- [ ] Register new account
- [ ] Login with account
- [ ] Logout
- [ ] Forgot password flow
- [ ] Reset password
- [ ] Play the game (work, buy stocks, etc.)
- [ ] Multiple users can play simultaneously
- [ ] Data persists after server restart

---

## 10. Monitoring & Maintenance

### Monitor Your App
- **PythonAnywhere**: Has built-in error logs
- **Railway**: Logs tab shows all output
- **DigitalOcean**: Use `journalctl -u econgame -f`

### Backup Your Data
```bash
# Automate backups of game_data/ folder
# Run daily via cron:
0 2 * * * tar -czf /backups/econgame-$(date +\%Y\%m\%d).tar.gz /var/www/econgame/game_data/
```

### Update Your App
```bash
# Pull latest code
git pull

# Restart service
systemctl restart econgame  # DigitalOcean
# OR click "Reload" in PythonAnywhere
# OR git push triggers auto-deploy on Railway
```

---

## 🎉 You're Done!

Your game is now live on the internet with:
✅ Custom domain (econgame.com)  
✅ User registration & login  
✅ Secure passwords  
✅ Password reset  
✅ HTTPS encryption  
✅ Multiple players supported  

Share your domain with friends and start playing! 🚀💰
