# Deployment Guide: Deploy EconGame to Render.com (FREE)

## Overview
This guide walks you through deploying your EconGame to Render.com for FREE and connecting your IONOS domain.

**Total Time:** 15-20 minutes  
**Cost:** $0 (100% FREE)

---

## Prerequisites
- [x] GitHub account
- [x] Your IONOS domain
- [x] Render.com account (create one at https://render.com)

---

## Step 1: Push Your Code to GitHub

### 1.1 Create a GitHub Repository
1. Go to https://github.com/new
2. Name it `econgame` (or any name you like)
3. Keep it **Public** (required for Render free tier)
4. Don't initialize with README (you already have code)
5. Click "Create repository"

### 1.2 Push Your Code
Open terminal in your project folder and run:

```bash
git init
git add .
git commit -m "Initial commit - EconGame ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/econgame.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

**Important:** Before pushing, create a `.gitignore` file:
```
__pycache__/
*.pyc
.env
game_data/*.json
.venv/
venv/
*.log
```

This prevents uploading sensitive data and local files.

---

## Step 2: Deploy to Render

### 2.1 Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (easiest option)
3. Authorize Render to access your repositories

### 2.2 Create New Web Service
1. Click "New +" button → "Web Service"
2. Connect your GitHub repository (`econgame`)
3. Render will detect it's a Python app

### 2.3 Configure Deployment Settings

**Name:** `econgame` (or your preferred name)

**Region:** Choose closest to your users (e.g., Oregon, Frankfurt, Singapore)

**Branch:** `main`

**Runtime:** Python 3

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:** 
```
gunicorn app_auth:app
```

**Instance Type:** **Free** (select this!)

### 2.4 Add Environment Variables
Click "Advanced" → "Add Environment Variable"

Add this variable:
- **Key:** `SECRET_KEY`
- **Value:** Click "Generate" or paste a random string

Optional (for email verification):
- **Key:** `SMTP_SERVER`
- **Value:** `smtp.gmail.com` (or your email provider)
- Add SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD if using email

### 2.5 Deploy!
1. Click "Create Web Service"
2. Render will start building and deploying
3. Wait 3-5 minutes for first deployment
4. You'll see logs showing the build progress

Once done, you'll get a URL like: `https://econgame-xxxx.onrender.com`

**Test it!** Open that URL and see your game live!

---

## Step 3: Connect Your IONOS Domain

### 3.1 Get Your Render CNAME
1. In Render dashboard, go to your web service
2. Click "Settings" tab
3. Scroll to "Custom Domains"
4. Click "Add Custom Domain"
5. Enter your domain or subdomain:
   - Full domain: `yourdomain.com`
   - Subdomain: `game.yourdomain.com` (recommended)
6. Click "Verify"

Render will show you a CNAME record, like:
```
CNAME: econgame-xxxx.onrender.com
```

### 3.2 Configure IONOS DNS

1. Log into your IONOS account
2. Go to **Domains & SSL** → Click your domain
3. Click **DNS Settings** or **Manage DNS**
4. Add a new record:

**For subdomain (e.g., game.yourdomain.com):**
- **Type:** CNAME
- **Name:** `game` (or your preferred subdomain)
- **Value:** `econgame-xxxx.onrender.com` (from Render)
- **TTL:** 3600 (or default)

**For root domain (yourdomain.com) - if CNAME not allowed:**
- **Type:** A Record
- **Name:** `@`
- **Value:** Get IP from Render support or use subdomain instead

5. Click "Save"

### 3.3 Wait for DNS Propagation
- **Time:** 10 minutes to 48 hours (usually 10-30 mins)
- Check status: https://dnschecker.org

### 3.4 Enable SSL in Render
1. Back in Render dashboard
2. Go to custom domain settings
3. Render automatically provisions FREE SSL certificate
4. Wait a few minutes
5. Your site will be HTTPS! 🔒

---

## Step 4: Post-Deployment Setup

### 4.1 Create Your First Admin Account
1. Visit your live site
2. Register a new account
3. Check Render logs for the verification link
4. Or configure email to receive verification emails

### 4.2 Set Up Email (Optional but Recommended)

**Option A: Gmail (Free)**
1. Create a Gmail account or use existing
2. Enable "2-Step Verification"
3. Generate an "App Password"
4. Add to Render environment variables:
   - `SMTP_SERVER=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USERNAME=your-email@gmail.com`
   - `SMTP_PASSWORD=your-app-password`
   - `SENDER_EMAIL=your-email@gmail.com`

**Option B: SendGrid (Free tier: 100 emails/day)**
1. Sign up at https://sendgrid.com
2. Verify your sender email
3. Create API key
4. Add to Render:
   - `SENDGRID_API_KEY=your-key`
   - `SENDER_EMAIL=verified-email@yourdomain.com`

### 4.3 Monitor Your App
- **Render Dashboard:** View logs, metrics, deployments
- **Free tier limitation:** App sleeps after 15 mins inactivity
- **Wake-up time:** 30-50 seconds on first visit

---

## Step 5: Update & Redeploy

Every time you update your code:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Render will **automatically redeploy** within 1-2 minutes!

---

## Important Notes for Production

### Database Limitation
Your game uses JSON files which don't work well with multiple users on Render because:
- Files reset on each deploy
- Multiple instances can't share files
- No data persistence between restarts

**Solution (when you get users):**
Upgrade to PostgreSQL (Render offers free 90-day databases):
1. In Render, create a PostgreSQL database
2. Update your code to use SQLAlchemy
3. Migrate JSON data to database

For now, JSON files work fine for testing!

### File Persistence Workaround
Render has persistent disks (paid) or you can:
- Store data in external database
- Use Redis for caching
- Use cloud storage (AWS S3, Cloudflare R2)

### Expected Free Tier Performance
- ✅ Perfect for 0-100 concurrent users
- ✅ Unlimited bandwidth
- ⚠️ App sleeps after 15 mins (30s wake time)
- ⚠️ 750 hours/month limit (usually enough)

---

## Troubleshooting

### Issue: Build Failed
**Check:** 
- `requirements.txt` has all dependencies
- Python version compatible (Render uses 3.7-3.11)
- No syntax errors in code

### Issue: App crashes on startup
**Check Render logs:**
- Missing environment variables
- Port binding (Render sets $PORT automatically)
- Import errors

### Issue: Domain not working
**Check:**
- DNS propagation complete (use dnschecker.org)
- CNAME record points to correct Render URL
- SSL certificate issued (check Render settings)

### Issue: Data keeps resetting
**This is expected!** 
- Render restarts containers regularly
- JSON files don't persist
- Solution: Upgrade to database (see above)

---

## Cost Breakdown

| Item | Cost |
|------|------|
| Render Web Service | **FREE** |
| Custom Domain (IONOS) | Already own |
| SSL Certificate | **FREE** (auto) |
| Bandwidth | **FREE** (unlimited) |
| **Total** | **$0/month** |

---

## Next Steps

1. [ ] Push code to GitHub
2. [ ] Deploy to Render
3. [ ] Configure IONOS domain
4. [ ] Test your live game
5. [ ] Set up email (optional)
6. [ ] Share with friends!
7. [ ] Monitor usage and upgrade if needed

---

## Upgrade Path (When You Need It)

**Render Paid Tier ($7/month):**
- No sleep (always on)
- Better performance
- Persistent disk

**PostgreSQL Database (Free 90 days, then $7/month):**
- Proper data storage
- Multi-user support
- Data persistence

**Total for serious deployment:** ~$14/month
**But start FREE and upgrade when needed!**

---

## Support

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **IONOS Support:** https://www.ionos.com/help

**Your game is ready to go live! Good luck! 🚀🎮💰**
