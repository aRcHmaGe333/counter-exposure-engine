"""
Pytest configuration and fixtures for testing the Counter-Exposure Engine.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / 'test_data'
os.environ['LOG_LEVEL'] = 'DEBUG'

@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Create test data directory if it doesn't exist
    TEST_DATA_DIR.mkdir(exist_ok=True)
    
    # Set test environment variables
    os.environ['YOUTUBE_API_KEY'] = 'test_youtube_key'
    os.environ['TWITCH_CLIENT_ID'] = 'test_twitch_id'
    os.environ['TWITCH_OAUTH_TOKEN'] = 'test_oauth_token'
    os.environ['MAX_RETRIES'] = '1'
    os.environ['REQUEST_TIMEOUT'] = '5'
    
    yield
    
    # Cleanup if needed
    pass

@pytest.fixture
def mock_requests():
    """
    Mock the requests.get method for testing HTTP requests.
    
    Yields:
        A MagicMock object that replaces requests.get
    """
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def youtube_sample_response():
    """Sample YouTube API response for testing."""
    return {
        'items': [
            {
                'id': {'videoId': 'test_video_id_1'},
                'snippet': {
                    'title': 'Test Stream 1',
                    'channelTitle': 'Test Channel 1',
                    'publishedAt': '2023-01-01T12:00:00Z',
                    'thumbnails': {
                        'default': {'url': 'http://example.com/thumb1.jpg'}
                    }
                },
                'liveStreamingDetails': {
                    'concurrentViewers': '42',
                    'actualStartTime': '2023-01-01T12:00:00Z'
                }
            }
        ],
        'nextPageToken': 'test_next_page'
    }

@pytest.fixture
def twitch_sample_response():
    """Sample Twitch API response for testing."""
    return {
        'data': [
            {
                'id': '12345678',
                'user_id': '12345',
                'user_login': 'teststreamer',
                'user_name': 'TestStreamer',
                'game_id': '123',
                'game_name': 'Just Chatting',
                'title': 'Test Stream',
                'viewer_count': 10,
                'started_at': '2023-01-01T12:00:00Z',
                'language': 'en',
                'thumbnail_url': 'https://example.com/thumb.jpg',
                'tag_ids': ['123', '456']
            }
        ],
        'pagination': {
            'cursor': 'test_cursor'
        }
    }
