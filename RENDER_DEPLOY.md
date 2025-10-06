# Deploy to Render.com (No Credit Card Required)

## Why Render?
- **TRUE free tier** (no credit card needed)
- 750 hours/month free compute
- Auto-deploy from GitHub
- Professional URLs: `your-app.onrender.com`

## 3-Step Deployment

### Step 1: Create GitHub Repo (if not already done)
```powershell
cd "C:\Users\archm\code\Counter-Counter-(CC)-Exposure\CascadeProjects\windsurf-project"
git init
git add .
git commit -m "Initial commit"
gh repo create counter-exposure-engine --private --source=. --push
```

### Step 2: Create Render Account
1. Go to: https://render.com/
2. Sign up with GitHub (instant OAuth)
3. Authorize Render to access your repos

### Step 3: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your `counter-exposure-engine` repo
3. Configure:
   - **Name:** `counter-exposure-engine`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python railway_server.py`
   - **Plan:** Free

4. Add Environment Variables:
   - `YOUTUBE_API_KEY` = (your key)
   - `TWITCH_CLIENT_ID` = (your ID)
   - `TWITCH_OAUTH_TOKEN` = (your token)

5. Click "Create Web Service"

## What Happens Next
- Render clones your repo
- Installs dependencies
- Starts `railway_server.py`
- Hourly auto-discovery begins
- Feed available at: `https://counter-exposure-engine.onrender.com/`

## Limitations (Free Tier)
- Service spins down after 15 min of inactivity
- Cold start = 30-60 seconds on first request
- 750 hours/month limit (automatically pauses at limit)

## Upgrade Later ($7/month)
- Always-on (no cold starts)
- Custom domain support
- Faster CPUs

---

**Pro tip:** Render's free tier is perfect for MVP testing. Add a custom domain later ($12/year) to look professional.
