"""
Base client class for platform-specific API clients.
Handles common functionality like retries, rate limiting, and error handling.
"""
import time
import random
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from ratelimit import limits, sleep_and_retry
from loguru import logger
from config import config

@dataclass
class Stream:
    """Data class representing a live stream."""
    platform: str
    stream_id: str
    title: str
    url: str
    channel_name: str
    viewer_count: int = 0
    started_at: Optional[float] = None
    thumbnail_url: Optional[str] = None
    language: Optional[str] = None
    tags: List[str] = field(default_factory=list)

class BaseDiscoveryClient:
    """Base class for platform-specific discovery clients."""
    
    PLATFORM: str = "base"
    
    def __init__(self, **kwargs):
        """Initialize the base client with common settings."""
        self.max_retries = kwargs.get('max_retries', config.MAX_RETRIES)
        self.timeout = kwargs.get('timeout', config.REQUEST_TIMEOUT)
        self.max_pages = kwargs.get('max_pages', config.MAX_PAGES)
        
        # Rate limiting (calls per minute)
        self.calls_per_minute = kwargs.get('calls_per_minute', 60)
        self._last_request_time = 0
    
    @sleep_and_retry
    @limits(calls=60, period=60)  # 60 calls per minute by default
    def _make_request(self, url: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting and retries.
        
        Args:
            url: The URL to request
            params: Query parameters
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Parsed JSON response as a dictionary
        """
        import requests
        from requests.exceptions import RequestException
        
        headers = kwargs.pop('headers', {})
        timeout = kwargs.pop('timeout', self.timeout)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise
                
                # Exponential backoff with jitter
                backoff = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {backoff:.2f}s")
                time.sleep(backoff)
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 60.0 / self.calls_per_minute
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def fetch_live_streams(self, **kwargs) -> Tuple[List[Stream], Optional[str]]:
        """
        Fetch live streams from the platform.
        
        Args:
            **kwargs: Platform-specific parameters
            
        Returns:
            Tuple of (list of Stream objects, next page token/cursor)
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def fetch_all_pages(self, **kwargs) -> List[Stream]:
        """
        Fetch all available pages of live streams.
        
        Args:
            **kwargs: Platform-specific parameters
            
        Returns:
            List of all Stream objects
        """
        all_streams = []
        next_token = None
        pages_fetched = 0
        
        while pages_fetched < self.max_pages:
            try:
                streams, next_token = self.fetch_live_streams(
                    page_token=next_token,
                    **kwargs
                )
                all_streams.extend(streams)
                
                if not next_token or not streams:
                    break
                    
                pages_fetched += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {pages_fetched + 1}: {e}")
                break
        
        logger.info(f"Fetched {len(all_streams)} streams from {self.PLATFORM}")
        return all_streams
