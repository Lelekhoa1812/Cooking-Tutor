import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import time
import re

logger = logging.getLogger(__name__)

class ImageSearchEngine:
    """Search engine for cooking-related images"""
    
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = timeout
    
    def search_cooking_images(self, query: str, num_results: int = 3, language: str = "en") -> List[Dict]:
        """Search for cooking-related images with robust error handling"""
        if not query or not query.strip():
            logger.warning("Empty query provided for image search")
            return []
        
        results = []
        
        # Try multiple image search strategies
        strategies = [
            self._search_google_images,
            self._search_bing_images,
            self._search_unsplash
        ]
        
        for strategy in strategies:
            try:
                strategy_results = strategy(query, num_results, language)
                if strategy_results:
                    # Filter and validate results
                    valid_results = self._validate_image_results(strategy_results)
                    if valid_results:
                        results.extend(valid_results)
                        logger.info(f"Image search strategy found {len(valid_results)} valid results")
                        if len(results) >= num_results:
                            break
            except Exception as e:
                logger.warning(f"Image search strategy failed: {e}")
                continue
        
        # Remove duplicates and return
        unique_results = self._remove_duplicate_images(results)
        final_results = unique_results[:num_results]
        
        logger.info(f"Image search completed: {len(final_results)} unique results from {len(results)} total")
        return final_results
    
    def _validate_image_results(self, results: List[Dict]) -> List[Dict]:
        """Validate and clean image results"""
        valid_results = []
        
        for result in results:
            try:
                # Check required fields
                if not result.get('url') or not result.get('url').startswith('http'):
                    continue
                
                # Ensure we have at least a basic title
                if not result.get('title'):
                    result['title'] = 'Cooking image'
                
                # Ensure we have alt text
                if not result.get('alt_text'):
                    result['alt_text'] = result.get('title', 'Cooking image')
                
                valid_results.append(result)
                
            except Exception as e:
                logger.debug(f"Invalid image result skipped: {e}")
                continue
        
        return valid_results
    
    def _remove_duplicate_images(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate images based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _search_google_images(self, query: str, num_results: int, language: str) -> List[Dict]:
        """Search Google Images for cooking content"""
        try:
            # Add cooking context to improve relevance
            cooking_query = f"{query} recipe cooking food dish"
            
            url = "https://www.google.com/search"
            params = {
                'q': cooking_query,
                'tbm': 'isch',  # Image search
                'hl': language,
                'safe': 'active',
                'num': min(num_results, 20)  # Limit results
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find image containers with multiple selectors
            image_containers = soup.find_all('div', class_='islrc')
            if not image_containers:
                # Try alternative selectors
                image_containers = soup.find_all('div', {'data-ved': True})
            
            for container in image_containers[:num_results]:
                try:
                    # Extract image URL
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    # Extract title/alt text
                    title = img_tag.get('alt', '') or img_tag.get('title', '') or 'Cooking image'
                    
                    # Extract source URL
                    link_tag = container.find('a')
                    source_url = link_tag.get('href', '') if link_tag else ''
                    
                    results.append({
                        'url': img_url,
                        'title': title,
                        'source_url': source_url,
                        'source': 'google_images',
                        'type': 'image'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing Google image: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Google Images search failed: {e}")
            return []
    
    def _search_bing_images(self, query: str, num_results: int, language: str) -> List[Dict]:
        """Search Bing Images for cooking content"""
        try:
            cooking_query = f"{query} recipe cooking food"
            
            url = "https://www.bing.com/images/search"
            params = {
                'q': cooking_query,
                'qft': '+filterui:imagesize-large',  # Large images
                'form': 'HDRSC2',
                'first': '1',
                'count': min(num_results, 20)
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find image containers with multiple selectors
            image_containers = soup.find_all('div', class_='img_cont')
            if not image_containers:
                # Try alternative selectors
                image_containers = soup.find_all('div', {'class': 'imgpt'})
            
            for container in image_containers[:num_results]:
                try:
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    title = img_tag.get('alt', '') or img_tag.get('title', '') or 'Cooking image'
                    
                    # Try to get source URL
                    link_tag = container.find('a')
                    source_url = link_tag.get('href', '') if link_tag else ''
                    
                    results.append({
                        'url': img_url,
                        'title': title,
                        'source_url': source_url,
                        'source': 'bing_images',
                        'type': 'image'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing Bing image: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Bing Images search failed: {e}")
            return []
    
    def _search_unsplash(self, query: str, num_results: int, language: str) -> List[Dict]:
        """Search Unsplash for high-quality cooking images"""
        try:
            cooking_query = f"{query} food cooking recipe"
            
            url = "https://unsplash.com/s/photos/" + cooking_query.replace(' ', '-')
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find image containers with multiple selectors
            image_containers = soup.find_all('figure')
            if not image_containers:
                # Try alternative selectors
                image_containers = soup.find_all('div', {'class': 'MorZF'})
            
            for container in image_containers[:num_results]:
                try:
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    title = img_tag.get('alt', '') or img_tag.get('title', '') or 'Cooking image'
                    
                    # Get source URL
                    link_tag = container.find('a')
                    source_url = link_tag.get('href', '') if link_tag else ''
                    if source_url and not source_url.startswith('http'):
                        source_url = 'https://unsplash.com' + source_url
                    
                    results.append({
                        'url': img_url,
                        'title': title,
                        'source_url': source_url,
                        'source': 'unsplash',
                        'type': 'image'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing Unsplash image: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Unsplash search failed: {e}")
            return []
    
    def _filter_cooking_relevance(self, images: List[Dict], query: str) -> List[Dict]:
        """Filter images for cooking relevance"""
        cooking_keywords = [
            'food', 'cooking', 'recipe', 'dish', 'meal', 'ingredient', 'kitchen',
            'chef', 'bake', 'cook', 'preparation', 'cuisine', 'delicious', 'tasty'
        ]
        
        relevant_images = []
        query_lower = query.lower()
        
        for image in images:
            title = image.get('title', '').lower()
            
            # Check if title contains cooking keywords or query terms
            is_relevant = (
                any(keyword in title for keyword in cooking_keywords) or
                any(word in title for word in query_lower.split() if len(word) > 3)
            )
            
            if is_relevant:
                relevant_images.append(image)
        
        return relevant_images
