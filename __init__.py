"""
Counter-Exposure Engine

A system for discovering and surfacing underexposed live streams
across multiple platforms.
"""

__version__ = "0.1.0"

from config import config
from youtube_client import YouTubeDiscovery
from twitch_client import TwitchDiscovery

__all__ = [
    'config',
    'YouTubeDiscovery',
    'TwitchDiscovery'
]
