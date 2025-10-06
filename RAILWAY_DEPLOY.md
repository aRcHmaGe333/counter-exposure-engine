# 🚂 Railway Deployment - Quick Guide

## What You Get

✅ **Auto-updates every hour** - Fresh discoveries continuously
✅ **Always online** - No sleeping (500 hours/month free = ~20 days)
✅ **Public URL** - Share with anyone
✅ **Zero code changes** - Your existing code untouched

---

## Step 1: Install Railway CLI

```powershell
npm install -g @railway/cli
```

---

## Step 2: Login & Deploy

```powershell
# Navigate to project
cd "C:\Users\archm\code\Counter-Counter-(CC)-Exposure\CascadeProjects\windsurf-project"

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

## Step 3: Add API Keys

In Railway dashboard (opens automatically):

1. Go to **Variables** tab
2. Add these secrets:
   ```
   YOUTUBE_API_KEY=your_youtube_key_here
   TWITCH_CLIENT_ID=your_twitch_client_id
   TWITCH_OAUTH_TOKEN=your_twitch_oauth_token
   ```
3. Click **Deploy** (redeploys with secrets)

---

## Step 4: Get Your URL

Railway gives you a URL like:
```
https://counter-exposure-production.up.railway.app
```

**That's it!** Your feed auto-updates every hour.

---

## What Happens

1. **On startup**: Runs discovery immediately
2. **Every hour**: Runs discovery again automatically
3. **Web server**: Always serves latest feed at `/`
4. **Health check**: Available at `/health` for monitoring

---

## Commands

```powershell
# View logs
railway logs

# Open dashboard
railway open

# Link to existing project
railway link

# Redeploy
railway up
```

---

## Troubleshooting

**"Service won't start"**
- Check logs: `railway logs`
- Verify API keys are set in dashboard
- Check PORT is auto-assigned (Railway does this)

**"Discovery fails"**
- Check API quota limits
- Verify API keys are correct
- Check logs for specific errors

**"Free tier limit"**
- 500 hours/month = ~20 days of 24/7 operation
- Upgrade to Hobby ($5/month) for unlimited

---

## Cost

**Free Tier**: 500 hours/month (enough for ~20 days continuous)
**Hobby Plan**: $5/month (unlimited, recommended)

---

## Alternative: GitHub Actions (Completely Free)

If you hit Railway limits, GitHub Actions runs for free:
- Updates every hour automatically
- Hosts on GitHub Pages
- Already configured (`.github/workflows/discover.yml`)
- Just push to GitHub and enable Pages

---

**You're 3 commands away from live auto-updating feed:**

```powershell
railway login
railway init
railway up
```

Go! 🚀
