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
        """Search for diverse cooking-related images including ingredients, techniques, and final dishes"""
        if not query or not query.strip():
            logger.warning("Empty query provided for image search")
            return []
        
        # Generate diverse search queries for comprehensive visual coverage
        search_queries = self._generate_diverse_cooking_queries(query, num_results)
        
        all_results = []
        
        # Try multiple image search strategies with diverse queries
        strategies = [
            self._search_google_images,
            self._search_bing_images,
            self._search_unsplash
        ]
        
        for strategy in strategies:
            try:
                strategy_results = []
                for search_query in search_queries:
                    query_results = strategy(search_query['query'], search_query['max_results'], language)
                    if query_results:
                        # Add query context to results
                        for result in query_results:
                            result['query_context'] = search_query['context']
                            result['image_type'] = search_query['type']
                        strategy_results.extend(query_results)
                
                if strategy_results:
                    # Filter and validate results
                    valid_results = self._validate_image_results(strategy_results)
                    if valid_results:
                        all_results.extend(valid_results)
                        logger.info(f"Image search strategy found {len(valid_results)} valid results")
                        if len(all_results) >= num_results * 2:  # Get more to filter
                            break
            except Exception as e:
                logger.warning(f"Image search strategy failed: {e}")
                continue
        
        # Remove duplicates and prioritize diverse results
        unique_results = self._remove_duplicate_images(all_results)
        diverse_results = self._prioritize_diverse_images(unique_results, num_results)
        
        logger.info(f"Image search completed: {len(diverse_results)} diverse results from {len(all_results)} total")
        return diverse_results
    
    def _generate_diverse_cooking_queries(self, original_query: str, num_results: int) -> List[Dict]:
        """Generate diverse search queries for comprehensive cooking image coverage"""
        queries = []
        
        # Extract key cooking terms from the original query
        query_lower = original_query.lower()
        
        # Clean the original query for better search results
        clean_query = original_query.strip()
        
        # 1. Final dish query - more specific and relevant
        if any(keyword in query_lower for keyword in ['pad thai', 'noodles', 'pasta']):
            final_dish_query = f"pad thai dish completed finished"
        elif any(keyword in query_lower for keyword in ['fusion', 'western']):
            final_dish_query = f"fusion cooking dish completed"
        else:
            final_dish_query = f"{clean_query} dish completed"
        
        queries.append({
            'query': final_dish_query,
            'context': 'final_dish',
            'type': 'final_dish',
            'max_results': max(1, num_results // 3)
        })
        
        # 2. Ingredients query - more specific
        if any(keyword in query_lower for keyword in ['pad thai', 'noodles', 'pasta']):
            ingredients_query = f"pad thai ingredients rice noodles shrimp"
        elif any(keyword in query_lower for keyword in ['fusion', 'western']):
            ingredients_query = f"fusion cooking ingredients fresh"
        else:
            ingredients_query = f"{clean_query} ingredients fresh"
        
        queries.append({
            'query': ingredients_query,
            'context': 'ingredients',
            'type': 'ingredients',
            'max_results': max(1, num_results // 3)
        })
        
        # 3. Cooking technique/process query - more specific
        if any(keyword in query_lower for keyword in ['pad thai', 'noodles', 'pasta']):
            technique_query = f"pad thai cooking technique wok stir fry"
        elif any(keyword in query_lower for keyword in ['fusion', 'western']):
            technique_query = f"fusion cooking technique western"
        else:
            technique_query = f"{clean_query} cooking technique"
        
        queries.append({
            'query': technique_query,
            'context': 'technique',
            'type': 'technique',
            'max_results': max(1, num_results // 3)
        })
        
        return queries
    
    def _prioritize_diverse_images(self, results: List[Dict], num_results: int) -> List[Dict]:
        """Prioritize diverse image types for better visual instruction"""
        # Group results by type
        type_groups = {
            'final_dish': [],
            'ingredients': [],
            'technique': [],
            'other': []
        }
        
        for result in results:
            image_type = result.get('image_type', 'other')
            if image_type in type_groups:
                type_groups[image_type].append(result)
            else:
                type_groups['other'].append(result)
        
        # Select diverse results
        diverse_results = []
        
        # Prioritize: 1 final dish, 1 ingredients, 1 technique, then fill with others
        if type_groups['final_dish']:
            diverse_results.append(type_groups['final_dish'][0])
        if type_groups['ingredients'] and len(diverse_results) < num_results:
            diverse_results.append(type_groups['ingredients'][0])
        if type_groups['technique'] and len(diverse_results) < num_results:
            diverse_results.append(type_groups['technique'][0])
        
        # Fill remaining slots with other results
        all_remaining = []
        for group in type_groups.values():
            all_remaining.extend(group[1:])  # Skip first item (already used)
        
        diverse_results.extend(all_remaining[:num_results - len(diverse_results)])
        
        return diverse_results[:num_results]
    
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
            # Use the query as-is for better relevance, don't add generic terms
            search_query = query.strip()
            
            url = "https://www.google.com/search"
            params = {
                'q': search_query,
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
            # Use the query as-is for better relevance
            search_query = query.strip()
            
            url = "https://www.bing.com/images/search"
            params = {
                'q': search_query,
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
            # Use the query as-is for better relevance
            search_query = query.strip()
            
            url = "https://unsplash.com/s/photos/" + search_query.replace(' ', '-')
            
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
