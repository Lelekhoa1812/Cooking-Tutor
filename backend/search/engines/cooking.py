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
        
        # Comprehensive cooking sources with enhanced search strategies
        self.cooking_sources = {
            'allrecipes': {
                'base_url': 'https://www.allrecipes.com',
                'search_url': 'https://www.allrecipes.com/search',
                'domains': ['allrecipes.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 1
            },
            'food_network': {
                'base_url': 'https://www.foodnetwork.com',
                'search_url': 'https://www.foodnetwork.com/search',
                'domains': ['foodnetwork.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 1
            },
            'epicurious': {
                'base_url': 'https://www.epicurious.com',
                'search_url': 'https://www.epicurious.com/search',
                'domains': ['epicurious.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 1
            },
            'serious_eats': {
                'base_url': 'https://www.seriouseats.com',
                'search_url': 'https://www.seriouseats.com/search',
                'domains': ['seriouseats.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 1
            },
            'bon_appetit': {
                'base_url': 'https://www.bonappetit.com',
                'search_url': 'https://www.bonappetit.com/search',
                'domains': ['bonappetit.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 1
            },
            'taste_of_home': {
                'base_url': 'https://www.tasteofhome.com',
                'search_url': 'https://www.tasteofhome.com/search',
                'domains': ['tasteofhome.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 2
            },
            'food_com': {
                'base_url': 'https://www.food.com',
                'search_url': 'https://www.food.com/search',
                'domains': ['food.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 2
            },
            'bbc_good_food': {
                'base_url': 'https://www.bbcgoodfood.com',
                'search_url': 'https://www.bbcgoodfood.com/search',
                'domains': ['bbcgoodfood.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 2
            },
            'martha_stewart': {
                'base_url': 'https://www.marthastewart.com',
                'search_url': 'https://www.marthastewart.com/search',
                'domains': ['marthastewart.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 2
            },
            'king_arthur_baking': {
                'base_url': 'https://www.kingarthurbaking.com',
                'search_url': 'https://www.kingarthurbaking.com/search',
                'domains': ['kingarthurbaking.com'],
                'search_params': ['q', 'query', 'search'],
                'priority': 2
            }
        }
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search cooking sources for relevant information with enhanced strategies"""
        results = []
        
        # Enhanced query processing
        enhanced_queries = self._create_enhanced_queries(query)
        logger.info(f"Enhanced queries for cooking search: {enhanced_queries}")
        
        # Strategy 1: Priority-based source searches
        priority_sources = self._get_priority_sources()
        
        for priority_level in [1, 2]:  # Search priority 1 sources first, then priority 2
            if len(results) >= num_results:
                break
                
            for source_name in priority_sources.get(priority_level, []):
                if len(results) >= num_results:
                    break
                    
                source_config = self.cooking_sources[source_name]
                
                # Try multiple query variations for each source
                for query_variant in enhanced_queries:
                    if len(results) >= num_results:
                        break
                        
                    source_results = self._search_cooking_source(query_variant, source_name, source_config)
                    if source_results:
                        results.extend(source_results)
                        logger.info(f"{source_name} found {len(source_results)} results for query: {query_variant}")
                        break  # Move to next source if we found results
                
                # Add delay between requests
                time.sleep(0.3)
        
        # Strategy 2: Recipe-specific searches if we need more results
        if len(results) < num_results:
            recipe_results = self._search_recipe_specific(query, num_results - len(results))
            results.extend(recipe_results)
        
        # Strategy 3: Technique-specific searches
        if len(results) < num_results:
            technique_results = self._search_technique_specific(query, num_results - len(results))
            results.extend(technique_results)
        
        # Strategy 4: Cooking fallback sources
        if len(results) < num_results:
            fallback_results = self._get_fallback_sources(query, num_results - len(results))
            results.extend(fallback_results)
        
        # Remove duplicates and return top results
        unique_results = self._remove_duplicates(results)
        return unique_results[:num_results]
    
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
    
    def _create_enhanced_queries(self, query: str) -> List[str]:
        """Create enhanced query variations for better cooking search results"""
        import re
        
        # Clean the base query
        base_query = re.sub(r'[^\w\s\-\.]', ' ', query).strip()
        base_query = re.sub(r'\s+', ' ', base_query)
        
        enhanced_queries = [base_query]
        
        # Add cooking-specific enhancements
        cooking_enhancements = [
            f"{base_query} recipe",
            f"{base_query} cooking method",
            f"{base_query} how to cook",
            f"{base_query} ingredients",
            f"{base_query} technique",
            f"{base_query} tutorial"
        ]
        
        # Add technique-specific queries
        cooking_techniques = ['bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'sauté', 'braise', 'poach']
        for technique in cooking_techniques:
            if technique in base_query.lower():
                enhanced_queries.append(f"{base_query} {technique} method")
                enhanced_queries.append(f"how to {technique} {base_query}")
        
        # Add cuisine-specific enhancements
        cuisines = ['italian', 'chinese', 'mexican', 'french', 'indian', 'thai', 'japanese', 'mediterranean']
        for cuisine in cuisines:
            if cuisine in base_query.lower():
                enhanced_queries.append(f"{cuisine} {base_query} recipe")
                enhanced_queries.append(f"authentic {cuisine} {base_query}")
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(enhanced_queries))
        return unique_queries[:5]  # Limit to 5 query variations
    
    def _get_priority_sources(self) -> Dict[int, List[str]]:
        """Get sources organized by priority"""
        priority_sources = {1: [], 2: []}
        
        for source_name, config in self.cooking_sources.items():
            priority = config.get('priority', 2)
            priority_sources[priority].append(source_name)
        
        return priority_sources
    
    def _search_recipe_specific(self, query: str, num_results: int) -> List[Dict]:
        """Search for recipe-specific content"""
        recipe_queries = [
            f"{query} recipe ingredients",
            f"{query} recipe instructions",
            f"{query} recipe steps",
            f"how to make {query}",
            f"{query} cooking recipe"
        ]
        
        results = []
        for recipe_query in recipe_queries:
            if len(results) >= num_results:
                break
                
            # Search top priority sources for recipe content
            priority_sources = self._get_priority_sources()
            for source_name in priority_sources.get(1, []):
                if len(results) >= num_results:
                    break
                    
                source_config = self.cooking_sources[source_name]
                source_results = self._search_cooking_source(recipe_query, source_name, source_config)
                results.extend(source_results)
                time.sleep(0.2)
        
        return results[:num_results]
    
    def _search_technique_specific(self, query: str, num_results: int) -> List[Dict]:
        """Search for cooking technique-specific content"""
        technique_queries = [
            f"{query} cooking technique",
            f"{query} cooking method",
            f"how to cook {query}",
            f"{query} preparation method",
            f"{query} cooking tips"
        ]
        
        results = []
        for technique_query in technique_queries:
            if len(results) >= num_results:
                break
                
            # Search priority sources for technique content
            priority_sources = self._get_priority_sources()
            for source_name in priority_sources.get(1, []):
                if len(results) >= num_results:
                    break
                    
                source_config = self.cooking_sources[source_name]
                source_results = self._search_cooking_source(technique_query, source_name, source_config)
                results.extend(source_results)
                time.sleep(0.2)
        
        return results[:num_results]
    
    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
