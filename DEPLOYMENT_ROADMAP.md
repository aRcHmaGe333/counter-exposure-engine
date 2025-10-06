# Deployment Roadmap - Counter-Exposure Engine

## 📊 Project Status Assessment

### Development Timeline (Actual)
- **August 19, 2025**: Initial scaffold (~10 min of AI coding)
- **September 10, 2025**: Core implementation (~25-30 min of AI coding)
- **October 4-5, 2025**: Documentation phase (ongoing)

**Total AI coding time: ~35-40 minutes**

### Current State: ✅ **MVP Complete, Pre-Production**

**What Works:**
- ✅ Multi-platform discovery (YouTube, Twitch)
- ✅ Fairness scoring algorithm
- ✅ SQLite exposure tracking with 24hr cooldown
- ✅ Rate limiting and retry logic
- ✅ Comprehensive unit tests
- ✅ CLI interface with multiple modes
- ✅ Static HTML web viewer
- ✅ Database and logs confirmed working (Sept 10 runs)

**What Needs Work:**
- ⚠️ Reverse discovery uses fragile HTML parsing (regex)
- ⚠️ No production monitoring/health checks
- ⚠️ No deployment automation
- ⚠️ SQLite not ideal for concurrent access
- ⚠️ No API quota tracking

---

## 🎯 Path to Production

### Option A: Quick Deploy (Cron-Based)
**Goal**: Get it running on a VPS with scheduled discovery
**Time**: ~2 hours total (AI coding: ~15 min)
**Cost**: $5-6/month (VPS)

### Option B: Web Service (API + Dashboard)
**Goal**: Public-facing service with API endpoints
**Time**: ~4-6 hours total (AI coding: ~30 min)
**Cost**: $10-20/month (VPS + domain)

### Option C: Production-Grade SaaS
**Goal**: Scalable service with monitoring, multiple workers
**Time**: ~12-16 hours total (AI coding: ~60 min)
**Cost**: $50-200/month (cloud services)

---

## 🚀 Recommended Path: Option A First

Start simple, iterate based on actual usage.

---

## 📋 Session-by-Session Plan

### **Session 1: Fix Critical Issues** (~30-45 minutes)
**AI Coding Time: ~10 minutes**

**Tasks:**
1. Replace regex HTML parsing with BeautifulSoup in `reverse_discovery.py`
2. Add basic health check function
3. Improve error logging
4. Add API quota tracking (optional)

**Files to Create/Modify:**
- `reverse_discovery.py` (rewrite parsing functions)
- `health_check.py` (new file)
- `requirements.txt` (add beautifulsoup4, lxml)

**Testing:**
- Run discovery locally
- Verify BeautifulSoup parsing works
- Check logs for proper error messages

---

### **Session 2: Deployment Setup** (~45-60 minutes)
**AI Coding Time: ~10 minutes**

**Tasks:**
1. Create deployment script
2. Create systemd service file (or Windows Task Scheduler XML)
3. Create simple monitoring script
4. Write deployment documentation

**Files to Create:**
- `deploy.sh` (or `deploy.ps1` for Windows)
- `counter-exposure.service` (Linux systemd)
- `monitor.py` (health checks + restart logic)
- `DEPLOYMENT.md` (step-by-step guide)

**Environment Options:**
- **Linux VPS**: DigitalOcean, Linode, Vultr ($5-6/month)
- **Windows VPS**: Azure, AWS ($10-15/month)
- **Local Machine**: Free (if always-on PC available)

**Deployment:**
- Set up VPS
- Install Python + dependencies
- Configure .env with API keys
- Set up cron job or scheduled task
- Test first run

---

### **Session 3: Monitoring & Polish** (~20-30 minutes)
**AI Coding Time: ~5 minutes**

**Tasks:**
1. Add email/webhook alerts on failures
2. Create backup script for SQLite database
3. Add statistics dashboard script
4. Document operational procedures

**Files to Create:**
- `alerts.py` (notification system)
- `backup.sh` (database backups)
- `stats_dashboard.py` (view discovery metrics)
- `OPERATIONS.md` (how to maintain)

**Setup:**
- Configure alert destinations
- Schedule daily database backups
- Test alert system
- Monitor for 1 week

---

## 🛠️ Technical Details

### Session 1 Deep Dive: Fix Reverse Discovery

**Problem**: 
```python
# Current fragile code in reverse_discovery.py
result_pattern = r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"'  # BREAKS EASILY
```

**Solution**:
```python
# New robust code with BeautifulSoup
from bs4 import BeautifulSoup

def _parse_google_results(self, html: str, page_num: int) -> List[SearchResult]:
    soup = BeautifulSoup(html, 'lxml')
    results = []
    
    # Find all search result divs
    for result_div in soup.select('div.g'):
        title_elem = result_div.select_one('h3')
        link_elem = result_div.select_one('a')
        snippet_elem = result_div.select_one('div.VwiC3b')
        
        if title_elem and link_elem:
            results.append(SearchResult(
                title=title_elem.get_text(),
                url=link_elem['href'],
                snippet=snippet_elem.get_text() if snippet_elem else '',
                source="google",
                timestamp=time.time(),
                rank=(page_num - 1) * 10 + len(results) + 1
            ))
    
    return results
```

**Updates Needed**:
- `requirements.txt`: Add `beautifulsoup4>=4.12.0` and `lxml>=5.0.0`
- `reverse_discovery.py`: Rewrite `_parse_google_results()` and `_parse_youtube_results()`
- Add error handling for changed HTML structure
- Add fallback strategy if parsing fails

---

### Session 2 Deep Dive: Deployment

**Linux VPS Deployment Script** (`deploy.sh`):
```bash
#!/bin/bash
set -e

echo "🚀 Counter-Exposure Engine Deployment"

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install -y python3.10 python3-pip python3-venv git

# Clone repository (or upload files)
cd /opt
sudo git clone <your-repo-url> counter-exposure
cd counter-exposure/CascadeProjects/windsurf-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env and add API keys!"
    nano .env
fi

# Test run
echo "Testing discovery..."
python run_engine.py --mode streams --count 5

# Install systemd service
sudo cp counter-exposure.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable counter-exposure.timer
sudo systemctl start counter-exposure.timer

echo "✅ Deployment complete!"
echo "Check status: sudo systemctl status counter-exposure.timer"
```

**Systemd Service** (`counter-exposure.service`):
```ini
[Unit]
Description=Counter-Exposure Engine Discovery
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/opt/counter-exposure/CascadeProjects/windsurf-project
ExecStart=/opt/counter-exposure/CascadeProjects/windsurf-project/venv/bin/python run_engine.py --mode combined --count 20 --output /var/log/counter-exposure/feed.json
StandardOutput=append:/var/log/counter-exposure/service.log
StandardError=append:/var/log/counter-exposure/error.log

[Install]
WantedBy=multi-user.target
```

**Systemd Timer** (`counter-exposure.timer`):
```ini
[Unit]
Description=Run Counter-Exposure Engine every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

---

### Session 3 Deep Dive: Monitoring

**Health Check Script** (`monitor.py`):
```python
#!/usr/bin/env python3
"""
Monitor Counter-Exposure Engine health and send alerts.
Run this script periodically (e.g., every 15 minutes).
"""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.message import EmailMessage

def check_recent_discoveries(db_path: str, hours: int = 2) -> dict:
    """Check if discoveries happened recently."""
    conn = sqlite3.connect(db_path)
    cutoff = (datetime.now() - timedelta(hours=hours)).timestamp()
    
    cursor = conn.execute(
        "SELECT COUNT(*) FROM exposures WHERE exposed_at >= ?",
        (cutoff,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    
    return {
        "status": "healthy" if count > 0 else "stale",
        "discoveries_last_2h": count
    }

def check_log_errors(log_path: str, lines: int = 100) -> dict:
    """Check recent log entries for errors."""
    if not Path(log_path).exists():
        return {"status": "unknown", "errors": 0}
    
    with open(log_path, 'r') as f:
        recent_lines = f.readlines()[-lines:]
    
    errors = [line for line in recent_lines if 'ERROR' in line]
    
    return {
        "status": "unhealthy" if len(errors) > 5 else "healthy",
        "error_count": len(errors),
        "recent_errors": errors[-3:] if errors else []
    }

def send_alert(subject: str, body: str):
    """Send email alert (configure SMTP settings)."""
    # TODO: Configure with your email settings
    pass

def main():
    health = {
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": check_recent_discoveries("exposure_tracker.db"),
            "logs": check_log_errors("counter_exposure_engine.log")
        }
    }
    
    # Overall health
    all_healthy = all(
        check["status"] == "healthy" 
        for check in health["checks"].values()
    )
    
    health["overall"] = "healthy" if all_healthy else "unhealthy"
    
    # Save health status
    Path("health.json").write_text(json.dumps(health, indent=2))
    
    # Alert if unhealthy
    if not all_healthy:
        print(f"⚠️  System unhealthy: {health}")
        # send_alert("Counter-Exposure Alert", json.dumps(health, indent=2))
    else:
        print(f"✅ System healthy")
    
    return 0 if all_healthy else 1

if __name__ == "__main__":
    exit(main())
```

---

## 📈 Success Metrics

### After Session 1:
- [ ] Reverse discovery works without regex parsing
- [ ] No errors when running `python run_engine.py --mode combined`
- [ ] Tests pass: `pytest tests/ -v`

### After Session 2:
- [ ] Service running on VPS
- [ ] Discoveries happening every hour
- [ ] Database growing with new entries
- [ ] Logs show successful runs

### After Session 3:
- [ ] Health checks run automatically
- [ ] Alerts configured and tested
- [ ] 7 days of stable operation
- [ ] Database backed up daily

---

## 🔧 Quick Commands Reference

### Development
```bash
# Run discovery locally
python run_engine.py --mode combined --count 10

# Run tests
pytest tests/ -v

# Check for errors
python -m pytest tests/ --cov=. --cov-report=html
```

### Deployment (Linux)
```bash
# Check service status
sudo systemctl status counter-exposure.timer
sudo systemctl status counter-exposure.service

# View logs
sudo journalctl -u counter-exposure.service -f
tail -f /var/log/counter-exposure/service.log

# Manual run
cd /opt/counter-exposure/CascadeProjects/windsurf-project
source venv/bin/activate
python run_engine.py --mode combined --count 20
```

### Monitoring
```bash
# Check health
python monitor.py

# View recent discoveries
sqlite3 exposure_tracker.db "SELECT * FROM exposures ORDER BY exposed_at DESC LIMIT 10;"

# Check database size
du -h exposure_tracker.db
```

---

## 💰 Cost Estimates

### Option A: Basic VPS Deployment
- **VPS**: $5-6/month (DigitalOcean, Linode, Vultr)
- **Total**: $5-6/month

### Option B: Web Service
- **VPS**: $10-12/month (2GB RAM)
- **Domain**: $10-15/year
- **SSL**: Free (Let's Encrypt)
- **Total**: $12-15/month

### Option C: Production Scale
- **Cloud VPS**: $20-50/month
- **Database**: $15-30/month (managed PostgreSQL)
- **Monitoring**: $10-20/month (if using paid service)
- **Domain + CDN**: $15-30/month
- **Total**: $60-130/month

---

## 🎯 Next Steps

1. **Read this document fully** ✓
2. **Decide on deployment option** (A, B, or C)
3. **Schedule Session 1** (fix critical issues)
4. **Execute sessions** as outlined above
5. **Monitor and iterate**

---

## 📚 Additional Resources

- [DigitalOcean VPS Setup](https://www.digitalocean.com/docs/droplets/how-to/create/)
- [Systemd Service Tutorial](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Python Application Deployment](https://realpython.com/python-application-layouts/)

---

**Last Updated**: October 5, 2025
**Status**: Ready for Session 1
