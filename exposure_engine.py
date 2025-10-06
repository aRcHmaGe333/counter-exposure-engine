"""
Counter-Exposure Engine - Main orchestration module
Discovers and surfaces underexposed live streams across platforms.
"""
import asyncio
import sqlite3
import time
import json
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from loguru import logger
import random

from youtube_client import YouTubeDiscovery
from twitch_client import TwitchDiscovery
from base_client import Stream
from config import config


@dataclass
class ExposureRecord:
    """Record of when a stream was exposed."""
    stream_id: str
    platform: str
    channel_name: str
    exposed_at: float
    score: float
    viewer_count: int


class ExposureTracker:
    """Tracks which streams have been exposed to prevent repeats."""
    
    def __init__(self, db_path: str = "exposure_tracker.db"):
        self.db_path = db_path
        self._init_database()
        self._exposed_today: Set[str] = set()
        self._load_today_exposures()
    
    def _init_database(self):
        """Initialize SQLite database for exposure tracking."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exposures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                exposed_at REAL NOT NULL,
                score REAL NOT NULL,
                viewer_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stream_platform ON exposures(stream_id, platform)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_exposed_at ON exposures(exposed_at)")
        conn.commit()
        conn.close()
    
    def _load_today_exposures(self):
        """Load today's exposures into memory for fast lookup."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT stream_id, platform FROM exposures WHERE exposed_at >= ?",
            (today_start,)
        )
        
        for stream_id, platform in cursor.fetchall():
            self._exposed_today.add(f"{platform}:{stream_id}")
        
        conn.close()
        logger.info(f"Loaded {len(self._exposed_today)} exposures from today")
    
    def is_exposed_today(self, stream: Stream) -> bool:
        """Check if stream was already exposed today."""
        key = f"{stream.platform}:{stream.stream_id}"
        return key in self._exposed_today
    
    def record_exposure(self, stream: Stream, score: float):
        """Record that a stream was exposed."""
        record = ExposureRecord(
            stream_id=stream.stream_id,
            platform=stream.platform,
            channel_name=stream.channel_name,
            exposed_at=time.time(),
            score=score,
            viewer_count=stream.viewer_count
        )
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO exposures 
            (stream_id, platform, channel_name, exposed_at, score, viewer_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.stream_id, record.platform, record.channel_name,
            record.exposed_at, record.score, record.viewer_count
        ))
        conn.commit()
        conn.close()
        
        # Update in-memory cache
        key = f"{stream.platform}:{stream.stream_id}"
        self._exposed_today.add(key)
        
        logger.info(f"Recorded exposure: {stream.platform}:{stream.channel_name}")
    
    def get_exposure_stats(self, days: int = 7) -> Dict:
        """Get exposure statistics for the last N days."""
        cutoff = time.time() - (days * 24 * 3600)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT platform, COUNT(*) as count, AVG(score) as avg_score, AVG(viewer_count) as avg_viewers
            FROM exposures 
            WHERE exposed_at >= ?
            GROUP BY platform
        """, (cutoff,))
        
        stats = {}
        for platform, count, avg_score, avg_viewers in cursor.fetchall():
            stats[platform] = {
                "count": count,
                "avg_score": round(avg_score, 2),
                "avg_viewers": round(avg_viewers, 1)
            }
        
        conn.close()
        return stats


class FairnessScheduler:
    """Ensures fair exposure across different categories and platforms."""
    
    def __init__(self, max_viewer_threshold: int = 5):
        self.max_viewer_threshold = max_viewer_threshold
        self.freshness_window_minutes = 30
    
    def calculate_underexposure_score(self, stream: Stream) -> float:
        """Calculate how underexposed a stream is (higher = more underexposed)."""
        if not stream.started_at:
            return 0.0
        
        # Base score inversely related to viewer count
        viewer_score = max(0, (self.max_viewer_threshold - stream.viewer_count) / self.max_viewer_threshold)
        
        # Freshness bonus (newer streams get higher priority)
        stream_age_minutes = (time.time() - stream.started_at) / 60
        freshness_score = max(0, (self.freshness_window_minutes - stream_age_minutes) / self.freshness_window_minutes)
        
        # Platform diversity bonus (slight preference for less common platforms)
        platform_bonus = 0.1 if stream.platform != "youtube" else 0.0
        
        # Combine scores
        total_score = (viewer_score * 0.6) + (freshness_score * 0.3) + platform_bonus
        
        return min(1.0, max(0.0, total_score))
    
    def filter_eligible_streams(self, streams: List[Stream], tracker: ExposureTracker) -> List[Tuple[Stream, float]]:
        """Filter streams that are eligible for exposure and calculate scores."""
        eligible = []
        
        for stream in streams:
            # Skip if already exposed today
            if tracker.is_exposed_today(stream):
                continue
            
            # Skip if too many viewers
            if stream.viewer_count > self.max_viewer_threshold:
                continue
            
            # Skip if too old
            if stream.started_at and (time.time() - stream.started_at) > (self.freshness_window_minutes * 60):
                continue
            
            score = self.calculate_underexposure_score(stream)
            if score > 0.1:  # Minimum threshold
                eligible.append((stream, score))
        
        return eligible
    
    def select_diverse_streams(self, scored_streams: List[Tuple[Stream, float]], count: int = 10) -> List[Tuple[Stream, float]]:
        """Select a diverse set of streams for exposure."""
        if not scored_streams:
            return []
        
        # Group by platform and language for diversity
        platform_groups = {}
        for stream, score in scored_streams:
            platform = stream.platform
            language = stream.language or "unknown"
            key = f"{platform}:{language}"
            
            if key not in platform_groups:
                platform_groups[key] = []
            platform_groups[key].append((stream, score))
        
        # Sort each group by score
        for key in platform_groups:
            platform_groups[key].sort(key=lambda x: x[1], reverse=True)
        
        # Round-robin selection for diversity
        selected = []
        group_keys = list(platform_groups.keys())
        random.shuffle(group_keys)  # Randomize order for fairness
        
        while len(selected) < count and any(platform_groups.values()):
            for key in group_keys:
                if platform_groups[key] and len(selected) < count:
                    selected.append(platform_groups[key].pop(0))
        
        return selected


class CounterExposureEngine:
    """Main engine for discovering and exposing underexposed streams."""
    
    def __init__(self):
        self.youtube_client = YouTubeDiscovery() if config.YOUTUBE_API_KEY else None
        self.twitch_client = TwitchDiscovery() if all([config.TWITCH_CLIENT_ID, config.TWITCH_OAUTH_TOKEN]) else None
        self.tracker = ExposureTracker()
        self.scheduler = FairnessScheduler()
        
        logger.info(f"Initialized engine - YouTube: {'✓' if self.youtube_client else '✗'}, Twitch: {'✓' if self.twitch_client else '✗'}")
    
    async def discover_streams(self) -> List[Stream]:
        """Discover live streams from all available platforms."""
        all_streams = []
        
        # Fetch from YouTube
        if self.youtube_client:
            try:
                yt_streams = self.youtube_client.fetch_all_pages(query="")
                all_streams.extend(yt_streams)
                logger.info(f"Discovered {len(yt_streams)} YouTube streams")
            except Exception as e:
                logger.error(f"YouTube discovery failed: {e}")
        
        # Fetch from Twitch
        if self.twitch_client:
            try:
                twitch_streams = self.twitch_client.fetch_all_pages()
                all_streams.extend(twitch_streams)
                logger.info(f"Discovered {len(twitch_streams)} Twitch streams")
            except Exception as e:
                logger.error(f"Twitch discovery failed: {e}")
        
        return all_streams
    
    def generate_exposure_feed(self, count: int = 20) -> List[Dict]:
        """Generate a feed of underexposed streams ready for exposure."""
        # Discover streams
        streams = asyncio.run(self.discover_streams())
        logger.info(f"Total streams discovered: {len(streams)}")
        
        # Filter and score eligible streams
        eligible = self.scheduler.filter_eligible_streams(streams, self.tracker)
        logger.info(f"Eligible underexposed streams: {len(eligible)}")
        
        if not eligible:
            logger.warning("No eligible streams found")
            return []
        
        # Select diverse streams for exposure
        selected = self.scheduler.select_diverse_streams(eligible, count)
        logger.info(f"Selected {len(selected)} streams for exposure")
        
        # Record exposures and format output
        exposure_feed = []
        for stream, score in selected:
            self.tracker.record_exposure(stream, score)
            
            exposure_feed.append({
                "platform": stream.platform,
                "stream_id": stream.stream_id,
                "title": stream.title,
                "url": stream.url,
                "channel_name": stream.channel_name,
                "viewer_count": stream.viewer_count,
                "started_at": stream.started_at,
                "thumbnail_url": stream.thumbnail_url,
                "language": stream.language,
                "tags": stream.tags,
                "underexposure_score": round(score, 3),
                "exposed_at": time.time()
            })
        
        return exposure_feed
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "platforms_enabled": {
                "youtube": self.youtube_client is not None,
                "twitch": self.twitch_client is not None
            },
            "exposure_stats": self.tracker.get_exposure_stats(),
            "scheduler_config": {
                "max_viewer_threshold": self.scheduler.max_viewer_threshold,
                "freshness_window_minutes": self.scheduler.freshness_window_minutes
            }
        }


if __name__ == "__main__":
    # Example usage
    engine = CounterExposureEngine()
    
    # Generate exposure feed
    feed = engine.generate_exposure_feed(count=10)
    
    print(f"\n🎯 Counter-Exposure Feed ({len(feed)} streams):")
    print("=" * 60)
    
    for item in feed:
        print(f"📺 {item['platform'].upper()}: {item['title'][:50]}...")
        print(f"   👤 {item['channel_name']} | 👀 {item['viewer_count']} viewers")
        print(f"   🔗 {item['url']}")
        print(f"   📊 Underexposure Score: {item['underexposure_score']}")
        print()
    
    # Show stats
    stats = engine.get_stats()
    print(f"\n📈 Engine Statistics:")
    print(json.dumps(stats, indent=2))
