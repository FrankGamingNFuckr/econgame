# 🚀 Production Quickstart Guide

## What You Need

1. ✅ Your game code (already done!)
2. ✅ A domain name ($8-15/year from Namecheap, Porkbun, etc.)
3. ✅ A hosting platform (see recommendations below)
4. ✅ Optional: Email account for password resets

---

## Which Hosting Should I Choose?

### 🎯 **Best for Beginners: PythonAnywhere**
- **Cost:** $5/month
- **Difficulty:** ⭐ Easy
- **Setup Time:** 15 minutes
- **Why:** Built for Python, easiest to understand
- **Link:** pythonanywhere.com

### 🚀 **Best for Modern Apps: Railway.app**
- **Cost:** $5 free credit/month, then pay-as-you-go
- **Difficulty:** ⭐⭐ Medium
- **Setup Time:** 10 minutes
- **Why:** Modern, Git-based deployment, auto-HTTPS
- **Link:** railway.app

### 💪 **Best for Control: DigitalOcean**
- **Cost:** $6/month
- **Difficulty:** ⭐⭐⭐⭐ Hard (requires Linux knowledge)
- **Setup Time:** 30-60 minutes
- **Why:** Full server control, can host multiple apps
- **Link:** digitalocean.com

---

## Quick Deploy to PythonAnywhere (Recommended)

### Step 1: Sign Up (2 minutes)
1. Go to **https://www.pythonanywhere.com**
2. Create account
3. Choose "Hacker" plan ($5/month)

### Step 2: Upload Code (5 minutes)
1. Go to "Files" tab
2. Upload your files:
   - `app_auth.py`
   - `templates/` folder
   - `static/` folder
   - `requirements.txt`

### Step 3: Install Dependencies (2 minutes)
1. Open "Bash" console
2. Run:
```bash
pip3 install --user flask gunicorn python-dotenv flask-limiter
```

### Step 4: Configure Web App (3 minutes)
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Flask" → "Python 3.10"
4. Set source code directory to where you uploaded files
5. Edit WSGI file to import `app_auth` instead of `flask_app`

### Step 5: Set Environment Variables (2 minutes)
1. In "Web" tab, scroll to "Environment variables"
2. Add:
```
SECRET_KEY = (generate with: python -c "import secrets; print(secrets.token_hex(32))")
```

### Step 6: Connect Domain (5 minutes)
1. In "Web" tab, add your custom domain
2. Go to Namecheap (or your domain registrar)
3. Add DNS records (PythonAnywhere will show you what to add)
4. Wait 10-60 minutes for DNS to propagate

### Step 7: Test! (2 minutes)
1. Visit your domain
2. Register a new account
3. Login and play!

✅ **Total Time: ~20 minutes**

---

## Quick Deploy to Railway.app (Git-Based)

### Prerequisites
- Install Git: https://git-scm.com/
- Create GitHub account: https://github.com/

### Step 1: Push Code to GitHub (5 minutes)
```bash
cd P:\EconGame
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/econgame.git
git push -u origin main
```

### Step 2: Deploy to Railway (3 minutes)
1. Go to **https://railway.app**
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `econgame` repository
6. Railway auto-deploys! 🎉

### Step 3: Add Environment Variables (2 minutes)
1. In Railway project, go to "Variables"
2. Add:
```
SECRET_KEY = (random 64-character string)
FLASK_ENV = production
```

### Step 4: Connect Domain (3 minutes)
1. In Railway, go to "Settings" → "Domains"
2. Click "Custom Domain" and add your domain
3. Copy the CNAME record Railway provides
4. Go to Namecheap and add the CNAME record
5. Wait for DNS propagation (10-60 minutes)

✅ **Total Time: ~15 minutes**

---

## Add Email Support (Optional)

### Using Gmail (Free)

1. **Enable 2-Factor Authentication** on your Google Account
2. **Generate App Password:**
   - Google Account → Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
3. **Add Environment Variables:**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-from-step-2
APP_URL=https://yourdomain.com
```
4. **Restart your app**
5. Test password reset - you should receive an email!

---

## Security Checklist

Before going live, make sure:

- [ ] `SECRET_KEY` environment variable is set (never use default!)
- [ ] `FLASK_ENV=production` is set
- [ ] Debug mode is OFF (check `app_auth.py`)
- [ ] HTTPS is enabled (check for lock icon in browser)
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] Game data folder (`game_data/`) is backed up
- [ ] Password reset email is working (or disabled if not needed)

---

## Common Issues

### "Internal Server Error"
- Check application logs
- Make sure all dependencies are installed
- Verify environment variables are set

### "Can't access from domain"
- Wait longer for DNS propagation (up to 48 hours)
- Check DNS records are correct
- Try clearing browser cache

### "Password reset not working"
- If email not configured, code will show on screen (development mode)
- Configure SMTP variables to send actual emails
- Check spam folder

---

## Need More Help?

📖 See full deployment guide: **DEPLOYMENT.md**

📝 General docs: **README.md**

🎮 Player guide: **QUICKSTART.md**

---

## Updating Your Live Site

After making changes to code:

**PythonAnywhere:**
1. Upload changed files
2. Click "Reload" button in Web tab

**Railway:**
1. Commit and push to GitHub:
```bash
git add .
git commit -m "Update game"
git push
```
2. Railway auto-deploys! (takes 1-2 minutes)

---

🎉 **Congratulations! Your game is now live on the internet!**
