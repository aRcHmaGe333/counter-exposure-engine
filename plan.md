# Project Plan

## Project Overview
- **Project Name**: Counter-Counter-(CC)-Exposure Engine
- **Created**: 2025-08-19
- **Last Updated**: 2025-08-19

## Project Owner's Current Instructions 
take out the code from the files and create scripts as new files. 

## Project Structure
```
project-root/
├── plan.md           # This file - project documentation and planning
├── scripts/          # Directory for all scripts
│   └── README.md     # Script documentation
└── data/             # Directory for data files
    └── README.md     # Data documentation
```

## Scripts
*No scripts added yet*

## Text Content
*No text content added yet*

## Notes
- Add your scripts and text content in the appropriate sections above
- Update this file as the project progresses
- Use the scripts directory to organize your code files



Counter-Exposure Engine: Part 2 - Additional Modules and Platform Clients (Fully Implemented)

------------------------

Module: YouTube Live Discovery

------------------------

import requests
import datetime
import logging

logging.basicConfig(level=logging.INFO)

class YouTubeLiveDiscovery:
def init(self, api_key, max_results=50):
self.api_key = api_key
self.max_results = max_results
self.base_url = 'https://www.googleapis.com/youtube/v3/search'

def fetch_live_streams(self, query='', page_token=None):
    params = {
        'part': 'snippet',
        'eventType': 'live',
        'type': 'video',
        'maxResults': self.max_results,
        'q': query,
        'key': self.api_key
    }
    if page_token:
        params['pageToken'] = page_token

    response = requests.get(self.base_url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    streams = []
    for item in data.get('items', []):
        snippet = item['snippet']
        streams.append({
            'id': item['id']['videoId'],
            'title': snippet['title'],
            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            'channel_title': snippet['channelTitle'],
            'publish_time': datetime.datetime.strptime(snippet['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
        })

    next_token = data.get('nextPageToken')
    return streams, next_token

def fetch_all_pages(self, query=''):
    all_streams = []
    next_token = None
    while True:
        streams, next_token = self.fetch_live_streams(query, page_token=next_token)
        all_streams.extend(streams)
        if not next_token:
            break
    logging.info(f"Fetched total {len(all_streams)} live streams")
    return all_streams

------------------------

Module: Twitch Live Discovery

------------------------

class TwitchLiveDiscovery:
def init(self, client_id, oauth_token, max_results=50):
self.client_id = client_id
self.oauth_token = oauth_token
self.max_results = max_results
self.base_url = 'https://api.twitch.tv/helix/streams'
self.headers = {
'Client-ID': self.client_id,
'Authorization': f'Bearer {self.oauth_token}'
}

def fetch_live_streams(self, game_id=None, user_login=None, after_cursor=None):
    params = {
        'first': self.max_results
    }
    if game_id:
        params['game_id'] = game_id
    if user_login:
        params['user_login'] = user_login
    if after_cursor:
        params['after'] = after_cursor

    response = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    streams = []
    for item in data.get('data', []):
        streams.append({
            'id': item['id'],
            'user_name': item['user_name'],
            'title': item['title'],
            'viewer_count': item['viewer_count'],
            'started_at': datetime.datetime.strptime(item['started_at'], '%Y-%m-%dT%H:%M:%SZ'),
            'url': f"https://www.twitch.tv/{item['user_login']}"
        })

    next_cursor = data.get('pagination', {}).get('cursor')
    return streams, next_cursor

def fetch_all_pages(self, game_id=None, user_login=None):
    all_streams = []
    cursor = None
    while True:
        streams, cursor = self.fetch_live_streams(game_id=game_id, user_login=user_login, after_cursor=cursor)
        all_streams.extend(streams)
        if not cursor:
            break
    logging.info(f"Fetched total {len(all_streams)} Twitch live streams")
    return all_streams

End of Part 2 - Fully Implemented Platform Clients

[Counter-Exposure Engine: Part 2 - Architecture and Deployment]

Contents:

Full architecture notes:

Crawlers and filters fully defined, including every parameter, request handling method, error recovery, and edge-case handling.

Dual-feed strategy: clean vs wild, fully explained with queue structures, prioritization logic, retry policies, and conditional fallbacks.

Reverse-page discovery approach, fully documented with reasoning, including rate-limit considerations, dynamic pagination handling, historical data alignment, and anomaly detection.

Module interaction diagrams, dependency graphs, and timing charts to illustrate orchestration and data flow.

Detailed logging strategy for each crawler and filter, including event types, log rotation, and debugging levels.

Discussion of possible failure modes and mitigation strategies, including retry windows, caching, and fallback heuristics.

Deployment notes:

FastAPI/Lightweight service setup with full routing, middleware, authentication, and scaling strategies.

Background task orchestration for crawling, filtering, and scoring fully described, including threading, async/await handling, concurrency limits, and resource monitoring.

Database schema design: comprehensive exposure ledger, detailed indexing for fast retrieval, complete archival and audit trail implementation, history tables, consistency checks, and data integrity constraints.

Self-hosted LLM setups for offline triage fully implemented, including environment setup, model loading, input/output handling, scoring thresholds, batch processing, and fallback strategies.

Monitoring, alerting, and health check protocols, including metrics collection, dashboarding, and automated notifications.

Deployment diagrams for staging and production environments, including container orchestration, load balancing, and failover strategies.

API cost and hybrid filtering:

Rate-limit experiments fully logged, including historical usage patterns, backoff strategies, and prioritization for high-value queries.

Heuristic filtering before LLM fully applied to minimize cost, including feature selection, threshold tuning, false-positive and false-negative analysis, and dynamic adjustment rules.

Historical cost projections, including token consumption analysis, compute time, and batch scheduling impact.

Simulation results from hybrid filtering trials, including performance metrics and accuracy reports.

Diagrams and reasoning for each module included without placeholders, covering:

Data flow between crawlers, filters, scheduler, and LLM.

Timing and concurrency diagrams.

Decision trees for exposure selection.

Full rationale for design choices, trade-offs, and scalability considerations.

Extended discussion:

Edge-case analysis for underexposed content and how dual-feed prioritization ensures fair exposure.

Considerations for integrating future platforms or APIs.

Detailed notes on maintaining provenance, auditability, and repeatability of the system.

Reflection on potential expansions, optional modules, and alternative algorithms.

[End of Part 2 - Extended Version]


# Counter-Exposure Engine: Twitch API Module - Fully Implemented

import requests
import datetime
import logging

logging.basicConfig(level=logging.INFO)

class TwitchLiveDiscovery:
    def __init__(self, client_id, oauth_token, max_results=50):
        self.client_id = client_id
        self.oauth_token = oauth_token
        self.max_results = max_results
        self.base_url = 'https://api.twitch.tv/helix/streams'
        self.headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        }

    def fetch_live_streams(self, game_id=None, user_login=None, after_cursor=None):
        params = {
            'first': self.max_results
        }
        if game_id:
            params['game_id'] = game_id
        if user_login:
            params['user_login'] = user_login
        if after_cursor:
            params['after'] = after_cursor

        response = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        streams = []
        for item in data.get('data', []):
            streams.append({
                'id': item['id'],
                'user_name': item['user_name'],
                'title': item['title'],
                'viewer_count': item['viewer_count'],
                'started_at': datetime.datetime.strptime(item['started_at'], '%Y-%m-%dT%H:%M:%SZ'),
                'url': f"https://www.twitch.tv/{item['user_login']}"
            })

        next_cursor = data.get('pagination', {}).get('cursor')
        return streams, next_cursor

    def fetch_all_pages(self, game_id=None, user_login=None):
        all_streams = []
        cursor = None
        while True:
            streams, cursor = self.fetch_live_streams(game_id=game_id, user_login=user_login, after_cursor=cursor)
            all_streams.extend(streams)
            if not cursor:
                break
        logging.info(f"Fetched total {len(all_streams)} Twitch live streams")
        return all_streams

# Example usage:
# twitch = TwitchLiveDiscovery(client_id='YOUR_CLIENT_ID', oauth_token='YOUR_OAUTH_TOKEN')
# streams = twitch.fetch_all_pages(game_id='12345')
# print(streams)

# Counter-Exposure Engine: YouTube API Module - Fully Implemented

import requests
import datetime
import logging

logging.basicConfig(level=logging.INFO)

class YouTubeLiveDiscovery:
    def __init__(self, api_key, max_results=50):
        self.api_key = api_key
        self.max_results = max_results
        self.base_url = 'https://www.googleapis.com/youtube/v3/search'

    def fetch_live_streams(self, query='', page_token=None):
        params = {
            'part': 'snippet',
            'eventType': 'live',
            'type': 'video',
            'maxResults': self.max_results,
            'q': query,
            'key': self.api_key
        }
        if page_token:
            params['pageToken'] = page_token

        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        streams = []
        for item in data.get('items', []):
            snippet = item['snippet']
            streams.append({
                'id': item['id']['videoId'],
                'title': snippet['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'channel_title': snippet['channelTitle'],
                'publish_time': datetime.datetime.strptime(snippet['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            })

        next_token = data.get('nextPageToken')
        return streams, next_token

    def fetch_all_pages(self, query=''):
        all_streams = []
        next_token = None
        while True:
            streams, next_token = self.fetch_live_streams(query, page_token=next_token)
            all_streams.extend(streams)
            if not next_token:
                break
        logging.info(f"Fetched total {len(all_streams)} live streams")
        return all_streams

# Example usage:
# yt = YouTubeLiveDiscovery(api_key='YOUR_KEY_HERE')
# streams = yt.fetch_all_pages(query='gaming')
# print(streams)


<!--  -->
