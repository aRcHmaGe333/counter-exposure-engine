"""
LLM-based content filtering for search result validation.
Uses local LLM to validate if content matches search intent.
"""
from typing import List, Dict, Optional
import json
from loguru import logger

class LLMContentValidator:
    """Validates search results using LLM reasoning."""
    
    def __init__(self, use_local: bool = True):
        """
        Initialize validator.
        
        Args:
            use_local: Use local LLM (Ollama) vs cloud API
        """
        self.use_local = use_local
        self.ollama_available = False
        
        if use_local:
            self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is available locally."""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            self.ollama_available = response.status_code == 200
            if self.ollama_available:
                logger.info("✓ Ollama detected - using local LLM for filtering")
            else:
                logger.warning("⚠ Ollama not available - using heuristic filtering")
        except:
            logger.warning("⚠ Ollama not available - using heuristic filtering")
    
    def validate_search_match(self, query: str, title: str, description: str = "") -> Dict:
        """
        Validate if content matches search intent.
        
        Args:
            query: Original search query (e.g., "tech tutorial")
            title: Video/content title
            description: Content description
            
        Returns:
            {
                "is_match": bool,
                "confidence": float,
                "reason": str,
                "method": "llm" | "heuristic"
            }
        """
        if self.ollama_available:
            return self._llm_validate(query, title, description)
        else:
            return self._heuristic_validate(query, title, description)
    
    def _llm_validate(self, query: str, title: str, description: str) -> Dict:
        """Use local LLM (Ollama) for validation."""
        import requests
        
        prompt = f"""Does this content match the search intent?

Search Query: "{query}"
Content Title: "{title}"
Description: "{description}"

Is this content relevant to someone searching for "{query}"?
Consider:
- "tech" tutorial ≠ "Texas Tech" sports
- "gaming" content ≠ casino gambling
- "music" tutorial ≠ music video

Answer ONLY with JSON:
{{
    "is_match": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}"""
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "llama3.2:latest",  # or whatever model is available
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = json.loads(result['response'])
                llm_response['method'] = 'llm'
                return llm_response
        except Exception as e:
            logger.warning(f"LLM validation failed: {e}, falling back to heuristics")
        
        # Fallback to heuristics
        return self._heuristic_validate(query, title, description)
    
    def _heuristic_validate(self, query: str, title: str, description: str) -> Dict:
        """Heuristic-based validation (no LLM needed)."""
        query_lower = query.lower()
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = f"{title_lower} {desc_lower}"
        
        # Known mismatches
        mismatches = {
            "tech": ["texas tech", "georgia tech", "virginia tech", "louisiana tech"],
            "gaming": ["gambling", "casino", "betting", "poker chips"],
            "music": ["music video only"],  # If query is "music tutorial" but it's just a music video
            "tutorial": ["live stream", "live game", "live match"],
            "vlog": ["live stream", "live game", "live match"]
        }
        
        # Check for mismatches
        for search_term, exclusions in mismatches.items():
            if search_term in query_lower:
                for exclusion in exclusions:
                    if exclusion in combined:
                        return {
                            "is_match": False,
                            "confidence": 0.9,
                            "reason": f"'{exclusion}' detected - likely mismatch for '{search_term}' search",
                            "method": "heuristic"
                        }
        
        # Check for tutorial/vlog + live mismatch
        tutorial_vlog_terms = ["tutorial", "vlog", "how to", "guide"]
        live_indicators = ["live stream", "live game", "live match", "live event", "streaming now"]
        
        if any(term in query_lower for term in tutorial_vlog_terms):
            if any(indicator in combined for indicator in live_indicators):
                # Exception: "live coding tutorial" is okay
                if "live coding" not in combined and "live tutorial" not in combined:
                    return {
                        "is_match": False,
                        "confidence": 0.85,
                        "reason": "Tutorial/guide query returned live stream content",
                        "method": "heuristic"
                    }
        
        # If no mismatches found, it's probably okay
        return {
            "is_match": True,
            "confidence": 0.7,
            "reason": "No obvious mismatches detected",
            "method": "heuristic"
        }
    
    def filter_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Filter a list of search results.
        
        Args:
            query: Original search query
            results: List of search results with 'title' and 'description' keys
            
        Returns:
            Filtered list with only matching results
        """
        filtered = []
        
        for result in results:
            validation = self.validate_search_match(
                query,
                result.get('title', ''),
                result.get('description', '') or result.get('snippet', '')
            )
            
            if validation['is_match']:
                result['validation'] = validation
                filtered.append(result)
            else:
                logger.debug(f"Filtered out: {result.get('title', 'Unknown')} - {validation['reason']}")
        
        return filtered


# Quick test
if __name__ == "__main__":
    validator = LLMContentValidator()
    
    test_cases = [
        {
            "query": "tech tutorial",
            "title": "Houston vs. Texas Tech LIVE 10/04/2025 | College Football",
            "expected": False
        },
        {
            "query": "tech tutorial",
            "title": "Python Tutorial for Beginners - Full Course",
            "expected": True
        },
        {
            "query": "gaming",
            "title": "Casino Gambling Tips and Tricks",
            "expected": False
        },
        {
            "query": "gaming",
            "title": "Minecraft Survival Let's Play Episode 1",
            "expected": True
        }
    ]
    
    print("\n🧪 Testing Content Validator:\n")
    for test in test_cases:
        result = validator.validate_search_match(test['query'], test['title'])
        status = "✅" if result['is_match'] == test['expected'] else "❌"
        print(f"{status} Query: '{test['query']}'")
        print(f"   Title: {test['title']}")
        print(f"   Match: {result['is_match']} (confidence: {result['confidence']}, method: {result['method']})")
        print(f"   Reason: {result['reason']}\n")
