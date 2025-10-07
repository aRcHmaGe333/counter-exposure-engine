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
                
                # Expanded search terms for deep discovery
                search_terms = [
                    # Entertainment
                    "gaming", "music", "art", "animation", "comedy", "podcast", "vlog",
                    "stream", "speedrun", "playthrough", "walkthrough", "lets play",
                    
                    # Educational
                    "tutorial", "how to", "guide", "lesson", "course", "lecture",
                    "explained", "documentary", "science", "history", "math",
                    
                    # Creative
                    "drawing", "painting", "digital art", "3d modeling", "photography",
                    "filmmaking", "editing", "music production", "beatmaking", "mixing",
                    
                    # Tech & Dev
                    "programming", "coding", "web dev", "app dev", "gamedev",
                    "tech review", "unboxing", "hardware", "software", "linux",
                    
                    # Lifestyle
                    "cooking", "baking", "recipe", "fitness", "workout", "yoga",
                    "travel", "vlogging", "daily vlog", "asmr", "meditation",
                    
                    # Hobbies
                    "crafts", "diy", "woodworking", "electronics", "robotics",
                    "gardening", "fishing", "camping", "hiking", "cycling",
                    
                    # Performance
                    "singing", "dancing", "instrument", "guitar", "piano", "drums",
                    "beat boxing", "acapella", "cover song", "original song",
                    
                    # Business
                    "entrepreneur", "startup", "business tips", "marketing",
                    "freelance", "side hustle", "investing", "crypto",
                    
                    # Innovation & Science
                    "invention", "innovation", "prototype", "experiment",
                    "chemistry experiment", "physics demo", "science project",
                    "engineering", "robotics project", "maker", "arduino",
                    "3d printing", "cnc", "laser cutting", "soldering",
                    
                    # Underground/Alternative
                    "independent film", "short film", "student film",
                    "underground music", "bedroom producer", "lo-fi beats",
                    "experimental art", "avant garde", "abstract",
                    "zine", "indie comic", "webcomic",
                    
                    # Deep Learning Niches
                    "restoration", "repair", "fix", "refurbish",
                    "thrifting", "vintage", "antique", "collecting",
                    "urban exploration", "abandoned", "history exploration",
                    "foraging", "wildcrafting", "homesteading", "off grid",
                    
                    # Skill Mastery
                    "practice session", "skill building", "progress video",
                    "study with me", "time lapse", "process video",
                    "behind the scenes", "making of", "studio tour",
                    
                    # Micro-Niches (goldmine territory)
                    "mechanical keyboard", "fountain pen", "watch repair",
                    "miniatures", "diorama", "scale model", "terrarium",
                    "lockpicking", "puzzle solving", "rubiks cube",
                    "whistling", "juggling", "poi spinning", "kendama",
                    
                    # Language/Cultural
                    "language learning", "polyglot", "speaking practice",
                    "cultural vlog", "expat life", "living abroad",
                    "traditional music", "folk song", "indigenous",
                    "dialect", "regional cuisine", "local history",
                    
                    # Underrated Formats
                    "unedited", "raw footage", "no commentary",
                    "ambient", "soundscape", "field recording",
                    "slideshow", "photo essay", "visual poem",
                    "voice over", "narration", "storytelling",
                    
                    # Problem-Solving Content
                    "debugging", "troubleshooting", "problem solving",
                    "case study", "analysis", "breakdown", "explained",
                    "comparison", "versus", "before and after",
                    
                    # Niche Communities
                    "retro gaming", "indie game", "pixel art", "chiptune",
                    "speedcubing", "card tricks", "origami", "calligraphy",
                    
                    # Languages (underexposed in English-speaking markets)
                    "music spanish", "tutorial arabic", "vlog japanese",
                    "gaming portuguese", "cooking italian", "tech german"
                ]
                
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0a0e27;
            background-image: 
                radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.1) 0px, transparent 50%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        
        .header {{ 
            text-align: center; 
            margin-bottom: 60px;
            position: relative;
        }}
        
        .header h1 {{ 
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 700;
            background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            animation: fadeInUp 0.8s ease;
        }}
        
        .header p {{
            color: #94a3b8;
            font-size: 1.1rem;
            animation: fadeInUp 0.8s ease 0.2s both;
        }}
        
        .stats {{ 
            display: flex; 
            justify-content: center; 
            gap: 20px; 
            margin: 40px 0;
            flex-wrap: wrap;
            animation: fadeInUp 0.8s ease 0.4s both;
        }}
        
        .stat {{ 
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 20px 30px; 
            border-radius: 16px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .stat:hover {{
            transform: translateY(-5px);
            border-color: #10b981;
            box-shadow: 0 10px 40px rgba(16, 185, 129, 0.2);
        }}
        
        .stat-number {{ 
            font-size: 2.5em; 
            font-weight: 700; 
            background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: block;
        }}
        
        .stat-label {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 8px;
        }}
        
        .content-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); 
            gap: 24px; 
            max-width: 1400px;
            margin: 0 auto;
            animation: fadeIn 1s ease 0.6s both;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes shimmer {{
            0% {{ background-position: -1000px 0; }}
            100% {{ background-position: 1000px 0; }}
        }}
        
        .content-item {{ 
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px; 
            padding: 24px; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }}
        
        .content-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
            transition: left 0.5s;
        }}
        
        .content-item:hover::before {{
            left: 100%;
        }}
        
        .content-item:hover {{ 
            transform: translateY(-8px) scale(1.02); 
            border-color: #10b981; 
            box-shadow: 0 20px 60px rgba(16, 185, 129, 0.3);
        }}
        
        .content-item.live {{ 
            border-left: 3px solid #ef4444;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(255,255,255,0.03) 100%);
        }}
        
        .content-item.underexposed {{ 
            border-left: 3px solid #10b981; 
        }}
        
        .platform {{ 
            position: absolute; 
            top: 16px; 
            right: 16px; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .platform.youtube {{ 
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
        }}
        
        .platform.web {{ 
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}
        
        .title {{ 
            font-size: 1.25rem; 
            font-weight: 600; 
            margin: 12px 0 8px 0; 
            color: #f1f5f9;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .channel {{ 
            color: #10b981; 
            margin: 8px 0; 
            font-weight: 500;
            font-size: 0.95rem;
        }}
        
        .description {{ 
            color: #94a3b8; 
            margin: 12px 0; 
            line-height: 1.6;
            font-size: 0.9rem;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .metrics {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin: 16px 0; 
            padding: 12px 0;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 0.85rem;
        }}
        
        .views {{ 
            color: #fbbf24;
            font-weight: 600;
        }}
        
        .score {{ 
            color: #10b981; 
            font-weight: 700;
            background: rgba(16, 185, 129, 0.1);
            padding: 4px 10px;
            border-radius: 8px;
        }}
        
        .url {{ 
            color: #6366f1; 
            text-decoration: none; 
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .url:hover {{ 
            color: #10b981; 
            transform: translateX(5px);
        }}
        
        .refresh-info {{ 
            text-align: center; 
            margin: 60px 0 20px 0; 
            color: #64748b; 
            font-size: 0.9rem;
        }}
        
        .live-indicator {{ 
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white; 
            padding: 4px 10px; 
            border-radius: 12px; 
            font-size: 0.75rem; 
            margin-left: 10px;
            font-weight: 600;
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.8; transform: scale(0.95); }}
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
