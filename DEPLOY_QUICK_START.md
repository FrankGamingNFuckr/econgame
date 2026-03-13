# Quick Start: Deploy to Render.com

Your game is ready for FREE deployment to Render.com!

## Files Created for Deployment:

✅ **render.yaml** - Render configuration (auto-deploy)
✅ **Procfile** - Tells server how to start your app
✅ **requirements.txt** - Python dependencies
✅ **.env.example** - Example environment variables
✅ **RENDER_DEPLOYMENT.md** - Complete deployment guide

## Quick Deploy (5 Minutes):

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR-USERNAME/econgame.git
git push -u origin main
```

### 2. Deploy on Render
1. Go to https://render.com and sign up with GitHub
2. Click "New +" → "Web Service"
3. Select your `econgame` repository
4. Render auto-detects settings from `render.yaml`
5. Click "Create Web Service"
6. Wait 3-5 minutes ⏳

### 3. Your game is LIVE! 🎉
You'll get a URL like: `https://econgame-xxxx.onrender.com`

### 4. Connect IONOS Domain
1. In Render: Settings → Custom Domains → Add domain
2. In IONOS: DNS Settings → Add CNAME record
3. Point to Render URL
4. Wait 10-30 minutes for DNS

**Full details:** See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

---

## Important Before Deploying:

**Set SECRET_KEY environment variable:**
- Render will auto-generate this
- Or generate your own:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Optional Email Setup (for verification emails):**
- Add SMTP credentials to Render environment variables
- Or leave it - verification links will show in logs

---

## Free Tier Limitations:

✅ **Perfect for your game:**
- Free forever
- Unlimited bandwidth
- Custom domain (your IONOS domain)
- Free SSL certificate

⚠️ **Small limitations:**
- App sleeps after 15 mins (wakes in 30s)
- 750 hours/month
- JSON files reset on redeploy (upgrade to database later)

---

## After Deployment:

Your game will be live at your domain! Users can:
- Register accounts
- Play the economy game
- Earn money, buy stocks, create businesses
- Everything works!

**Ready to deploy? Follow [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)**
