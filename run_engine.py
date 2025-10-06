#!/usr/bin/env python3
"""
Counter-Exposure Engine Runner
Main entry point for running the complete counter-exposure system.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from exposure_engine import CounterExposureEngine
from reverse_discovery import ReverseSearchDiscovery, ContentFilter
from config import config
from loguru import logger

def setup_environment():
    """Setup environment variables and configuration."""
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        logger.info("Creating .env template file")
        env_template = """# Counter-Exposure Engine Configuration
# YouTube API Configuration
YOUTUBE_API_KEY=your_youtube_api_key_here

# Twitch API Configuration  
TWITCH_CLIENT_ID=your_twitch_client_id_here
TWITCH_OAUTH_TOKEN=your_twitch_oauth_token_here

# Engine Settings
YOUTUBE_MAX_RESULTS=50
TWITCH_MAX_RESULTS=100
LOG_LEVEL=INFO
REQUEST_TIMEOUT=10
MAX_RETRIES=3
MAX_PAGES=10
"""
        env_file.write_text(env_template)
        logger.warning("Created .env template. Please add your API credentials!")
        return False
    return True

def run_exposure_engine(count: int = 20):
    """Run the main exposure engine."""
    logger.info("🎯 Starting Counter-Exposure Engine")
    
    engine = CounterExposureEngine()
    
    # Generate exposure feed
    feed = engine.generate_exposure_feed(count=count)
    
    if not feed:
        logger.warning("No underexposed streams found!")
        return []
    
    # Display results
    print(f"\n🎯 Counter-Exposure Feed ({len(feed)} streams):")
    print("=" * 80)
    
    for i, item in enumerate(feed, 1):
        print(f"{i:2d}. 📺 {item['platform'].upper()}: {item['title'][:60]}...")
        print(f"     👤 {item['channel_name']} | 👀 {item['viewer_count']} viewers")
        print(f"     🔗 {item['url']}")
        print(f"     📊 Score: {item['underexposure_score']:.3f}")
        print()
    
    # Show stats
    stats = engine.get_stats()
    print(f"\n📈 Engine Statistics:")
    print(json.dumps(stats, indent=2))
    
    return feed

def run_reverse_discovery(queries: list, max_results: int = 20):
    """Run reverse discovery for underexposed content."""
    logger.info("🔍 Starting Reverse Discovery")
    
    discovery = ReverseSearchDiscovery()
    content_filter = ContentFilter()
    
    # Discover content
    results = discovery.discover_underexposed_content(queries)
    
    # Filter results
    filtered_results = content_filter.filter_results(results)
    
    if not filtered_results:
        logger.warning("No underexposed content found!")
        return []
    
    # Display results
    print(f"\n🔍 Reverse Discovery Results ({len(filtered_results)} items):")
    print("=" * 80)
    
    for i, result in enumerate(filtered_results[:max_results], 1):
        print(f"{i:2d}. 📄 {result.title[:60]}...")
        print(f"     🔗 {result.url}")
        print(f"     📝 {result.snippet[:80]}...")
        print(f"     📊 Rank: {result.rank} | Source: {result.source}")
        print()
    
    return filtered_results

def run_combined_discovery(stream_count: int = 10, content_count: int = 10, queries: list = None):
    """Run both exposure engine and reverse discovery."""
    logger.info("🚀 Starting Combined Discovery")
    
    if queries is None:
        queries = ["new indie game", "small streamer", "unknown artist", "underrated content"]
    
    # Run exposure engine
    streams = run_exposure_engine(stream_count)
    
    print("\n" + "="*80)
    
    # Run reverse discovery
    content = run_reverse_discovery(queries, content_count)
    
    return {
        'streams': streams,
        'content': content,
        'total_discovered': len(streams) + len(content)
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Counter-Exposure Engine')
    parser.add_argument('--mode', choices=['streams', 'reverse', 'combined'], 
                       default='combined', help='Discovery mode')
    parser.add_argument('--count', type=int, default=10, 
                       help='Number of results to return')
    parser.add_argument('--queries', nargs='+', 
                       default=["new indie game", "small streamer", "unknown artist"],
                       help='Search queries for reverse discovery')
    parser.add_argument('--output', type=str, help='Output file for results (JSON)')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup environment and exit')
    
    args = parser.parse_args()
    
    # Setup environment if requested
    if args.setup:
        setup_environment()
        return
    
    # Check environment
    if not setup_environment():
        logger.error("Environment not configured. Run with --setup first.")
        return
    
    # Run discovery based on mode
    results = None
    
    if args.mode == 'streams':
        results = {'streams': run_exposure_engine(args.count)}
    elif args.mode == 'reverse':
        results = {'content': run_reverse_discovery(args.queries, args.count)}
    elif args.mode == 'combined':
        results = run_combined_discovery(args.count, args.count, args.queries)
    
    # Save results if output file specified
    if args.output and results:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2, default=str))
        logger.info(f"Results saved to {output_path}")
    
    # Summary
    if results:
        total = 0
        if 'streams' in results:
            total += len(results['streams'])
        if 'content' in results:
            total += len(results['content'])
        if 'total_discovered' in results:
            total = results['total_discovered']
        
        print(f"\n✅ Discovery Complete: {total} underexposed items found")

if __name__ == "__main__":
    main()
