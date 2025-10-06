"""
Tests for the base client functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

from base_client import BaseDiscoveryClient, Stream

class TestBaseDiscoveryClient:
    """Test cases for BaseDiscoveryClient."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return BaseDiscoveryClient()
    
    def test_stream_dataclass(self):
        """Test Stream dataclass initialization."""
        now = time.time()
        stream = Stream(
            platform="test",
            stream_id="123",
            title="Test Stream",
            url="http://example.com/stream",
            channel_name="Test Channel",
            viewer_count=10,
            started_at=now,
            thumbnail_url="http://example.com/thumb.jpg",
            language="en",
            tags=["gaming", "live"]
        )
        
        assert stream.platform == "test"
        assert stream.stream_id == "123"
        assert stream.title == "Test Stream"
        assert stream.viewer_count == 10
        assert stream.started_at == now
        assert "gaming" in stream.tags
    
    @patch('base_client.requests.get')
    def test_make_request_success(self, mock_get, client):
        """Test successful API request."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Make request
        result = client._make_request("http://example.com/api")
        
        # Verify
        assert result == {"key": "value"}
        mock_get.assert_called_once()
    
    @patch('base_client.requests.get')
    def test_make_request_retry(self, mock_get, client):
        """Test request with retry on failure."""
        # Setup mock to fail once then succeed
        client.max_retries = 2
        
        mock_response1 = MagicMock()
        mock_response1.raise_for_status.side_effect = Exception("Failed")
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"key": "value"}
        mock_response2.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        # Make request
        result = client._make_request("http://example.com/api")
        
        # Verify
        assert result == {"key": "value"}
        assert mock_get.call_count == 2
    
    @patch('base_client.requests.get')
    def test_make_request_max_retries_exceeded(self, mock_get, client):
        """Test request fails after max retries."""
        # Setup mock to always fail
        client.max_retries = 2
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Failed")
        mock_get.return_value = mock_response
        
        # Make request and verify exception
        with pytest.raises(Exception, match="Failed"):
            client._make_request("http://example.com/api")
        
        # Verify retries
        assert mock_get.call_count == 3  # Initial + 2 retries
    
    def test_enforce_rate_limit(self, client):
        """Test rate limiting between requests."""
        client.calls_per_minute = 60  # 1 call per second
        
        # First call - should not sleep
        start_time = time.time()
        client._enforce_rate_limit()
        first_call_time = time.time() - start_time
        
        # Second call - should sleep about 1 second
        start_time = time.time()
        client._enforce_rate_limit()
        second_call_time = time.time() - start_time
        
        # Verify timing
        assert first_call_time < 0.1  # Should be almost instant
        assert 0.9 < second_call_time < 1.1  # Should sleep about 1 second
    
    def test_fetch_all_pages(self, client):
        """Test pagination handling."""
        # Create a mock client with a simple fetch_live_streams implementation
        class MockClient(BaseDiscoveryClient):
            def __init__(self):
                super().__init__(max_pages=3)
                self.call_count = 0
            
            def fetch_live_streams(self, **kwargs):
                self.call_count += 1
                if self.call_count < 3:
                    return [f"stream_{self.call_count}"], f"page_{self.call_count}"
                return [f"stream_{self.call_count}"], None
        
        # Test
        client = MockClient()
        result = client.fetch_all_pages()
        
        # Verify
        assert len(result) == 3
        assert "stream_1" in result
        assert "stream_2" in result
        assert "stream_3" in result
        assert client.call_count == 3
