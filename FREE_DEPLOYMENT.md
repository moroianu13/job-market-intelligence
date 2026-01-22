# 🆓 FREE Deployment Guide - Zero Cost, Zero Surprises

**100% Free deployment options with no credit card required!**

---

## ⭐ Recommended: Streamlit Cloud (EASIEST & FREE FOREVER)

**Best for**: Interactive dashboard hosting
**Cost**: **$0 forever** for public repos
**Requirements**: GitHub account only (no credit card!)
**Limitations**: Public repos only, 1GB RAM, 1 CPU

### Quick Deploy to Streamlit Cloud

1. **Push your code to GitHub** (already done ✅)

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"**

4. **Select your repository**: `moroianu13/job-market-intelligence`

5. **Configure**:
   - Main file: `app/streamlit_app.py`
   - Python version: `3.10`

6. **Add secrets** (Settings → Secrets):
   ```toml
   ADZUNA_APP_ID = "your_app_id_here"
   ADZUNA_APP_KEY = "your_app_key_here"
   ```

7. **Deploy!** 🚀

Your app will be live at: `https://your-app-name.streamlit.app`

**✅ Advantages**:
- Completely free forever
- No credit card needed
- Auto-deploys on git push
- Built-in HTTPS
- Easy to use

**⚠️ Limitations**:
- Repository must be public
- App sleeps after inactivity (wakes in seconds)
- 1GB RAM limit
- Can't run scheduled pipelines (only UI)

---

## 🚂 Option 2: Railway.app (FREE $5/month credit)

**Best for**: Full stack with database
**Cost**: **$0** with free tier ($5 credit/month, no CC required for hobby plan)
**Limitations**: Up to 500 hours/month, sleeps after 30min inactivity

### Deploy to Railway

Railway gives you $5 free credits every month - perfect for this project!

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Deploy**:
   ```bash
   cd ~/job-market-intelligence
   railway init
   railway up
   ```

4. **Add environment variables**:
   ```bash
   railway variables set ADZUNA_APP_ID=your_id
   railway variables set ADZUNA_APP_KEY=your_key
   ```

5. **Access your app**:
   ```bash
   railway open
   ```

**Railway configuration** (already created in `railway.toml`):
- Streamlit UI on port 8501
- Auto-deploys from main branch
- PostgreSQL database (free 1GB)
- Redis cache included

**Free tier includes**:
- ✅ $5 credit/month (plenty for this project)
- ✅ PostgreSQL + Redis free
- ✅ Custom domain
- ✅ No credit card for hobby tier
- ⚠️ App sleeps after 30min inactivity

---

## 🎨 Option 3: Render.com (FREE with limitations)

**Best for**: Multiple services (web + database)
**Cost**: **$0** for free tier (no credit card required)
**Limitations**: Apps sleep after 15min, slow cold starts

### Deploy to Render

1. **Create account** at [render.com](https://render.com) (no CC required)

2. **Connect GitHub** repository

3. **Create Web Service**:
   - Repository: `moroianu13/job-market-intelligence`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`

4. **Add Environment Variables**:
   - `ADZUNA_APP_ID`
   - `ADZUNA_APP_KEY`

5. **Deploy!**

**Free tier includes**:
- ✅ 750 hours/month (enough for 24/7)
- ✅ PostgreSQL database (90 days, then deleted)
- ✅ Custom domain
- ✅ HTTPS included
- ⚠️ Apps sleep after 15min inactivity
- ⚠️ Slow cold start (up to 30 seconds)

---

## 🐙 Option 4: GitHub Pages (Static Dashboard)

**Best for**: Documentation and static reports
**Cost**: **$0** forever
**Limitations**: Static content only (no Streamlit)

Already configured! Your documentation is available at:
- https://moroianu13.github.io/job-market-intelligence

To enable:
1. Go to GitHub repo → Settings → Pages
2. Source: Deploy from branch `main`
3. Folder: `/ (root)` or `/docs`
4. Save

---

## 📊 Cost Comparison Table

| Platform | Cost | Database | Scheduled Jobs | Auto-deploy | Sleeps? | CC Required? |
|----------|------|----------|----------------|-------------|---------|--------------|
| **Streamlit Cloud** | $0 | No | No | Yes | Yes | ❌ No |
| **Railway** | $0 ($5 credit) | Yes (1GB) | Limited | Yes | Yes | ❌ No (hobby) |
| **Render** | $0 | Yes (90d) | No | Yes | Yes | ❌ No |
| **GitHub Pages** | $0 | No | No | Yes | No | ❌ No |
| **Heroku Free** | ❌ Discontinued | - | - | - | - | - |

---

## 🎯 Recommended Setup (100% Free)

### **For Interactive Dashboard**: Streamlit Cloud
- Deploy the Streamlit UI
- Public, always accessible
- No configuration needed

### **For Documentation**: GitHub Pages  
- Host README, reports, screenshots
- Fast and reliable

### **For Scheduled Data Collection**: GitHub Actions
- 2000 free minutes/month
- Run pipeline weekly
- Already configured!

---

## ⚙️ Free Scheduled Pipeline (GitHub Actions)

You already have this configured! It runs automatically every Monday.

**Free tier includes**:
- ✅ 2000 CI/CD minutes/month
- ✅ Unlimited public repo builds
- ✅ Artifact storage (500MB)
- ⚠️ No credit card required

To enable:
1. Add GitHub Secrets (Settings → Secrets → Actions):
   - `ADZUNA_APP_ID`
   - `ADZUNA_APP_KEY`
   - `DOCKER_USERNAME` (optional)
   - `DOCKER_TOKEN` (optional)

2. GitHub Actions will automatically:
   - Run tests on every push
   - Execute pipeline weekly
   - Generate reports
   - Upload artifacts

---

## 🚨 How to Avoid Charges (100% Safety)

### ✅ DO:
- Use Streamlit Cloud for UI (free forever)
- Use GitHub Actions for automation (2000 min/month free)
- Use Railway hobby tier ($5 credit, no CC)
- Use Render free tier
- Keep apps public
- Monitor usage dashboards

### ❌ DON'T:
- Add credit card unless absolutely necessary
- Enable auto-scaling (use fixed resources)
- Use paid tiers
- Deploy to AWS/GCP/Azure without free tier limits
- Leave expensive services running 24/7

### 🔒 Safety Measures:
1. **No credit card** - Don't add one if not required
2. **Set alerts** - Enable usage notifications
3. **Check dashboards** - Monitor monthly usage
4. **Use free tiers only** - Explicitly select free plans
5. **Keep backups** - Export data regularly

---

## 📝 Step-by-Step: Deploy in 5 Minutes

### **Option 1: Streamlit Cloud (Recommended)**

```bash
# 1. Already pushed to GitHub ✅

# 2. Go to https://share.streamlit.io

# 3. Click "New app"

# 4. Fill in:
#    - Repository: moroianu13/job-market-intelligence
#    - Branch: main
#    - Main file: app/streamlit_app.py

# 5. Add secrets in Settings:
#    ADZUNA_APP_ID = "your_id"
#    ADZUNA_APP_KEY = "your_key"

# 6. Click "Deploy"

# Done! 🎉
```

### **Option 2: Railway**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login (no credit card)
railway login

# 3. Initialize project
cd ~/job-market-intelligence
railway init

# 4. Add environment variables
railway variables set ADZUNA_APP_ID=your_id
railway variables set ADZUNA_APP_KEY=your_key

# 5. Deploy
railway up

# Done! 🎉
```

---

## 🆘 Troubleshooting

### "App won't start on Streamlit Cloud"

**Check**:
1. `requirements.txt` has all dependencies
2. Secrets are configured correctly
3. File path is `app/streamlit_app.py` (not just `streamlit_app.py`)

**Fix**: Add `packages.txt` if system dependencies needed:
```
# packages.txt
build-essential
```

### "Railway: Out of credit"

**Solution**:
- Free tier gives $5/month
- This project uses ~$2-3/month
- If exceeded, app sleeps until next month (no charges!)

### "Render: App is slow"

**Expected**: Free tier has cold starts (15-30 seconds)
**Solution**: Visit app once to wake it up

---

## 📊 Monitoring Free Tier Usage

### Streamlit Cloud
- Dashboard: https://share.streamlit.io/
- Shows: CPU, RAM, deployments
- No usage limits!

### Railway
- Dashboard: https://railway.app/dashboard
- Shows: Credit usage, hours, bandwidth
- Alert at 80% usage

### GitHub Actions
- Repository → Actions tab
- Shows: Workflow runs, minutes used
- 2000 minutes/month free

---

## 🎉 Summary

**Best free setup**:

1. **Streamlit Cloud** for UI (free forever)
2. **GitHub Actions** for weekly pipeline (free)
3. **GitHub** for code hosting (free)
4. **GitHub Pages** for docs (free)

**Total cost**: **$0.00/month** 🎊

**No credit card needed anywhere!**

---

## 📚 Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [GitHub Actions Free Tier](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)

---

## ✅ Next Steps

1. **Deploy to Streamlit Cloud** (5 minutes, no CC)
2. **Enable GitHub Actions** (add secrets)
3. **Share your dashboard URL** 🎊

**Zero cost. Zero surprises. Zero charges.** ✨
