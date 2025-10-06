"""
Twitch Live Stream Discovery Client.
Fetches live streams from Twitch's Helix API with proper rate limiting and error handling.
"""
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from loguru import logger
from base_client import BaseDiscoveryClient, Stream
from config import config

class TwitchDiscovery(BaseDiscoveryClient):
    """Client for discovering live streams on Twitch."""
    
    PLATFORM = "twitch"
    BASE_URL = "https://api.twitch.tv/helix"
    
    def __init__(self, client_id: str = None, oauth_token: str = None, **kwargs):
        """Initialize the Twitch discovery client.
        
        Args:
            client_id: Twitch API client ID
            oauth_token: Twitch OAuth token
            **kwargs: Additional arguments for BaseDiscoveryClient
        """
        super().__init__(**kwargs)
        self.client_id = client_id or config.TWITCH_CLIENT_ID
        self.oauth_token = oauth_token or config.TWITCH_OAUTH_TOKEN
        self.max_results = kwargs.get('max_results', 100)  # Max allowed by Twitch
        
        if not all([self.client_id, self.oauth_token]):
            logger.warning("Twitch credentials not fully configured. Twitch integration will be disabled.")
        
        self._headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }
    
    def _process_stream(self, item: Dict) -> Optional[Stream]:
        """Process a single stream item from the Twitch API response."""
        try:
            return Stream(
                platform=self.PLATFORM,
                stream_id=item['id'],
                title=item['title'],
                url=f"https://www.twitch.tv/{item['user_login']}",
                channel_name=item['user_name'],
                viewer_count=item['viewer_count'],
                started_at=self._parse_datetime(item['started_at']),
                thumbnail_url=item['thumbnail_url'].format(width=1920, height=1080) if item['thumbnail_url'] else None,
                language=item['language'],
                tags=item.get('tag_ids', [])
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Error processing Twitch stream: {e}")
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
    
    def _get_game_info(self, game_ids: List[str]) -> Dict[str, str]:
        """Get game information for the given game IDs."""
        if not game_ids:
            return {}
            
        try:
            params = [('id', game_id) for game_id in game_ids]
            data = self._make_request(
                f"{self.BASE_URL}/games",
                params=params,
                headers=self._headers
            )
            return {game['id']: game['name'] for game in data.get('data', [])}
        except Exception as e:
            logger.warning(f"Error fetching game info: {e}")
            return {}
    
    def fetch_live_streams(
        self,
        game_id: str = None,
        user_login: str = None,
        language: str = None,
        page_token: str = None,
        **kwargs
    ) -> Tuple[List[Stream], Optional[str]]:
        """
        Fetch currently live streams from Twitch.
        
        Args:
            game_id: Filter by game ID
            user_login: Filter by broadcaster login name
            language: Filter by language code (e.g., 'en', 'es')
            page_token: Cursor for pagination
            **kwargs: Additional parameters for the API
            
        Returns:
            Tuple of (list of Stream objects, next page cursor)
        """
        if not all([self.client_id, self.oauth_token]):
            logger.warning("Twitch credentials not configured")
            return [], None
        
        params = {
            'first': min(100, self.max_results),  # Max allowed by Twitch
            **kwargs
        }
        
        if game_id:
            params['game_id'] = game_id
        if user_login:
            params['user_login'] = user_login
        if language:
            params['language'] = language
        if page_token:
            params['after'] = page_token
        
        try:
            # First, get the streams
            data = self._make_request(
                f"{self.BASE_URL}/streams",
                params=params,
                headers=self._headers
            )
            
            streams = []
            for item in data.get('data', []):
                if stream := self._process_stream(item):
                    streams.append(stream)
            
            return streams, data.get('pagination', {}).get('cursor')
            
        except Exception as e:
            logger.error(f"Error fetching Twitch live streams: {e}")
            return [], None
    
    def search_channels(
        self,
        query: str,
        live_only: bool = True,
        **kwargs
    ) -> List[Stream]:
        """
        Search for channels matching a query.
        
        Args:
            query: Search query string
            live_only: Only return currently live channels
            **kwargs: Additional parameters for the API
            
        Returns:
            List of matching Stream objects
        """
        if not all([self.client_id, self.oauth_token]):
            logger.warning("Twitch credentials not configured")
            return []
        
        params = {
            'query': query,
            'first': min(100, self.max_results),
            **kwargs
        }
        
        try:
            # First, search for channels
            search_data = self._make_request(
                f"{self.BASE_URL}/search/channels",
                params=params,
                headers=self._headers
            )
            
            if not search_data.get('data'):
                return []
            
            # If we only want live channels, filter the results
            if live_only:
                user_logins = [channel['broadcaster_login'] for channel in search_data['data']]
                return self.fetch_live_streams(user_login=user_logins)[0]
            
            # Otherwise, return the channel search results
            return [
                Stream(
                    platform=self.PLATFORM,
                    stream_id=channel['id'],
                    title=channel['title'],
                    url=f"https://www.twitch.tv/{channel['broadcaster_login']}",
                    channel_name=channel['display_name'],
                    viewer_count=0,  # Not live, so 0 viewers
                    thumbnail_url=channel['thumbnail_url'],
                    language=channel['broadcaster_language']
                )
                for channel in search_data['data']
            ]
            
        except Exception as e:
            logger.error(f"Error searching Twitch channels: {e}")
            return []
