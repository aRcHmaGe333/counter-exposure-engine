#!/usr/bin/env python3
"""
Simple web server to serve the Counter-Exposure feed.
Refreshes discoveries every hour automatically.
"""
import asyncio
import time
from pathlib import Path
from datetime import datetime
from threading import Thread

# Try FastAPI first, fall back to Flask
try:
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    USE_FASTAPI = True
except ImportError:
    from flask import Flask, send_file
    USE_FASTAPI = False

from simple_web_ui import SimpleWebUI
from exposure_engine import CounterExposureEngine
from loguru import logger

# Background discovery task
def run_discovery_loop():
    """Run discovery every hour in background."""
    ui = SimpleWebUI()
    
    while True:
        try:
            logger.info("🔍 Starting discovery...")
            ui.run()
            logger.info("✅ Discovery complete!")
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
        
        # Wait 1 hour
        logger.info("💤 Sleeping for 1 hour...")
        time.sleep(3600)

# Initialize discovery on startup
logger.info("🚀 Running initial discovery...")
try:
    ui = SimpleWebUI()
    ui.run()
except Exception as e:
    logger.error(f"Initial discovery failed: {e}")

# Start background discovery thread
discovery_thread = Thread(target=run_discovery_loop, daemon=True)
discovery_thread.start()

# Web Server Setup
if USE_FASTAPI:
    app = FastAPI(title="Counter-Exposure Engine")
    
    @app.get("/")
    async def serve_root():
        """Serve the main feed page."""
        html_file = Path("counter_exposure_feed.html")
        if html_file.exists():
            return FileResponse(html_file)
        return HTMLResponse("<h1>Feed not generated yet. Check back in a moment!</h1>")
    
    @app.get("/feed.json")
    async def feed_json():
        """Serve raw feed data."""
        json_file = Path("feed_data.json")
        if json_file.exists():
            return FileResponse(json_file)
        return {"error": "Feed not generated yet"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        html_exists = Path("counter_exposure_feed.html").exists()
        db_exists = Path("exposure_tracker.db").exists()
        
        return {
            "status": "healthy" if html_exists and db_exists else "initializing",
            "feed_exists": html_exists,
            "database_exists": db_exists,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/stats")
    async def get_stats():
        """Get discovery statistics."""
        try:
            engine = CounterExposureEngine()
            return engine.get_stats()
        except Exception as e:
            return {"error": str(e)}
    
    @app.post("/discover")
    async def trigger_discovery():
        """Manually trigger discovery."""
        try:
            ui = SimpleWebUI()
            content = ui.run()
            return {
                "status": "success",
                "items_discovered": len(content),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

else:
    # Flask fallback
    app = Flask(__name__)
    
    @app.route("/")
    def serve_root_flask():
        html_file = Path("counter_exposure_feed.html")
        if html_file.exists():
            return send_file(html_file)
        return "<h1>Feed not generated yet. Check back in a moment!</h1>"
    
    @app.route("/health")
    def health_check_flask():
        html_exists = Path("counter_exposure_feed.html").exists()
        db_exists = Path("exposure_tracker.db").exists()
        
        return {
            "status": "healthy" if html_exists and db_exists else "initializing",
            "feed_exists": html_exists,
            "database_exists": db_exists,
            "timestamp": datetime.now().isoformat()
        }

# Run server
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    
    if USE_FASTAPI:
        logger.info(f"🚀 Starting FastAPI server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        logger.info(f"🚀 Starting Flask server on port {port}")
        app.run(host="0.0.0.0", port=port)
