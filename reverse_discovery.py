"""
Reverse Discovery Module - Implements "jump to last page" strategy
Discovers content by starting from the least exposed pages and working backwards.
"""
import requests
import time
import random
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from loguru import logger
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Represents a search result from reverse discovery."""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: Optional[float] = None
    rank: Optional[int] = None

class ReverseSearchDiscovery:
    """Discovers underexposed content by reverse-paginating search results."""

    def __init__(self, max_retries: int = 3, delay_range: Tuple[float, float] = (1.0, 3.0)):
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _random_delay(self):
        """Add random delay to avoid being blocked."""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Make HTTP request with retries and error handling."""
        for attempt in range(self.max_retries + 1):
            try:
                self._random_delay()
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
        return None

    def find_last_page_google(self, query: str, site: str = None) -> int:
        """Find the last available page for a Google search."""
        search_params = {'q': query}
        if site:
            search_params['q'] += f' site:{site}'

        # Try increasingly large page numbers to find the limit
        test_pages = [100, 200, 500, 1000]
        last_valid_page = 1

        for page_num in test_pages:
            search_params['start'] = (page_num - 1) * 10

            response = self._make_request('https://www.google.com/search', search_params)
            if not response:
                break

            # Check if page has results
            if 'did not match any documents' in response.text or 'No results found' in response.text:
                break

            # Check for "Next" button or pagination indicators
            if 'Next' in response.text or f'start={page_num * 10}' in response.text:
                last_valid_page = page_num
            else:
                break

        logger.info(f"Found last page for query '{query}': {last_valid_page}")
        return last_valid_page

    def reverse_search_google(self, query: str, site: str = None, max_pages: int = 10) -> List[SearchResult]:
        """Search Google starting from the last page and working backwards."""
        results = []

        # Find the last available page
        last_page = self.find_last_page_google(query, site)
        start_page = min(last_page, max_pages)

        logger.info(f"Starting reverse search from page {start_page}")

        for page_num in range(start_page, 0, -1):
            search_params = {'q': query}
            if site:
                search_params['q'] += f' site:{site}'
            search_params['start'] = (page_num - 1) * 10

            response = self._make_request('https://www.google.com/search', search_params)
            if not response:
                continue

            # Parse results from this page
            page_results = self._parse_google_results(response.text, page_num)
            results.extend(page_results)

            logger.info(f"Extracted {len(page_results)} results from page {page_num}")

        return results

    def _parse_google_results(self, html: str, page_num: int) -> List[SearchResult]:
        """Parse search results from Google HTML (basic extraction)."""
        results = []

        # This is a simplified parser - in production you'd want something more robust
        # like BeautifulSoup or a proper HTML parser

        # Look for result divs (this is fragile and may need updates)
        import re

        # Pattern to match Google result blocks
        result_pattern = r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</h3>.*?<span[^>]*>(.*?)</span>'
        matches = re.findall(result_pattern, html, re.DOTALL | re.IGNORECASE)

        for i, (url, title, snippet) in enumerate(matches):
            # Clean up extracted text
            title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()

            # Skip Google's own URLs
            if 'google.com' in url:
                continue

            results.append(SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                source="google",
                timestamp=time.time(),
                rank=(page_num - 1) * 10 + i + 1
            ))

        return results

    def reverse_search_youtube_live(self, query: str = "", max_pages: int = 5) -> List[SearchResult]:
        """Search for live YouTube streams starting from less popular results."""
        results = []

        # YouTube search with live filter
        base_url = "https://www.youtube.com/results"

        for page in range(max_pages, 0, -1):
            params = {
                'search_query': query,
                'sp': 'EgJAAQ%253D%253D',  # Live filter
                'p': page
            }

            response = self._make_request(base_url, params)
            if not response:
                continue

            # Parse YouTube results (simplified)
            page_results = self._parse_youtube_results(response.text, page)
            results.extend(page_results)

            logger.info(f"Extracted {len(page_results)} YouTube live results from page {page}")

        return results

    def _parse_youtube_results(self, html: str, page_num: int) -> List[SearchResult]:
        """Parse YouTube search results (basic extraction)."""
        results = []

        # This would need a more sophisticated parser in production
        import re

        # Look for video data in YouTube's JSON
        video_pattern = r'"videoId":"([^"]*)".*?"title":{"runs":\[{"text":"([^"]*)"}.*?"viewCountText":{"simpleText":"([^"]*)"}'
        matches = re.findall(video_pattern, html, re.DOTALL)

        for i, (video_id, title, view_count) in enumerate(matches):
            url = f"https://www.youtube.com/watch?v={video_id}"

            results.append(SearchResult(
                title=title,
                url=url,
                snippet=f"Views: {view_count}",
                source="youtube_live",
                timestamp=time.time(),
                rank=(page_num - 1) * 20 + i + 1
            ))

        return results

    def discover_underexposed_content(self, queries: List[str], platforms: List[str] = None) -> List[SearchResult]:
        """Discover underexposed content across multiple queries and platforms."""
        if platforms is None:
            platforms = ["google", "youtube_live"]

        all_results = []

        for query in queries:
            logger.info(f"Processing query: '{query}'")

            if "google" in platforms:
                google_results = self.reverse_search_google(query, max_pages=5)
                all_results.extend(google_results)

            if "youtube_live" in platforms:
                youtube_results = self.reverse_search_youtube_live(query, max_pages=3)
                all_results.extend(youtube_results)

        # Sort by rank (higher rank = less exposed, but filter out popular content first)
        # Remove results that are clearly popular (based on view count in snippet)
        filtered_results = []
        for result in all_results:
            # Extract view count from snippet if available
            import re
            view_match = re.search(r'(\d+(?:,\d+)*)\s*(?:views?|visningar)', result.snippet, re.IGNORECASE)
            if view_match:
                view_count = int(view_match.group(1).replace(',', ''))
                # Only keep truly underexposed content (< 10,000 views)
                if view_count < 10000:
                    filtered_results.append(result)
            else:
                # If no view count found, assume it might be underexposed
                filtered_results.append(result)

        # Sort by rank (higher rank = less exposed)
        filtered_results.sort(key=lambda x: x.rank or 0, reverse=True)

        logger.info(f"Total underexposed content discovered: {len(filtered_results)} (filtered from {len(all_results)} total)")
        return filtered_results


class ContentFilter:
    """Filters discovered content to remove spam and low-quality results."""

    def __init__(self):
        self.spam_domains = {
            'spam-site.com', 'fake-news.net', 'clickbait.org'
        }
        self.spam_keywords = {
            'click here', 'free money', 'you won', 'congratulations',
            'limited time', 'act now', 'exclusive offer'
        }

    def is_spam(self, result: SearchResult) -> bool:
        """Check if a result appears to be spam."""
        # Check domain
        try:
            domain = urlparse(result.url).netloc.lower()
            if domain in self.spam_domains:
                return True
        except:
            pass

        # Check title and snippet for spam keywords
        text = (result.title + " " + result.snippet).lower()
        for keyword in self.spam_keywords:
            if keyword in text:
                return True

        return False

    def is_substantial(self, result: SearchResult) -> bool:
        """Check if a result has substantial content."""
        # Basic checks for content quality
        if len(result.title) < 10:
            return False

        if len(result.snippet) < 20:
            return False

        # Check for meaningful words
        meaningful_words = len([w for w in result.title.split() if len(w) > 3])
        if meaningful_words < 2:
            return False

        return True

    def filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter results to remove spam and low-quality content."""
        filtered = []

        for result in results:
            if self.is_spam(result):
                logger.debug(f"Filtered spam: {result.title}")
                continue

            if not self.is_substantial(result):
                logger.debug(f"Filtered low-quality: {result.title}")
                continue

            filtered.append(result)

        logger.info(f"Filtered {len(results) - len(filtered)} results, {len(filtered)} remaining")
        return filtered


if __name__ == "__main__":
    # Example usage
    discovery = ReverseSearchDiscovery()
    content_filter = ContentFilter()

    # Discover underexposed content
    queries = ["new indie game", "small streamer", "unknown artist"]
    results = discovery.discover_underexposed_content(queries)

    # Filter results
    filtered_results = content_filter.filter_results(results)

    print(f"\n🔍 Reverse Discovery Results ({len(filtered_results)} items):")
    print("=" * 60)

    for result in filtered_results[:10]:  # Show top 10
        print(f"📄 {result.title}")
        print(f"   🔗 {result.url}")
        print(f"   📝 {result.snippet[:100]}...")
        print(f"   📊 Rank: {result.rank} | Source: {result.source}")
        print()