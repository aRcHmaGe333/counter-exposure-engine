"""
Configuration settings for the Counter-Exposure Engine.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Application configuration."""
    
    # YouTube API Settings
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    YOUTUBE_MAX_RESULTS = int(os.getenv('YOUTUBE_MAX_RESULTS', '50'))
    
    # Twitch API Settings
    TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', '')
    TWITCH_OAUTH_TOKEN = os.getenv('TWITCH_OAUTH_TOKEN', '')
    TWITCH_MAX_RESULTS = int(os.getenv('TWITCH_MAX_RESULTS', '50'))
    
    # Application Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    MAX_PAGES = int(os.getenv('MAX_PAGES', '10'))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.YOUTUBE_API_KEY:
            logger.warning("YouTube API key not set. YouTube integration will be disabled.")
        
        if not all([cls.TWITCH_CLIENT_ID, cls.TWITCH_OAUTH_TOKEN]):
            logger.warning("Twitch credentials not fully configured. Twitch integration will be disabled.")

# Initialize and validate config
config = Config()
config.validate()

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "counter_exposure_engine.log",
    rotation="10 MB",
    retention="7 days",
    level=config.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
)
