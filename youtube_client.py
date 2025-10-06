"""
YouTube Live Stream Discovery Client.
Fetches live streams from YouTube's API with proper rate limiting and error handling.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from base_client import BaseDiscoveryClient, Stream
from config import config

class YouTubeDiscovery(BaseDiscoveryClient):
    """Client for discovering live streams on YouTube."""
    
    PLATFORM = "youtube"
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None, **kwargs):
        """Initialize the YouTube discovery client.
        
        Args:
            api_key: YouTube Data API v3 key
            **kwargs: Additional arguments for BaseDiscoveryClient
        """
        super().__init__(**kwargs)
        self.api_key = api_key or config.YOUTUBE_API_KEY
        self.max_results = kwargs.get('max_results', config.YOUTUBE_MAX_RESULTS)
        
        if not self.api_key:
            logger.warning("No YouTube API key provided. YouTube integration will be disabled.")
    
    def _process_stream(self, item: Dict) -> Optional[Stream]:
        """Process a single stream item from the YouTube API response."""
        try:
            snippet = item['snippet']
            video_id = item['id']['videoId']
            
            # Get live streaming details if available
            live_details = item.get('liveStreamingDetails', {})
            
            return Stream(
                platform=self.PLATFORM,
                stream_id=video_id,
                title=snippet.get('title', 'Untitled Stream'),
                url=f"https://www.youtube.com/watch?v={video_id}",
                channel_name=snippet.get('channelTitle', 'Unknown Channel'),
                viewer_count=int(live_details.get('concurrentViewers', 0)),
                started_at=self._parse_datetime(live_details.get('actualStartTime') or snippet['publishedAt']),
                thumbnail_url=self._get_thumbnail(snippet.get('thumbnails', {})),
                language=snippet.get('defaultAudioLanguage'),
                tags=snippet.get('tags', [])
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing YouTube stream: {e}")
            return None
    
    @staticmethod
    def _parse_datetime(dt_str: str) -> float:
        """Parse ISO 8601 datetime string to timestamp."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00')).timestamp()
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _get_thumbnail(thumbnails: Dict) -> Optional[str]:
        """Get the highest resolution thumbnail URL."""
        for res in ['maxres', 'high', 'medium', 'default']:
            if res in thumbnails and 'url' in thumbnails[res]:
                return thumbnails[res]['url']
        return None
    
    def fetch_live_streams(self, query: str = '', page_token: str = None, **kwargs) -> Tuple[List[Stream], Optional[str]]:
        """
        Fetch currently live streams from YouTube.
        
        Args:
            query: Search query string
            page_token: Token for pagination
            **kwargs: Additional parameters for the API
            
        Returns:
            Tuple of (list of Stream objects, next page token)
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured")
            return [], None
        
        params = {
            'part': 'snippet,liveStreamingDetails',
            'eventType': 'live',
            'type': 'video',
            'maxResults': min(50, self.max_results),  # Max allowed by YouTube
            'q': query,
            'key': self.api_key,
            **kwargs
        }
        
        if page_token:
            params['pageToken'] = page_token
        
        try:
            data = self._make_request(
                f"{self.BASE_URL}/search",
                params=params
            )
            
            streams = []
            for item in data.get('items', []):
                if stream := self._process_stream(item):
                    streams.append(stream)
            
            return streams, data.get('nextPageToken')
            
        except Exception as e:
            logger.error(f"Error fetching YouTube live streams: {e}")
            return [], None
