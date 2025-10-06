#!/usr/bin/env python3
"""
Quick share script - Upload feed to GitHub Gist for easy sharing.
"""
import json
import os
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests

def upload_to_gist():
    """Upload counter_exposure_feed.html to GitHub Gist."""
    
    # Read the HTML file
    html_file = Path("counter_exposure_feed.html")
    if not html_file.exists():
        print("❌ counter_exposure_feed.html not found!")
        print("Run 'python simple_web_ui.py' first to generate the feed.")
        return None
    
    html_content = html_file.read_text(encoding='utf-8')
    
    # Create gist payload
    gist_data = {
        "description": "Counter-Exposure Engine - Discovered Underexposed Content",
        "public": True,
        "files": {
            "counter_exposure_feed.html": {
                "content": html_content
            }
        }
    }
    
    # Get GitHub token (optional, but recommended for managing your gists)
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {}
    
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        print("🔐 Using GitHub token from environment")
    else:
        print("💡 Tip: Set GITHUB_TOKEN env var to manage your gists")
    
    # Upload to GitHub Gist
    print("📤 Uploading to GitHub Gist...")
    response = requests.post(
        'https://api.github.com/gists',
        headers=headers,
        json=gist_data
    )
    
    if response.status_code == 201:
        gist_url = response.json()['html_url']
        raw_url = response.json()['files']['counter_exposure_feed.html']['raw_url']
        
        print("\n✅ Success! Your feed is now public:")
        print(f"\n📺 View: {gist_url}")
        print(f"🔗 Direct link: {raw_url}")
        print(f"\n👥 Share this URL with your friend!")
        
        return gist_url
    else:
        print(f"\n❌ Upload failed: {response.status_code}")
        print(response.json())
        return None

def main():
    print("🚀 Counter-Exposure Feed Sharer")
    print("=" * 50)
    
    # Check if feed exists, if not, generate it
    if not Path("counter_exposure_feed.html").exists():
        print("📊 Feed not found. Generating...")
        os.system("python simple_web_ui.py")
    
    # Upload to gist
    url = upload_to_gist()
    
    if url:
        print("\n💡 To update the feed:")
        print("   1. Run: python simple_web_ui.py")
        print("   2. Run: python share.py")
        print("\n🎉 Your friend can now see your discoveries!")

if __name__ == "__main__":
    main()
