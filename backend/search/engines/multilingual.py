import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import time
import re
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)

class MultilingualCookingEngine:
    """Multilingual cooking search engine supporting English, Vietnamese, and Chinese sources"""
    
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5,vi;q=0.3,zh-CN;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.timeout = timeout
        
        # Comprehensive cooking sources by language
        self.cooking_sources = {
            'en': {
                # Major Cooking Sources
                'allrecipes': {
                    'base_url': 'https://www.allrecipes.com',
                    'search_url': 'https://www.allrecipes.com/search',
                    'domains': ['allrecipes.com'],
                    'selectors': ['a[href*="/recipe/"]', 'a[href*="/recipes/"]', '.search-result a']
                },
                'food_network': {
                    'base_url': 'https://www.foodnetwork.com',
                    'search_url': 'https://www.foodnetwork.com/search',
                    'domains': ['foodnetwork.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                },
                'epicurious': {
                    'base_url': 'https://www.epicurious.com',
                    'search_url': 'https://www.epicurious.com/search',
                    'domains': ['epicurious.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                },
                'serious_eats': {
                    'base_url': 'https://www.seriouseats.com',
                    'search_url': 'https://www.seriouseats.com/search',
                    'domains': ['seriouseats.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                },
                'bon_appetit': {
                    'base_url': 'https://www.bonappetit.com',
                    'search_url': 'https://www.bonappetit.com/search',
                    'domains': ['bonappetit.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                },
                'taste_of_home': {
                    'base_url': 'https://www.tasteofhome.com',
                    'search_url': 'https://www.tasteofhome.com/search',
                    'domains': ['tasteofhome.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                },
                'food_com': {
                    'base_url': 'https://www.food.com',
                    'search_url': 'https://www.food.com/search',
                    'domains': ['food.com'],
                    'selectors': ['a[href*="/recipes/"]', 'a[href*="/recipe/"]', '.search-result a']
                }
            },
            'vi': {
                # Vietnamese Cooking Sources
                'mon_ngon_viet': {
                    'base_url': 'https://monngonviet.com',
                    'search_url': 'https://monngonviet.com/tim-kiem',
                    'domains': ['monngonviet.com'],
                    'selectors': ['a[href*="/cong-thuc/"]', 'a[href*="/mon-an/"]', '.search-result a']
                },
                'day_phong_cach': {
                    'base_url': 'https://dayphongcach.vn',
                    'search_url': 'https://dayphongcach.vn/tim-kiem',
                    'domains': ['dayphongcach.vn'],
                    'selectors': ['a[href*="/mon-an/"]', 'a[href*="/cong-thuc/"]', '.search-result a']
                },
                'am_thuc_viet': {
                    'base_url': 'https://amthucviet.vn',
                    'search_url': 'https://amthucviet.vn/tim-kiem',
                    'domains': ['amthucviet.vn'],
                    'selectors': ['a[href*="/mon-an/"]', 'a[href*="/cong-thuc/"]', '.search-result a']
                }
            },
            'zh': {
                # Chinese Cooking Sources
                'xiachufang': {
                    'base_url': 'https://www.xiachufang.com',
                    'search_url': 'https://www.xiachufang.com/search',
                    'domains': ['xiachufang.com'],
                    'selectors': ['a[href*="/recipe/"]', 'a[href*="/cook/"]', '.search-result a']
                },
                'douguo': {
                    'base_url': 'https://www.douguo.com',
                    'search_url': 'https://www.douguo.com/search',
                    'domains': ['douguo.com'],
                    'selectors': ['a[href*="/recipe/"]', 'a[href*="/cook/"]', '.search-result a']
                },
                'meishij': {
                    'base_url': 'https://www.meishij.net',
                    'search_url': 'https://www.meishij.net/search',
                    'domains': ['meishij.net'],
                    'selectors': ['a[href*="/recipe/"]', 'a[href*="/cook/"]', '.search-result a']
                }
            }
        }
    
    def search(self, query: str, num_results: int = 10, languages: List[str] = None) -> List[Dict]:
        """Search across multiple languages and cooking sources"""
        if languages is None:
            languages = ['en', 'vi', 'zh']
        
        all_results = []
        
        for lang in languages:
            if lang in self.cooking_sources:
                lang_results = self._search_language_sources(query, lang, num_results // len(languages))
                all_results.extend(lang_results)
                time.sleep(0.5)  # Rate limiting between languages
        
        return all_results[:num_results]
    
    def _search_language_sources(self, query: str, language: str, num_results: int) -> List[Dict]:
        """Search sources for a specific language"""
        results = []
        sources = self.cooking_sources.get(language, {})
        
        for source_name, source_config in sources.items():
            if len(results) >= num_results:
                break
                
            source_results = self._search_source(query, source_name, source_config, language)
            results.extend(source_results)
            time.sleep(0.3)  # Rate limiting
        
        return results
    
    def _search_source(self, query: str, source_name: str, source_config: Dict, language: str) -> List[Dict]:
        """Search a specific cooking source"""
        try:
            search_url = source_config.get('search_url')
            if not search_url:
                return []
            
            params = {
                'q': query,
                'query': query,
                'search': query,
                'keyword': query
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Source-specific selectors
            selectors = source_config.get('selectors', ['a[href*="http"]'])
            
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
                            'domain': source_config['domains'][0],
                            'language': language
                        })
                except Exception as e:
                    logger.debug(f"Error parsing {source_name} link: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Cooking source {source_name} ({language}) search failed: {e}")
            return []
    
    def search_by_language(self, query: str, language: str, num_results: int = 10) -> List[Dict]:
        """Search sources for a specific language only"""
        if language not in self.cooking_sources:
            logger.warning(f"Language {language} not supported")
            return []
        
        return self._search_language_sources(query, language, num_results)
    
    def _get_fallback_sources(self, query: str, language: str, num_results: int) -> List[Dict]:
        """Get fallback cooking sources when direct search fails"""
        fallback_sources = {
            'en': [
                {
                    'url': 'https://www.allrecipes.com/recipes',
                    'title': f'AllRecipes: {query}',
                    'source': 'allrecipes_fallback',
                    'language': 'en',
                    'domain': 'allrecipes.com'
                },
                {
                    'url': 'https://www.foodnetwork.com/recipes',
                    'title': f'Food Network: {query}',
                    'source': 'foodnetwork_fallback',
                    'language': 'en',
                    'domain': 'foodnetwork.com'
                },
                {
                    'url': 'https://www.epicurious.com/recipes-menus',
                    'title': f'Epicurious: {query}',
                    'source': 'epicurious_fallback',
                    'language': 'en',
                    'domain': 'epicurious.com'
                }
            ],
            'vi': [
                {
                    'url': 'https://monngonviet.com/cong-thuc',
                    'title': f'Món Ngon Việt: {query}',
                    'source': 'monngonviet_fallback',
                    'language': 'vi',
                    'domain': 'monngonviet.com'
                },
                {
                    'url': 'https://dayphongcach.vn/mon-an',
                    'title': f'Dạy Phong Cách: {query}',
                    'source': 'dayphongcach_fallback',
                    'language': 'vi',
                    'domain': 'dayphongcach.vn'
                }
            ],
            'zh': [
                {
                    'url': 'https://www.xiachufang.com/recipe',
                    'title': f'下厨房: {query}',
                    'source': 'xiachufang_fallback',
                    'language': 'zh',
                    'domain': 'xiachufang.com'
                },
                {
                    'url': 'https://www.douguo.com/recipe',
                    'title': f'豆果: {query}',
                    'source': 'douguo_fallback',
                    'language': 'zh',
                    'domain': 'douguo.com'
                }
            ]
        }
        
        return fallback_sources.get(language, [])[:num_results]