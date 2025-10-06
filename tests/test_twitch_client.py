"""
Tests for the Twitch client functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from twitch_client import TwitchDiscovery

class TestTwitchDiscovery:
    """Test cases for TwitchDiscovery."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return TwitchDiscovery(
            client_id="test_client_id",
            oauth_token="test_oauth_token"
        )
    
    def test_init(self):
        """Test client initialization."""
        client = TwitchDiscovery(
            client_id="test_id",
            oauth_token="test_token",
            max_results=75
        )
        assert client.client_id == "test_id"
        assert client.oauth_token == "test_token"
        assert client.max_results == 75
        
        # Test with no credentials
        client = TwitchDiscovery()
        assert client.client_id is None
        assert client.oauth_token is None
    
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
    
    @patch.object(TwitchDiscovery, '_make_request')
    def test_fetch_live_streams(self, mock_make_request, client):
        """Test fetching live streams."""
        # Setup mock response
        mock_response = {
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
        mock_make_request.return_value = mock_response
        
        # Call method
        streams, next_cursor = client.fetch_live_streams(
            game_id="123",
            language="en"
        )
        
        # Verify
        assert len(streams) == 1
        assert streams[0].title == "Test Stream"
        assert streams[0].viewer_count == 10
        assert next_cursor == "test_cursor"
        
        # Verify API call
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        assert "streams" in args[0]  # Should call streams endpoint
        assert kwargs['params']['game_id'] == "123"
        assert kwargs['headers']['Client-ID'] == "test_client_id"
    
    @patch.object(TwitchDiscovery, '_make_request')
    def test_search_channels(self, mock_make_request, client):
        """Test searching for channels."""
        # Setup mock response
        mock_response = {
            'data': [
                {
                    'id': '12345',
                    'broadcaster_login': 'teststreamer',
                    'display_name': 'TestStreamer',
                    'title': 'Test Channel',
                    'broadcaster_language': 'en',
                    'thumbnail_url': 'https://example.com/thumb.jpg'
                }
            ]
        }
        mock_make_request.return_value = mock_response
        
        # Call method
        results = client.search_channels("test")
        
        # Verify
        assert len(results) == 1
        assert results[0].channel_name == "TestStreamer"
        assert results[0].url == "https://www.twitch.tv/teststreamer"
        
        # Verify API call
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        assert "search/channels" in args[0]
        assert kwargs['params']['query'] == "test"
    
    @patch.object(TwitchDiscovery, '_make_request')
    def test_get_game_info(self, mock_make_request, client):
        """Test getting game information."""
        # Setup mock response
        mock_response = {
            'data': [
                {'id': '123', 'name': 'Test Game'},
                {'id': '456', 'name': 'Another Game'}
            ]
        }
        mock_make_request.return_value = mock_response
        
        # Call method
        game_info = client._get_game_info(['123', '456'])
        
        # Verify
        assert game_info == {
            '123': 'Test Game',
            '456': 'Another Game'
        }
        
        # Verify API call
        mock_make_request.assert_called_once()

    @patch.object(TwitchDiscovery, '_make_request')
    def test_api_error_handling(self, mock_make_request, client):
        """Test error handling for API requests."""
        # Setup mock to raise an exception
        mock_make_request.side_effect = Exception("API Error")

        # Call method and verify it handles the error
        streams, next_cursor = client.fetch_live_streams()
        assert streams == []
        assert next_cursor is None
        args, kwargs = mock_make_request.call_args
        assert "games" in args[0]
        assert ('id', '123') in kwargs['params']
        assert ('id', '456') in kwargs['params']
