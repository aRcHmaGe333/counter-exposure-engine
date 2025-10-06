#!/usr/bin/env python3
"""
Simple Web UI for Counter-Exposure Engine
Creates a local HTML file that auto-refreshes with discovered content.
No server needed - just open the HTML file in your browser!
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from youtube_client import YouTubeDiscovery
from reverse_discovery import ReverseSearchDiscovery, ContentFilter
from llm_filter import LLMContentValidator
from loguru import logger

class SimpleWebUI:
    """Creates a local web interface without needing a server."""
    
    def __init__(self):
        self.output_file = Path("counter_exposure_feed.html")
        self.data_file = Path("feed_data.json")
        self.validator = LLMContentValidator()  # Initialize LLM validator
        
    def discover_content(self):
        """Discover content from all available sources."""
        all_content = []
        
        # Get API key
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key or api_key == 'your_youtube_api_key_here':
            print("Enter your YouTube API key:")
            api_key = input("API Key: ").strip()
        
        # YouTube Discovery
        if api_key:
            print("🔍 Discovering YouTube content...")
            try:
                yt_client = YouTubeDiscovery(api_key=api_key)
                
                # Try different search strategies
                search_terms = ["gaming", "music", "tutorial", "vlog", "tech", "art"]
                
                for term in search_terms:
                    try:
                        # Search for regular videos (not just live)
                        response = yt_client._make_request(
                            "https://www.googleapis.com/youtube/v3/search",
                            params={
                                'key': api_key,
                                'part': 'snippet',
                                'type': 'video',
                                'maxResults': 10,
                                'q': term,
                                'order': 'date',  # Get newest first
                                'publishedAfter': (datetime.now().replace(hour=0, minute=0, second=0)).isoformat() + 'Z'
                            }
                        )
                        
                        if response and response.get('items'):
                            for item in response['items']:
                                snippet = item['snippet']
                                video_id = item['id']['videoId']
                                
                                # Get video statistics
                                stats_response = yt_client._make_request(
                                    "https://www.googleapis.com/youtube/v3/videos",
                                    params={
                                        'key': api_key,
                                        'part': 'statistics,liveStreamingDetails',
                                        'id': video_id
                                    }
                                )
                                
                                view_count = 0
                                is_live = False
                                if stats_response and stats_response.get('items'):
                                    stats = stats_response['items'][0].get('statistics', {})
                                    view_count = int(stats.get('viewCount', 0))
                                    is_live = 'liveStreamingDetails' in stats_response['items'][0]
                                
                                # Focus on TRULY underexposed content (very low views)
                                if view_count <= 500:  # Much stricter underexposed threshold
                                    # Validate content matches search intent
                                    validation = self.validator.validate_search_match(
                                        term,
                                        snippet['title'],
                                        snippet['description']
                                    )
                                    
                                    if validation['is_match']:
                                        all_content.append({
                                            'title': snippet['title'],
                                            'channel': snippet['channelTitle'],
                                            'url': f"https://www.youtube.com/watch?v={video_id}",
                                            'thumbnail': snippet['thumbnails'].get('medium', {}).get('url', ''),
                                            'description': snippet['description'][:200] + '...',
                                            'view_count': view_count,
                                            'published': snippet['publishedAt'],
                                            'platform': 'YouTube',
                                            'is_live': is_live,
                                            'category': term,
                                            'underexposure_score': max(0, 1000 - view_count) / 1000,
                                            'validation_confidence': validation['confidence']
                                        })
                                    else:
                                        logger.debug(f"Filtered out '{snippet['title']}': {validation['reason']}")
                            
                            found_count = len([c for c in all_content if c['category'] == term])
                            print(f"   Found {found_count} underexposed videos for '{term}'")
                            if found_count > 0:
                                print("   📺 Sample discoveries:")
                                for item in [c for c in all_content if c['category'] == term][-3:]:  # Show last 3
                                    print(f"      • {item['title'][:50]}... ({item['view_count']} views)")
                                    print(f"        🔗 {item['url']}")
                                print()
                    except Exception as e:
                        print(f"   Error searching for '{term}': {e}")
                        
            except Exception as e:
                print(f"❌ YouTube discovery failed: {e}")
        
        # Reverse Discovery
        print("🔍 Running reverse discovery...")
        try:
            reverse_discovery = ReverseSearchDiscovery()
            content_filter = ContentFilter()
            
            queries = ["new indie game", "small creator", "unknown artist", "underrated"]
            reverse_results = reverse_discovery.discover_underexposed_content(queries)
            filtered_results = content_filter.filter_results(reverse_results)
            
            for result in filtered_results[:20]:  # Limit to top 20
                all_content.append({
                    'title': result.title,
                    'channel': 'Unknown',
                    'url': result.url,
                    'thumbnail': '',
                    'description': result.snippet,
                    'view_count': 0,
                    'published': datetime.now().isoformat(),
                    'platform': 'Web Search',
                    'is_live': False,
                    'category': 'reverse_discovery',
                    'underexposure_score': (result.rank or 0) / 1000
                })
            
            print(f"   Found {len(filtered_results)} items via reverse discovery")
            if len(filtered_results) > 0:
                print("   🔍 Sample reverse discoveries:")
                for result in filtered_results[:3]:  # Show first 3
                    print(f"      • {result.title[:50]}...")
                    print(f"        🔗 {result.url}")
                print()
            
        except Exception as e:
            print(f"❌ Reverse discovery failed: {e}")
        
        # Sort by underexposure score
        all_content.sort(key=lambda x: x['underexposure_score'], reverse=True)
        
        print(f"🎯 Total underexposed content discovered: {len(all_content)}")

        # Show summary of what was actually found
        if all_content:
            print("\n📋 DISCOVERY SUMMARY:")
            print("=" * 40)
            youtube_count = len([c for c in all_content if c['platform'] == 'YouTube'])
            web_count = len([c for c in all_content if c['platform'] == 'Web Search'])
            live_count = len([c for c in all_content if c['is_live']])
            ultra_low = len([c for c in all_content if c['view_count'] <= 100])

            print(f"📺 YouTube Videos: {youtube_count}")
            print(f"🔍 Web Search Results: {web_count}")
            print(f"🔴 Live Streams: {live_count}")
            print(f"⭐ Ultra-Underexposed (≤100 views): {ultra_low}")

            print(f"\n🎯 TOP 5 MOST UNDEREXPOSED:")
            for i, item in enumerate(all_content[:5], 1):
                print(f"{i}. {item['title'][:60]}...")
                print(f"   👀 {item['view_count']} views | 📊 Score: {item['underexposure_score']:.3f}")
                print(f"   🔗 {item['url']}")
                print()
        else:
            print("\n⚠️  NO CONTENT DISCOVERED - This could mean:")
            print("   • No underexposed content available right now")
            print("   • API rate limits reached")
            print("   • Search parameters too restrictive")

        return all_content
    
    def generate_html(self, content):
        """Generate HTML page with discovered content."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Counter-Exposure Engine - Live Feed</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
            color: #fff; 
            min-height: 100vh;
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            padding: 20px;
            background: rgba(76, 175, 80, 0.1);
            border-radius: 10px;
            border: 1px solid #4CAF50;
        }}
        .header h1 {{ 
            color: #4CAF50; 
            margin: 0;
            font-size: 2.5em;
        }}
        .stats {{ 
            display: flex; 
            justify-content: center; 
            gap: 30px; 
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .stat {{ 
            background: rgba(255,255,255,0.1); 
            padding: 15px 25px; 
            border-radius: 8px; 
            text-align: center;
        }}
        .stat-number {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #4CAF50; 
        }}
        .content-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); 
            gap: 20px; 
            margin-top: 30px;
        }}
        .content-item {{ 
            background: rgba(255,255,255,0.05); 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 12px; 
            padding: 20px; 
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        .content-item:hover {{ 
            transform: translateY(-5px); 
            border-color: #4CAF50; 
            box-shadow: 0 10px 30px rgba(76, 175, 80, 0.3);
        }}
        .content-item.live {{ 
            border-left: 4px solid #FF5722; 
            background: rgba(255, 87, 34, 0.1);
        }}
        .content-item.underexposed {{ 
            border-left: 4px solid #4CAF50; 
        }}
        .platform {{ 
            position: absolute; 
            top: 10px; 
            right: 10px; 
            background: #4CAF50; 
            color: white; 
            padding: 5px 10px; 
            border-radius: 15px; 
            font-size: 0.8em;
        }}
        .platform.youtube {{ background: #FF0000; }}
        .platform.web {{ background: #2196F3; }}
        .title {{ 
            font-size: 1.2em; 
            font-weight: bold; 
            margin: 10px 0; 
            color: #4CAF50; 
            line-height: 1.4;
        }}
        .channel {{ 
            color: #81C784; 
            margin: 5px 0; 
            font-weight: 500;
        }}
        .description {{ 
            color: #ccc; 
            margin: 10px 0; 
            line-height: 1.5;
            font-size: 0.9em;
        }}
        .metrics {{ 
            display: flex; 
            justify-content: space-between; 
            margin: 15px 0; 
            font-size: 0.9em;
        }}
        .views {{ 
            color: #FFA726; 
        }}
        .score {{ 
            color: #4CAF50; 
            font-weight: bold;
        }}
        .url {{ 
            color: #64B5F6; 
            text-decoration: none; 
            font-size: 0.9em;
            word-break: break-all;
        }}
        .url:hover {{ 
            color: #90CAF9; 
            text-decoration: underline;
        }}
        .refresh-info {{ 
            text-align: center; 
            margin: 30px 0; 
            color: #888; 
            font-style: italic;
        }}
        .live-indicator {{ 
            background: #FF5722; 
            color: white; 
            padding: 3px 8px; 
            border-radius: 10px; 
            font-size: 0.8em; 
            margin-left: 10px;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        .no-content {{ 
            text-align: center; 
            padding: 50px; 
            color: #888; 
            font-size: 1.2em;
        }}
    </style>
    <script>
        // Auto-refresh every 10 minutes
        setTimeout(() => location.reload(), 600000);
        
        // Update timestamp
        function updateTimestamp() {{
            const now = new Date();
            document.getElementById('timestamp').textContent = now.toLocaleString();
        }}
        
        setInterval(updateTimestamp, 1000);
        window.onload = updateTimestamp;
    </script>
</head>
<body>
    <div class="header">
        <h1>Counter-Exposure Engine</h1>
        <p>Discovering underexposed content across platforms</p>
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(content)}</div>
                <div>Items Discovered</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len([c for c in content if c['platform'] == 'YouTube'])}</div>
                <div>YouTube Videos</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len([c for c in content if c['is_live']])}</div>
                <div>Live Streams</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len([c for c in content if c['view_count'] <= 100])}</div>
                <div>Ultra-Underexposed</div>
            </div>
        </div>
        <div class="refresh-info">
            Last updated: <span id="timestamp"></span> | Auto-refresh in 10 minutes
        </div>
    </div>
    
    <div class="content-grid">
"""
        
        if not content:
            html += """
        <div class="no-content">
            <h2>No underexposed content found</h2>
            <p>Try running the discovery again or check your API configuration.</p>
        </div>
"""
        else:
            for item in content:
                live_indicator = '<span class="live-indicator">LIVE</span>' if item['is_live'] else ''
                platform_class = item['platform'].lower().replace(' ', '')
                
                html += f"""
        <div class="content-item {'live' if item['is_live'] else 'underexposed'}">
            <div class="platform {platform_class}">{item['platform']}</div>
            <div class="title">{item['title'][:80]}{'...' if len(item['title']) > 80 else ''}{live_indicator}</div>
            <div class="channel">📺 {item['channel']}</div>
            <div class="description">{item['description']}</div>
            <div class="metrics">
                <span class="views">👀 {item['view_count']:,} views</span>
                <span class="score">📊 Score: {item['underexposure_score']:.3f}</span>
            </div>
            <a href="{item['url']}" target="_blank" class="url">🔗 {item['url'][:60]}{'...' if len(item['url']) > 60 else ''}</a>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def run(self):
        """Run the discovery and generate the web interface."""
        print("🚀 Counter-Exposure Engine - Simple Web UI")
        print("=" * 50)
        
        # Discover content
        content = self.discover_content()
        
        # Save data as JSON
        self.data_file.write_text(json.dumps(content, indent=2, default=str), encoding='utf-8')
        
        # Generate HTML
        html = self.generate_html(content)
        self.output_file.write_text(html, encoding='utf-8')
        
        print(f"\n✅ Web interface generated: {self.output_file.absolute()}")
        print(f"📊 Data saved to: {self.data_file.absolute()}")
        print("\n🌐 Open the HTML file in your browser to view the feed!")
        print("💡 The page will auto-refresh every 10 minutes.")
        
        return content

if __name__ == "__main__":
    ui = SimpleWebUI()
    ui.run()
