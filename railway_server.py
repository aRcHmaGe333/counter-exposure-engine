#!/usr/bin/env python3
"""
Railway-optimized entry point with auto-discovery loop.
Runs web server + background discovery without modifying existing code.
"""
import os
import sys
import time
import threading
from pathlib import Path

# Import existing working code (ZERO MODIFICATIONS)
from simple_web_ui import SimpleWebUI
from loguru import logger

# Configuration
DISCOVERY_INTERVAL = 3600  # 1 hour in seconds
PORT = int(os.environ.get("PORT", 8000))

def discovery_loop():
    """Background thread that runs discovery every hour."""
    ui = SimpleWebUI()
    
    # Initial discovery on startup
    logger.info("🚀 Running initial discovery...")
    try:
        ui.run()
        logger.info("✅ Initial discovery complete")
    except Exception as e:
        logger.error(f"❌ Initial discovery failed: {e}")
    
    # Continuous loop
    while True:
        try:
            logger.info(f"💤 Sleeping for {DISCOVERY_INTERVAL/60} minutes...")
            time.sleep(DISCOVERY_INTERVAL)
            
            logger.info("🔍 Running scheduled discovery...")
            ui.run()
            logger.info("✅ Discovery complete")
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            # Continue loop even if discovery fails

def start_server():
    """Start the web server."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import FileResponse, HTMLResponse
        import uvicorn
        
        app = FastAPI(title="Counter-Exposure Engine")
        
        @app.get("/")
        async def root():
            """Serve the main feed page."""
            html_file = Path("counter_exposure_feed.html")
            if html_file.exists():
                return FileResponse(html_file)
            return HTMLResponse(
                "<h1>🔍 Discovering content...</h1>"
                "<p>First discovery run in progress. Refresh in a moment!</p>"
            )
        
        @app.get("/health")
        async def health():
            """Health check for Railway."""
            return {
                "status": "healthy",
                "feed_exists": Path("counter_exposure_feed.html").exists()
            }
        
        logger.info(f"🚀 Starting web server on port {PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
        
    except ImportError:
        # Fallback to Flask if FastAPI not available
        from flask import Flask, send_file
        
        app = Flask(__name__)
        
        @app.route("/")
        def root():
            html_file = Path("counter_exposure_feed.html")
            if html_file.exists():
                return send_file(html_file)
            return "<h1>🔍 Discovering content...</h1><p>Refresh in a moment!</p>"
        
        @app.route("/health")
        def health():
            return {"status": "healthy"}
        
        logger.info(f"🚀 Starting Flask server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎯 Counter-Exposure Engine - Railway Deployment")
    logger.info("=" * 60)
    
    # Start discovery loop in background thread
    discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
    discovery_thread.start()
    logger.info("✅ Discovery loop started (updates every hour)")
    
    # Start web server in main thread
    start_server()
