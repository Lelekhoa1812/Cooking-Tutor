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
        """Search for cooking-related images"""
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
                    results.extend(strategy_results)
                    logger.info(f"Image search found {len(strategy_results)} results")
                    if len(results) >= num_results:
                        break
            except Exception as e:
                logger.warning(f"Image search strategy failed: {e}")
                continue
        
        return results[:num_results]
    
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
                'safe': 'active'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find image containers
            image_containers = soup.find_all('div', class_='islrc')
            
            for container in image_containers[:num_results]:
                try:
                    # Extract image URL
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    # Extract title/alt text
                    title = img_tag.get('alt', '') or img_tag.get('title', '')
                    
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
                'count': num_results
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find image containers
            image_containers = soup.find_all('div', class_='img_cont')
            
            for container in image_containers[:num_results]:
                try:
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    title = img_tag.get('alt', '') or img_tag.get('title', '')
                    
                    results.append({
                        'url': img_url,
                        'title': title,
                        'source_url': '',
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
            
            # Find image containers
            image_containers = soup.find_all('figure')
            
            for container in image_containers[:num_results]:
                try:
                    img_tag = container.find('img')
                    if not img_tag:
                        continue
                    
                    img_url = img_tag.get('src') or img_tag.get('data-src')
                    if not img_url or not img_url.startswith('http'):
                        continue
                    
                    title = img_tag.get('alt', '') or img_tag.get('title', '')
                    
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
