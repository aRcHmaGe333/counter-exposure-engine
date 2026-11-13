# Counter-Exposure Engine

A system for discovering and surfacing underexposed live streams and content across multiple platforms, giving fair exposure to creators who haven't gained traction yet.

## 🎯 Mission

Surface content that algorithms miss - zero-viewer streams, new creators, and underexposed content that deserves a fair chance.

## ✨ Features

### Core Engine
- **Multi-platform Discovery**: YouTube and Twitch live stream detection
- **Fairness Scheduling**: Round-robin exposure based on underexposure scores
- **Exposure Tracking**: SQLite database prevents repeat exposure within 24h
- **Rate Limiting**: Built-in API rate limiting and retry logic
- **Real-time Scoring**: Dynamic scoring based on viewer count and stream freshness

### Reverse Discovery
- **Last-Page Strategy**: Starts from the least exposed search results
- **Content Filtering**: Removes spam and low-quality content
- **Multi-source**: Google search and YouTube live discovery
- **Quality Heuristics**: Filters for substantial, meaningful content

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Create configuration template
python run_engine.py --setup
```

### 2. Configure APIs
Edit the generated `.env` file with your API credentials:
```env
YOUTUBE_API_KEY=your_youtube_api_key_here
TWITCH_CLIENT_ID=your_twitch_client_id_here
TWITCH_OAUTH_TOKEN=your_twitch_oauth_token_here
```

### 3. Run Discovery
```bash
# Discover underexposed streams
python run_engine.py --mode streams --count 10

# Reverse discovery for content
python run_engine.py --mode reverse --count 10

# Combined discovery
python run_engine.py --mode combined --count 10
```

## 📊 Usage Examples

### Stream Discovery
```python
from exposure_engine import CounterExposureEngine

engine = CounterExposureEngine()
feed = engine.generate_exposure_feed(count=20)

for stream in feed:
    print(f"{stream['platform']}: {stream['title']}")
    print(f"Channel: {stream['channel_name']} | Viewers: {stream['viewer_count']}")
    print(f"Score: {stream['underexposure_score']}")
```

### Reverse Discovery
```python
from reverse_discovery import ReverseSearchDiscovery, ContentFilter

discovery = ReverseSearchDiscovery()
filter = ContentFilter()

results = discovery.discover_underexposed_content(["indie game", "new artist"])
filtered = filter.filter_results(results)

for result in filtered:
    print(f"{result.title} - {result.url}")
```

## 🏗️ Architecture

### Core Components
- **`exposure_engine.py`**: Main orchestration and fairness scheduling
- **`youtube_client.py`**: YouTube API integration with live stream discovery
- **`twitch_client.py`**: Twitch API integration with stream fetching
- **`base_client.py`**: Shared functionality for API clients
- **`reverse_discovery.py`**: Reverse search and content discovery
- **`config.py`**: Configuration management and environment setup

### Data Flow
1. **Discovery**: Fetch live streams from YouTube/Twitch APIs
2. **Filtering**: Remove already-exposed and high-viewer streams
3. **Scoring**: Calculate underexposure scores based on metrics
4. **Selection**: Round-robin selection for platform diversity
5. **Tracking**: Record exposures in SQLite database
6. **Output**: Generate structured feed for consumption

## 🔧 Configuration

### Environment Variables
```env
# API Keys
YOUTUBE_API_KEY=your_key
TWITCH_CLIENT_ID=your_id
TWITCH_OAUTH_TOKEN=your_token

# Engine Settings
YOUTUBE_MAX_RESULTS=50
TWITCH_MAX_RESULTS=100
LOG_LEVEL=INFO
REQUEST_TIMEOUT=10
MAX_RETRIES=3
MAX_PAGES=10
```

### Fairness Parameters
- **Max Viewer Threshold**: 5 viewers (configurable)
- **Freshness Window**: 30 minutes for new streams
- **Exposure Cooldown**: 24 hours between exposures
- **Platform Diversity**: Round-robin selection across platforms

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_youtube_client.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 📈 Monitoring

The engine provides built-in statistics and logging:

```python
engine = CounterExposureEngine()
stats = engine.get_stats()

print(f"Platforms enabled: {stats['platforms_enabled']}")
print(f"Exposure stats: {stats['exposure_stats']}")
```

## 🛡️ Rate Limiting & Ethics

- **Respectful API Usage**: Built-in rate limiting for all platforms
- **No Hosting**: Links to original content, doesn't rehost
- **Fair Exposure**: Algorithm-agnostic discovery based purely on underexposure
- **Transparency**: All exposure decisions are logged and auditable

## 🔮 Future Enhancements

- **Additional Platforms**: Kick, Trovo, Rumble integration
- **LLM Content Filtering**: Smart spam detection and quality assessment  
- **Web Interface**: Dashboard for browsing discovered content
- **API Endpoints**: RESTful API for integration with other services
- **Real-time Updates**: WebSocket feeds for live discovery updates

## 📝 License

This project is designed to promote fair exposure and support underrepresented creators across platforms.

## 🤝 Contributing

The engine is built with modularity in mind - new platform clients can be added by extending `BaseDiscoveryClient`.

---

**Built to give everyone a fair chance at exposure. 🎯**
## Support This Work

If this project is useful to you, consider supporting ongoing independent development.

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20this%20work-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/earthcraft)

Direct link: https://ko-fi.com/earthcraft

## Better implementations

The purpose of this project matters more than its current design. Its architecture and methods are examples of how to achieve that purpose, not permanent limits. A better approach can replace any part or all of the implementation when it produces a better result. Document new methods as they are developed; preserve the original publication history.

[Principle shared by all projects](https://github.com/aRcHmaGe333/aRcHmaGe333/blob/main/UNIVERSAL_IMPLEMENTATION_PRINCIPLES.md)
