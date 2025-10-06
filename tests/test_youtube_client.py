"""
Tests for the YouTube client functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from youtube_client import YouTubeDiscovery

class TestYouTubeDiscovery:
    """Test cases for YouTubeDiscovery."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return YouTubeDiscovery(api_key="test_key")
    
    def test_init(self):
        """Test client initialization."""
        client = YouTubeDiscovery(api_key="test_key", max_results=30)
        assert client.api_key == "test_key"
        assert client.max_results == 30
        
        # Test with no API key
        client = YouTubeDiscovery()
        assert client.api_key is None
    
    def test_parse_datetime(self, client):
        """Test datetime parsing."""
        # Test with timezone
        dt_str = "2023-01-01T12:00:00Z"
        expected = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp()
        assert client._parse_datetime(dt_str) == expected
        
        # Test with timezone offset
        dt_str = "2023-01-01T12:00:00+02:00"
        expected = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).timestamp()
        assert client._parse_datetime(dt_str) == expected
        
        # Test with invalid datetime
        assert client._parse_datetime("invalid") is None
        assert client._parse_datetime("") is None
        assert client._parse_datetime(None) is None
    
    def test_get_thumbnail(self, client):
        """Test thumbnail URL selection."""
        thumbnails = {
            'default': {'url': 'http://example.com/default.jpg'},
            'medium': {'url': 'http://example.com/medium.jpg'},
            'high': {'url': 'http://example.com/high.jpg'},
            'maxres': {'url': 'http://example.com/maxres.jpg'}
        }
        
        # Should return highest resolution available
        assert client._get_thumbnail(thumbnails) == 'http://example.com/maxres.jpg'
        
        # Test with missing resolutions
        del thumbnails['maxres']
        assert client._get_thumbnail(thumbnails) == 'http://example.com/high.jpg'
        
        del thumbnails['high']
        assert client._get_thumbnail(thumbnails) == 'http://example.com/medium.jpg'
        
        del thumbnails['medium']
        assert client._get_thumbnail(thumbnails) == 'http://example.com/default.jpg'
        
        # Test with no thumbnails
        assert client._get_thumbnail({}) is None
    
    @patch.object(YouTubeDiscovery, '_make_request')
    def test_fetch_live_streams(self, mock_make_request, client):
        """Test fetching live streams."""
        # Setup mock response
        mock_response = {
            'items': [
                {
                    'id': {'videoId': 'test123'},
                    'snippet': {
                        'title': 'Test Stream',
                        'channelTitle': 'Test Channel',
                        'publishedAt': '2023-01-01T12:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'http://example.com/thumb.jpg'}
                        }
                    },
                    'liveStreamingDetails': {
                        'concurrentViewers': '42',
                        'actualStartTime': '2023-01-01T12:00:00Z'
                    }
                }
            ],
            'nextPageToken': 'test_token'
        }
        mock_make_request.return_value = mock_response
        
        # Call method
        streams, next_token = client.fetch_live_streams(query="gaming")
        
        # Verify
        assert len(streams) == 1
        assert streams[0].title == "Test Stream"
        assert streams[0].viewer_count == 42
        assert next_token == "test_token"
        
        # Verify API call
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        assert "search" in args[0]  # Should call search endpoint
        assert kwargs['params']['q'] == "gaming"
    
    @patch.object(YouTubeDiscovery, 'fetch_live_streams')
    def test_fetch_all_pages(self, mock_fetch, client):
        """Test fetching all pages of results."""
        # Setup mock to return 3 pages of results
        mock_fetch.side_effect = [
            (["page1"], "token1"),
            (["page2"], "token2"),
            (["page3"], None)  # Last page
        ]
        
        # Call method
        results = client.fetch_all_pages(query="gaming")
        
        # Verify
        assert len(results) == 3
        assert "page1" in results
        assert "page2" in results
        assert "page3" in results
        assert mock_fetch.call_count == 3
    
    @patch.object(YouTubeDiscovery, '_make_request')
    def test_api_error_handling(self, mock_make_request, client):
        """Test error handling for API requests."""
        # Setup mock to raise an exception
        mock_make_request.side_effect = Exception("API Error")
        
        # Call method and verify it handles the error
        streams, next_token = client.fetch_live_streams()
        assert streams == []
        assert next_token is None
