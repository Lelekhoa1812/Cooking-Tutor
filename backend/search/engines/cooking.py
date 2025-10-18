import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import time

logger = logging.getLogger(__name__)

class CookingSearchEngine:
    """Specialized cooking search engine with curated sources"""
    
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = timeout
        
        # Curated cooking sources
        self.cooking_sources = {
            'allrecipes': {
                'base_url': 'https://www.allrecipes.com',
                'search_url': 'https://www.allrecipes.com/search',
                'domains': ['allrecipes.com']
            },
            'food_network': {
                'base_url': 'https://www.foodnetwork.com',
                'search_url': 'https://www.foodnetwork.com/search',
                'domains': ['foodnetwork.com']
            },
            'epicurious': {
                'base_url': 'https://www.epicurious.com',
                'search_url': 'https://www.epicurious.com/search',
                'domains': ['epicurious.com']
            },
            'serious_eats': {
                'base_url': 'https://www.seriouseats.com',
                'search_url': 'https://www.seriouseats.com/search',
                'domains': ['seriouseats.com']
            },
            'bon_appetit': {
                'base_url': 'https://www.bonappetit.com',
                'search_url': 'https://www.bonappetit.com/search',
                'domains': ['bonappetit.com']
            }
        }
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search cooking sources for relevant information"""
        results = []
        
        # Strategy 1: Direct cooking source searches
        for source_name, source_config in self.cooking_sources.items():
            if len(results) >= num_results:
                break
                
            source_results = self._search_cooking_source(query, source_name, source_config)
            results.extend(source_results)
            
            # Add delay between requests
            time.sleep(0.5)
        
        # Strategy 2: Cooking fallback sources
        if len(results) < num_results:
            fallback_results = self._get_fallback_sources(query, num_results - len(results))
            results.extend(fallback_results)
        
        return results[:num_results]
    
    def _search_cooking_source(self, query: str, source_name: str, source_config: Dict) -> List[Dict]:
        """Search a specific cooking source"""
        try:
            search_url = source_config.get('search_url')
            if not search_url:
                return []
            
            params = {
                'q': query,
                'query': query,
                'search': query
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Source-specific selectors
            selectors = self._get_source_selectors(source_name)
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    logger.info(f"{source_name} found {len(links)} results with selector: {selector}")
                    break
            
            for link in links[:3]:  # Limit per source
                try:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    # Make absolute URL
                    if href.startswith('/'):
                        href = source_config['base_url'] + href
                    
                    title = link.get_text(strip=True)
                    if title and href.startswith('http'):
                        results.append({
                            'url': href,
                            'title': title,
                            'source': source_name,
                            'domain': source_config['domains'][0]
                        })
                except Exception as e:
                    logger.debug(f"Error parsing {source_name} link: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Cooking source {source_name} search failed: {e}")
            return []
    
    def _get_source_selectors(self, source_name: str) -> List[str]:
        """Get CSS selectors for specific cooking sources"""
        selectors_map = {
            'allrecipes': [
                'a[href*="/recipe/"]',
                'a[href*="/recipes/"]',
                '.search-result a',
                '.result-title a'
            ],
            'food_network': [
                'a[href*="/recipes/"]',
                '.search-result a',
                '.result-title a',
                'a[href*="/recipe/"]'
            ],
            'epicurious': [
                'a[href*="/recipes/"]',
                '.search-result a',
                '.result-title a',
                'a[href*="/recipe/"]'
            ],
            'serious_eats': [
                'a[href*="/recipes/"]',
                '.search-result a',
                '.result-title a',
                'a[href*="/recipe/"]'
            ],
            'bon_appetit': [
                'a[href*="/recipes/"]',
                '.search-result a',
                '.result-title a',
                'a[href*="/recipe/"]'
            ]
        }
        return selectors_map.get(source_name, ['a[href*="http"]'])
    
    def _get_fallback_sources(self, query: str, num_results: int) -> List[Dict]:
        """Get fallback cooking sources when direct search fails"""
        fallback_sources = [
            {
                'url': 'https://www.allrecipes.com/recipes',
                'title': f'AllRecipes: {query}',
                'source': 'allrecipes_fallback',
                'domain': 'allrecipes.com'
            },
            {
                'url': 'https://www.foodnetwork.com/recipes',
                'title': f'Food Network: {query}',
                'source': 'foodnetwork_fallback',
                'domain': 'foodnetwork.com'
            },
            {
                'url': 'https://www.epicurious.com/recipes-menus',
                'title': f'Epicurious: {query}',
                'source': 'epicurious_fallback',
                'domain': 'epicurious.com'
            },
            {
                'url': 'https://www.seriouseats.com/recipes',
                'title': f'Serious Eats: {query}',
                'source': 'seriouseats_fallback',
                'domain': 'seriouseats.com'
            },
            {
                'url': 'https://www.bonappetit.com/recipes',
                'title': f'Bon Appétit: {query}',
                'source': 'bonappetit_fallback',
                'domain': 'bonappetit.com'
            }
        ]
        
        return fallback_sources[:num_results]
