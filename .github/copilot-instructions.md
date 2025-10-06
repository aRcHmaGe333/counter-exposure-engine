# Counter-Exposure Engine - AI Coding Instructions

## Project Overview

This is a **fairness-driven content discovery engine** that surfaces underexposed streams and content across platforms (YouTube, Twitch). The core mission is algorithmic counter-exposure: finding creators with 0-5 viewers who deserve a fair chance.

## Architecture Patterns

### Three-Layer Discovery System
1. **Live Stream Discovery** (`youtube_client.py`, `twitch_client.py`) - Real-time platform APIs
2. **Reverse Search Discovery** (`reverse_discovery.py`) - "Last page" strategy to find buried content
3. **Fairness Orchestration** (`exposure_engine.py`) - Scoring, deduplication, and round-robin selection

### Core Data Flow
```
Platform APIs → Raw Streams → Eligibility Filter → Underexposure Scoring → Diversity Selection → SQLite Tracking → Exposure Feed
```

**Key Components:**
- `BaseDiscoveryClient`: Shared rate limiting, retries, pagination (inherit from this for new platforms)
- `ExposureTracker`: SQLite-based 24hr cooldown prevention with in-memory cache for today's exposures  
- `FairnessScheduler`: Calculates underexposure scores (viewer count + stream freshness + platform diversity)

## Critical Development Patterns

### 1. API Client Architecture
All platform clients **must** extend `BaseDiscoveryClient` for consistent rate limiting and error handling:

```python
class NewPlatformClient(BaseDiscoveryClient):
    PLATFORM = "platform_name"
    
    def fetch_live_streams(self, **kwargs) -> Tuple[List[Stream], Optional[str]]:
        # Return (streams, next_page_token)
```

### 2. Environment Configuration  
**Always check `config.py` first** - all settings load from `.env` with sensible defaults. Never hardcode API keys or limits.

**Setup workflow:**
```bash
python run_engine.py --setup  # Creates .env template
# Edit .env with real API keys
python run_engine.py --mode combined --count 10
```

### 3. Underexposure Scoring Logic
The fairness algorithm is in `FairnessScheduler.calculate_underexposure_score()`:
- **Viewer Score** (60%): Inverse of viewer count (max 5 viewers)
- **Freshness Score** (30%): Newer streams prioritized (30min window)  
- **Platform Bonus** (10%): Non-YouTube platforms get slight boost

### 4. Database Schema
`ExposureTracker` uses SQLite with **critical indexes**:
- `idx_stream_platform` for fast duplicate detection
- `idx_exposed_at` for time-based queries
- In-memory cache (`_exposed_today`) for performance

## Testing Strategy

### Mock External APIs Properly
All platform clients have comprehensive test coverage with mocked HTTP responses. **Pattern:**

```python
@patch.object(BaseDiscoveryClient, '_make_request')
def test_fetch_streams(self, mock_request, client):
    mock_request.return_value = {/* platform-specific response */}
    # Test logic, error handling, data transformation
```

### Test Commands
```bash
python -m pytest tests/ -v                    # All tests
python -m pytest tests/test_youtube_client.py # Specific platform
python -m pytest tests/ --cov=. --cov-report=html  # With coverage
```

## Entry Points & Workflows

### CLI Interface (`run_engine.py`)
- `--mode streams`: Live stream discovery only
- `--mode reverse`: Reverse search discovery only  
- `--mode combined`: Both strategies (default)
- `--setup`: Initialize .env configuration
- `--output results.json`: Save structured output

### Web UI (`simple_web_ui.py`)
Generates **static HTML** (no server) with auto-refresh. Runs full discovery and creates `counter_exposure_feed.html`.

### Engine Integration
```python
from exposure_engine import CounterExposureEngine
engine = CounterExposureEngine()
feed = engine.generate_exposure_feed(count=20)
# Returns structured list with underexposure_score, exposure tracking
```

## Key Dependencies & Rate Limiting

### External APIs
- **YouTube Data API v3**: Live stream search, video statistics (quota: 10,000/day)
- **Twitch Helix API**: Stream listing with OAuth (rate: 800/min)
- **Google Search**: Reverse discovery via HTML scraping (use delays: 1-3s)

### Rate Limiting Pattern
`BaseDiscoveryClient` uses `@sleep_and_retry` + `@limits` decorators. **Always** call `self._enforce_rate_limit()` before API requests.

## Reverse Discovery Strategy

**"Last Page" Philosophy**: Most algorithms surface popular content first. We start from page 100+ and work backwards to find buried gems.

**Implementation** (`ReverseSearchDiscovery`):
1. Find last available page via binary search
2. Extract results from final pages first
3. Filter spam/low-quality via `ContentFilter`
4. Prioritize by reverse rank (higher page = more underexposed)

## Extension Points

### Adding New Platforms
1. Create client extending `BaseDiscoveryClient`
2. Implement `fetch_live_streams()` returning `(List[Stream], next_token)`
3. Add credentials to `config.py`
4. Register in `CounterExposureEngine.__init__()`

### Custom Scoring Algorithms
Modify `FairnessScheduler.calculate_underexposure_score()` - current formula balances viewer count, freshness, and diversity.

### Quality Filters
Extend `ContentFilter` in `reverse_discovery.py` for platform-specific spam detection patterns.

## Debugging & Monitoring

### Logging Strategy
- **loguru** with file rotation (`counter_exposure_engine.log`)
- **Level control**: Set `LOG_LEVEL=DEBUG` in `.env`
- **Key events**: API calls, exposure records, filtering decisions

### Data Inspection
```python
# View exposure history
engine = CounterExposureEngine()
stats = engine.get_stats()  # Platform status, exposure counts

# Database queries
tracker = ExposureTracker()
recent_stats = tracker.get_exposure_stats(days=7)
```

### Common Issues
- **No results found**: Check API quotas, verify credentials in `.env`
- **Duplicate exposures**: Verify `ExposureTracker` database integrity
- **Rate limiting**: Adjust `calls_per_minute` in client constructor

## Ethical Guidelines

This system promotes **fair exposure** without content hosting:
- Links to original creators (no rehosting)
- 24hr cooldown prevents spam exposure
- Transparent scoring (all decisions logged)
- Respects platform rate limits
- Algorithm-agnostic discovery based purely on underexposure metrics

When extending functionality, maintain these principles: surface the unseen, respect creators' original platforms, and keep exposure decisions auditable.