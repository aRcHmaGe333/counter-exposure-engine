#!/usr/bin/env python3
"""
Quick YouTube API Test - No server needed
Tests your YouTube API key and discovers live streams locally.
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from youtube_client import YouTubeDiscovery
from loguru import logger

def test_youtube_api():
    """Test YouTube API with your key."""
    
    # Try to get API key from multiple sources
    api_key = None
    
    # 1. Try environment variable (after restart)
    api_key = os.getenv('YOUTUBE_API_KEY')
    if api_key and api_key != 'your_youtube_api_key_here':
        print(f"✅ Found API key from environment: {api_key[:10]}...")
    else:
        # 2. Ask user to paste it directly
        print("🔑 YouTube API key not found in environment.")
        print("Please paste your YouTube API key here:")
        api_key = input("API Key: ").strip()
        
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return
    
    print(f"\n🎯 Testing YouTube API with key: {api_key[:10]}...")
    
    # Create YouTube client
    try:
        client = YouTubeDiscovery(api_key=api_key)
        print("✅ YouTube client created successfully")
    except Exception as e:
        print(f"❌ Failed to create YouTube client: {e}")
        return
    
    # Test API connection
    print("\n🔍 Searching for live streams...")
    try:
        # Test basic API functionality first
        print("   Testing basic API access...")
        try:
            # Test with a simple search (not live-specific)
            response = client._make_request(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    'key': api_key,
                    'part': 'snippet',
                    'type': 'video',
                    'maxResults': 5,
                    'q': 'test'
                }
            )
            if response and response.get('items'):
                print(f"   ✅ Basic API access working - found {len(response['items'])} videos")
            else:
                print("   ❌ Basic API access failed - no results")
                return
        except Exception as e:
            print(f"   ❌ Basic API test failed: {e}")
            return

        # Now test live streams specifically
        print("   Testing live stream search...")
        streams = []
        test_queries = ["gaming", "music", "news", ""]

        for query in test_queries:
            print(f"   Trying live query: '{query}'...")
            try:
                result_streams, _ = client.fetch_live_streams(query=query, max_results=10)
                if result_streams:
                    streams.extend(result_streams)
                    print(f"   ✅ Found {len(result_streams)} live streams with query '{query}'")
                    break
                else:
                    print(f"   ⚠️  No live streams found with query '{query}'")
            except Exception as e:
                print(f"   ❌ Error with live query '{query}': {e}")

        if not streams:
            print("\n⚠️  No live streams found with any query. This could mean:")
            print("   - No live streams are currently active")
            print("   - API key doesn't have proper permissions")
            print("   - YouTube API quota exceeded")
            print("   - YouTube Data API v3 not enabled for your project")
            return
        
        print(f"🎉 Found {len(streams)} live streams!")
        print("\n📺 Live Streams Discovered:")
        print("=" * 80)
        
        for i, stream in enumerate(streams[:5], 1):  # Show first 5
            print(f"{i}. 📺 {stream.title[:60]}...")
            print(f"   👤 Channel: {stream.channel_name}")
            print(f"   👀 Viewers: {stream.viewer_count}")
            print(f"   🔗 URL: {stream.url}")
            print(f"   🏷️  Category: {stream.category}")
            print()
        
        # Show underexposed streams (≤5 viewers)
        underexposed = [s for s in streams if s.viewer_count <= 5]
        if underexposed:
            print(f"\n🎯 Underexposed Streams ({len(underexposed)} found):")
            print("=" * 50)
            for stream in underexposed:
                print(f"📺 {stream.title[:50]}... | 👀 {stream.viewer_count} viewers")
                print(f"   🔗 {stream.url}")
                print()
        else:
            print("\n⚠️  No underexposed streams found (all have >5 viewers)")
        
        # Test pagination
        print(f"\n🔄 Testing pagination...")
        all_streams = client.fetch_all_pages(query="gaming", max_pages=2)
        print(f"✅ Fetched {len(all_streams)} total streams across multiple pages")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        if "quotaExceeded" in str(e):
            print("💡 This looks like a quota issue. Try again tomorrow or check your API limits.")
        elif "forbidden" in str(e).lower():
            print("💡 This looks like a permissions issue. Make sure your API key has YouTube Data API v3 enabled.")
        elif "invalid" in str(e).lower():
            print("💡 This looks like an invalid API key. Double-check your key.")
        return False

def create_simple_web_viewer():
    """Create a simple HTML file to view results locally."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Counter-Exposure Engine - Local Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .stream { border: 1px solid #333; margin: 10px 0; padding: 15px; border-radius: 8px; background: #2a2a2a; }
        .title { font-size: 18px; font-weight: bold; color: #4CAF50; }
        .channel { color: #81C784; margin: 5px 0; }
        .viewers { color: #FFA726; }
        .url { color: #64B5F6; text-decoration: none; }
        .underexposed { border-left: 4px solid #FF5722; }
        h1 { color: #4CAF50; }
        .refresh-btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🎯 Counter-Exposure Engine - Live Streams</h1>
    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    <div id="streams">
        <p>Run the Python script to populate this page with live streams!</p>
        <p>Command: <code>python test_youtube_live.py</code></p>
    </div>
    
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => location.reload(), 300000);
    </script>
</body>
</html>
"""
    
    html_file = Path("local_viewer.html")
    html_file.write_text(html_content, encoding='utf-8')
    print(f"Created local viewer: {html_file.absolute()}")
    print("Open this file in your browser to view results!")

if __name__ == "__main__":
    print("🚀 Counter-Exposure Engine - YouTube API Test")
    print("=" * 50)
    
    # Create local HTML viewer
    create_simple_web_viewer()
    
    # Test YouTube API
    success = test_youtube_api()
    
    if success:
        print("\n✅ YouTube API test completed successfully!")
        print("💡 Your API key is working and you can discover live streams.")
        print("\n🎯 Next steps:")
        print("   1. Open 'local_viewer.html' in your browser")
        print("   2. Run the full engine: python run_engine.py --mode streams --count 10")
        print("   3. Or restart terminal and try: python run_engine.py --mode streams")
    else:
        print("\n❌ YouTube API test failed.")
        print("💡 Check your API key and try again.")
