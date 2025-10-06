# 🎮 PLAY NOW - 30 Second Setup

## Fastest Way to See It Work

### Step 1: Generate Your Feed (10 seconds)
```powershell
cd "c:\Users\archm\code\Counter-Counter-(CC)-Exposure\CascadeProjects\windsurf-project"
python simple_web_ui.py
```

**Result**: Creates `counter_exposure_feed.html` - a beautiful webpage showing discovered content!

### Step 2: Open & Enjoy (5 seconds)
```powershell
# Open in browser
start counter_exposure_feed.html
```

### Step 3: Share with Friend (15 seconds)
```powershell
# Upload to web instantly
python share.py
```

**Copy the URL it gives you → Send to friend → They see your discoveries!** 🎉

---

## Alternative: Run Web Server Locally

```powershell
# Install web dependencies
pip install fastapi uvicorn

# Start server
python web_server.py
```

Then go to: **http://localhost:8000**

Give your friend: **http://YOUR_IP:8000** (if on same network)

---

## Free Cloud Options (5-10 minutes)

### Option A: Railway.app (Easiest)
1. Go to https://railway.app
2. Sign in with GitHub
3. New Project → Deploy from GitHub → Select your repo
4. Add environment variables (YouTube API key, etc.)
5. Get public URL like: `counter-exposure.up.railway.app`

### Option B: GitHub Pages (Free Forever)
1. Push code to GitHub
2. Go to Settings → Pages → Source: gh-pages branch
3. Add secrets: YOUTUBE_API_KEY, TWITCH_CLIENT_ID, TWITCH_OAUTH_TOKEN
4. Go to Actions → Run "Discover & Publish" workflow
5. Visit: `https://yourusername.github.io/repo-name/counter_exposure_feed.html`

### Option C: Render.com
1. Go to https://render.com
2. New Web Service → Connect GitHub
3. Build: `pip install -r requirements-web.txt`
4. Start: `python web_server.py`
5. Add environment variables
6. Get URL like: `counter-exposure.onrender.com`

---

## 🎯 My Recommendation for "Play Now"

**For immediate gratification:**
```powershell
# 1. Generate feed
python simple_web_ui.py

# 2. Upload and share
python share.py
```

**Copy the Gist URL → Send to friend → Done!** ✨

---

## What You Get

Your feed shows:
- 📺 Underexposed YouTube videos (≤500 views)
- 🔴 Live streams with 0-5 viewers
- 🔍 Reverse-discovered hidden content
- 📊 Underexposure scores
- 🎨 Beautiful dark theme
- ⚡ Auto-refresh every 10 minutes

---

## 💡 Tips

**Generate fresh discoveries:**
```powershell
python simple_web_ui.py
```

**Share updated feed:**
```powershell
python share.py
```

**Check database:**
```powershell
sqlite3 exposure_tracker.db "SELECT COUNT(*) FROM exposures;"
```

**View logs:**
```powershell
Get-Content counter_exposure_engine.log -Tail 20
```

---

## 🚨 If Something Breaks

**No discoveries found?**
- Check API keys in `.env`
- Try: `python run_engine.py --mode streams --count 5`

**Import errors?**
- Run: `pip install -r requirements.txt`

**Share script fails?**
- GitHub Gist might be rate-limited
- Try again in 5 minutes
- Or just upload `counter_exposure_feed.html` to https://gist.github.com manually

---

## 🎉 That's It!

You now have a working content discovery engine that finds underexposed creators!

**While you play with it, I'll be working on the production deployment in the background.** 😄
