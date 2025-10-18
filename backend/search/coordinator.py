import logging
from typing import List, Dict, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .engines.duckduckgo import DuckDuckGoEngine
from .engines.cooking import CookingSearchEngine
from .engines.multilingual import MultilingualCookingEngine
from .engines.video import VideoSearchEngine
from .extractors.content import ContentExtractor
from .processors.cooking import CookingSearchProcessor
from .processors.language import LanguageProcessor
from .processors.sources import SourceAggregator
from .processors.enhanced import EnhancedContentProcessor
# Reranker removed - using simple relevance scoring for cooking content

logger = logging.getLogger(__name__)

class SearchCoordinator:
    """Coordinate multiple search strategies for comprehensive cooking information"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        
        # Initialize search engines
        self.duckduckgo_engine = DuckDuckGoEngine()
        self.cooking_engine = CookingSearchEngine()
        self.multilingual_engine = MultilingualCookingEngine()
        self.video_engine = VideoSearchEngine()
        
        # Initialize processors
        self.content_extractor = ContentExtractor()
        self.cooking_processor = CookingSearchProcessor()
        self.language_processor = LanguageProcessor()
        self.source_aggregator = SourceAggregator()
        self.enhanced_processor = EnhancedContentProcessor()
        self.reranker = None  # No complex reranking needed for cooking content
        
        # Search strategies - prioritize cooking sources first
        self.strategies = [
            self._search_cooking_sources,
            self._search_duckduckgo,
            self._search_multilingual
        ]
    
    def search(self, query: str, num_results: int = 10, target_language: str = None) -> Tuple[str, Dict[int, str]]:
        """Execute comprehensive multilingual search with multiple strategies"""
        logger.info(f"Starting comprehensive multilingual search for: {query}")
        
        # Detect and enhance query for multiple languages
        enhanced_queries = self.language_processor.enhance_query(query, target_language)
        logger.info(f"Enhanced queries: {list(enhanced_queries.keys())}")
        
        # Execute search strategies in parallel
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit search tasks for each language
            future_to_strategy = {}
            
            for lang, enhanced_query in enhanced_queries.items():
                for strategy in self.strategies:
                    future = executor.submit(strategy, enhanced_query, num_results // len(enhanced_queries), lang)
                    future_to_strategy[future] = f"{strategy.__name__}_{lang}"
            
            # Collect results
            for future in as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                        logger.info(f"{strategy_name} found {len(results)} results")
                except Exception as e:
                    logger.error(f"{strategy_name} failed: {e}")
        
        # Remove duplicates and filter by language preference
        unique_results = self._remove_duplicates(all_results)
        if target_language:
            unique_results = self.language_processor.filter_by_language(unique_results, target_language)
        
        logger.info(f"Total unique results: {len(unique_results)}")
        
        # Extract content from URLs
        enriched_results = self._enrich_with_content(unique_results)
        
        # Simple cooking relevance filtering
        if enriched_results:
            cooking_keywords = ['recipe', 'cooking', 'baking', 'food', 'ingredient', 'kitchen', 'chef', 'meal', 'dish', 'cuisine', 'cook', 'bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'season', 'spice', 'herb', 'sauce', 'marinade', 'dressing']
            relevant_results = []
            for result in enriched_results:
                title = result.get('title', '').lower()
                content = result.get('content', '').lower()
                if any(keyword in title or keyword in content for keyword in cooking_keywords):
                    relevant_results.append(result)
            
            if relevant_results:
                enriched_results = relevant_results
                logger.info(f"Filtered to {len(enriched_results)} cooking-relevant results")
        
        # Process results into comprehensive summary
        summary, url_mapping = self.cooking_processor.process_results(enriched_results, query)
        
        logger.info(f"Multilingual search completed: {len(url_mapping)} sources processed")
        return summary, url_mapping
    
    def _search_multilingual(self, query: str, num_results: int, language: str = None) -> List[Dict]:
        """Search using multilingual medical engine"""
        try:
            if language:
                results = self.multilingual_engine.search_by_language(query, language, num_results)
            else:
                results = self.multilingual_engine.search(query, num_results)
            return results
        except Exception as e:
            logger.error(f"Multilingual search failed: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int, language: str = None) -> List[Dict]:
        """Search using DuckDuckGo engine"""
        try:
            results = self.duckduckgo_engine.search(query, num_results)
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _search_cooking_sources(self, query: str, num_results: int, language: str = None) -> List[Dict]:
        """Search using cooking sources engine"""
        try:
            results = self.cooking_engine.search(query, num_results)
            return results
        except Exception as e:
            logger.error(f"Cooking sources search failed: {e}")
            return []
    
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
    
    def _enrich_with_content(self, results: List[Dict]) -> List[Dict]:
        """Enrich results with extracted content"""
        enriched_results = []
        
        # Extract content in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit content extraction tasks
            future_to_result = {
                executor.submit(self.content_extractor.extract, result['url']): result
                for result in results
            }
            
            # Collect enriched results
            for future in as_completed(future_to_result):
                original_result = future_to_result[future]
                try:
                    content = future.result()
                    if content:
                        enriched_result = original_result.copy()
                        enriched_result['content'] = content
                        enriched_results.append(enriched_result)
                except Exception as e:
                    logger.warning(f"Content extraction failed for {original_result['url']}: {e}")
                    # Still include result without content
                    enriched_results.append(original_result)
        
        return enriched_results
    
    def quick_search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Quick search for basic results without content extraction"""
        logger.info(f"Quick search for: {query}")
        
        # Try cooking sources first for better relevance
        results = []
        try:
            cooking_results = self.cooking_engine.search(query, num_results)
            if cooking_results:
                results = cooking_results
                logger.info(f"Cooking engine found {len(results)} results")
        except Exception as e:
            logger.warning(f"Cooking engine failed: {e}")
        
        # If no cooking results, try DuckDuckGo
        if not results:
            logger.info("No cooking results, trying DuckDuckGo")
            results = self.duckduckgo_engine.search(query, num_results)
        
        # If no results, try with simplified query
        if not results:
            logger.warning("No results from search engines, trying simplified query")
            simplified_query = self._simplify_query(query)
            if simplified_query != query:
                # Try cooking sources first with simplified query
                try:
                    cooking_results = self.cooking_engine.search(simplified_query, num_results)
                    if cooking_results:
                        results = cooking_results
                        logger.info(f"Simplified cooking query '{simplified_query}' found {len(results)} results")
                except Exception as e:
                    logger.warning(f"Simplified cooking query failed: {e}")
                
                # If still no results, try DuckDuckGo with simplified query
                if not results:
                    results = self.duckduckgo_engine.search(simplified_query, num_results)
                    logger.info(f"Simplified DuckDuckGo query '{simplified_query}' found {len(results)} results")
        
        # Remove duplicates
        unique_results = self._remove_duplicates(results)
        
        # If we still have no results, create a basic fallback
        if not unique_results:
            logger.warning("No search results found, creating basic fallback")
            unique_results = self._create_fallback_results(query)
        
        logger.info(f"Quick search completed: {len(unique_results)} results")
        return unique_results
    
    def _simplify_query(self, query: str) -> str:
        """Simplify query to core cooking terms"""
        if not query:
            return ""
        
        # Extract key cooking terms
        import re
        words = query.split()
        
        # Keep cooking keywords and important terms
        cooking_keywords = [
            'recipe', 'cooking', 'baking', 'roasting', 'grilling', 'frying', 'boiling', 'steaming',
            'ingredients', 'seasoning', 'spices', 'herbs', 'sauce', 'marinade', 'dressing',
            'technique', 'method', 'temperature', 'timing', 'preparation', 'cooking time',
            'oven', 'stovetop', 'grill', 'pan', 'pot', 'skillet', 'knife', 'cutting',
            'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', 'diet',
            'appetizer', 'main course', 'dessert', 'breakfast', 'lunch', 'dinner',
            'cuisine', 'italian', 'chinese', 'mexican', 'french', 'indian', 'thai'
        ]
        
        # Keep words that are cooking keywords or are important (longer than 3 chars)
        important_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower in cooking_keywords or len(word) > 3:
                important_words.append(word)
        
        # If we have important words, use them; otherwise use first few words
        if important_words:
            return ' '.join(important_words[:5])  # Max 5 words
        else:
            return ' '.join(words[:3])  # Max 3 words
    
    def _create_fallback_results(self, query: str) -> List[Dict]:
        """Create basic fallback results when search fails"""
        # Create some basic cooking information URLs as fallback
        fallback_urls = [
            "https://www.allrecipes.com",
            "https://www.foodnetwork.com",
            "https://www.epicurious.com",
            "https://www.seriouseats.com",
            "https://www.bonappetit.com"
        ]
        
        results = []
        for i, url in enumerate(fallback_urls[:3]):  # Limit to 3 fallback results
            results.append({
                'url': url,
                'title': f"Cooking Information - {query}",
                'source': 'fallback',
                'composite_score': 0.3 - (i * 0.05)  # Decreasing score
            })
        
        return results
    
    def cooking_focus_search(self, query: str, num_results: int = 8) -> Tuple[str, Dict[int, str]]:
        """Cooking-focused search with enhanced processing"""
        logger.info(f"Cooking focus search for: {query}")
        
        # Use cooking engine primarily
        cooking_results = self.cooking_engine.search(query, num_results)
        
        # Add some general results for context
        general_results = self.duckduckgo_engine.search(query, 3)
        
        # Combine and deduplicate
        all_results = self._remove_duplicates(cooking_results + general_results)
        
        # Enrich with content
        enriched_results = self._enrich_with_content(all_results)
        
        # Simple cooking relevance filtering
        if enriched_results:
            cooking_keywords = ['recipe', 'cooking', 'baking', 'food', 'ingredient', 'kitchen', 'chef', 'meal', 'dish', 'cuisine', 'cook', 'bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'season', 'spice', 'herb', 'sauce', 'marinade', 'dressing']
            relevant_results = []
            for result in enriched_results:
                title = result.get('title', '').lower()
                content = result.get('content', '').lower()
                if any(keyword in title or keyword in content for keyword in cooking_keywords):
                    relevant_results.append(result)
            
            if relevant_results:
                enriched_results = relevant_results
                logger.info(f"Filtered to {len(enriched_results)} cooking-relevant results")
        
        # Process with cooking focus
        summary, url_mapping = self.cooking_processor.process_results(enriched_results, query)
        
        logger.info(f"Cooking focus search completed: {len(url_mapping)} sources")
        return summary, url_mapping
    
    def multilingual_cooking_search(self, query: str, num_results: int = 10, target_language: str = None) -> Tuple[str, Dict[int, str]]:
        """Comprehensive multilingual cooking search"""
        logger.info(f"Multilingual cooking search for: {query} (target: {target_language})")
        
        # Detect source language
        source_language = self.language_processor.detect_language(query)
        logger.info(f"Detected source language: {source_language}")
        
        # Use multilingual search with language preference
        summary, url_mapping = self.search(query, num_results, target_language)
        
        logger.info(f"Multilingual cooking search completed: {len(url_mapping)} sources")
        return summary, url_mapping
    
    def comprehensive_search(self, query: str, num_results: int = 15, target_language: str = None, include_videos: bool = True) -> Tuple[str, Dict[int, str], Dict]:
        """Comprehensive search with maximum information extraction and detailed references"""
        logger.info(f"Starting comprehensive search for: {query} (target: {target_language})")
        
        # Detect source language
        source_language = self.language_processor.detect_language(query)
        logger.info(f"Detected source language: {source_language}")
        
        # Execute comprehensive search
        search_results = []
        video_results = []
        
        # 1. Multilingual text search
        text_summary, text_url_mapping = self.search(query, num_results, target_language)
        
        # 2. Video search if requested
        if include_videos:
            try:
                video_results = self.video_search(query, num_results=5, target_language=target_language)
                logger.info(f"Video search found {len(video_results)} videos")
            except Exception as e:
                logger.warning(f"Video search failed: {e}")
        
        # 3. Aggregate all sources
        all_sources = []
        
        # Add text sources
        for i, url in text_url_mapping.items():
            # Find corresponding source data
            source_data = self._find_source_data(url, text_url_mapping)
            if source_data:
                all_sources.append(source_data)
        
        # Add video sources
        for video in video_results:
            all_sources.append(video)
        
        # 4. Process with enhanced content processor
        if all_sources:
            comprehensive_summary, detailed_mapping = self.enhanced_processor.process_comprehensive_content(all_sources, query)
        else:
            comprehensive_summary = text_summary
            detailed_mapping = text_url_mapping
        
        # 5. Create comprehensive source aggregation
        source_aggregation = self.source_aggregator.aggregate_sources(all_sources, video_results)
        
        # 6. Generate comprehensive references
        comprehensive_references = self.source_aggregator.create_comprehensive_references(all_sources, max_references=20)
        
        # 7. Add inline citations
        final_summary = self.enhanced_processor.create_inline_citations(comprehensive_summary, detailed_mapping)
        
        # 8. Add source statistics
        source_stats = self.enhanced_processor.generate_source_statistics(all_sources)
        
        # 9. Combine everything
        final_response = f"{final_summary}\n\n{comprehensive_references}\n\n{source_stats}"
        
        logger.info(f"Comprehensive search completed: {len(all_sources)} total sources processed")
        
        return final_response, detailed_mapping, source_aggregation
    
    def _find_source_data(self, url: str, url_mapping: Dict[int, str]) -> Dict:
        """Find source data for a given URL"""
        # This is a simplified version - ensure required fields always exist
        return {
            'url': url,
            'title': f"Source: {url}",
            'content': '',
            'domain': self._extract_domain(url),
            'type': 'text',
            'source_type': 'text',
            'language': 'en',
            'source_name': '',
            'platform': ''
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''
    
    def video_search(self, query: str, num_results: int = 3, target_language: str = None) -> List[Dict]:
        """Search for cooking videos across multiple platforms"""
        logger.info(f"Video search for: {query} (target: {target_language})")
        
        # Detect language if not provided
        if not target_language:
            target_language = self.language_processor.detect_language(query)
        
        # Map language codes
        lang_mapping = {
            'EN': 'en',
            'VI': 'vi', 
            'ZH': 'zh',
            'en': 'en',
            'vi': 'vi',
            'zh': 'zh'
        }
        search_language = lang_mapping.get(target_language, 'en')
        
        # Search for videos
        raw_results = self.video_engine.search(query, num_results, search_language)
        
        # Simple video relevance filtering
        cooking_keywords = ['recipe', 'cooking', 'baking', 'food', 'ingredient', 'kitchen', 'chef', 'meal', 'dish', 'cuisine', 'cook', 'bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'season', 'spice', 'herb', 'sauce', 'marinade', 'dressing']
        filtered_video_results = []
        for result in raw_results:
            title = result.get('title', '').lower()
            if any(keyword in title for keyword in cooking_keywords):
                filtered_video_results.append(result)
        
        # Validate and normalize results to avoid corrupted cards/links
        video_results = self._sanitize_video_results(filtered_video_results, limit=num_results)
        
        logger.info(f"Video search completed: {len(video_results)} videos found")
        return video_results

    def _sanitize_video_results(self, results: List[Dict], limit: int = 4) -> List[Dict]:
        """Ensure each video has a valid absolute https URL, reasonable title, and platform metadata.
        Drop unreachable/broken items and deduplicate by URL.
        """
        from urllib.parse import urlparse
        import requests
        clean: List[Dict] = []
        seen = set()
        for item in results or []:
            url = (item or {}).get('url', '')
            title = (item or {}).get('title', '').strip()
            if not url or not title:
                continue
            try:
                parsed = urlparse(url)
                if parsed.scheme not in ('http', 'https'):
                    continue
                if not parsed.netloc:
                    continue
                # Quick reachability check; YouTube often blocks HEAD, so skip strict checks for youtube domain
                host = parsed.netloc.lower()
                norm_url = url
                if 'youtube.com' not in host:
                    try:
                        r = requests.head(url, allow_redirects=True, timeout=3)
                        if r.status_code >= 400:
                            continue
                        norm_url = getattr(r, 'url', url) or url
                    except Exception:
                        # If HEAD blocked, try a light GET with small timeout
                        try:
                            r = requests.get(url, stream=True, timeout=4)
                            if r.status_code >= 400:
                                continue
                            norm_url = getattr(r, 'url', url) or url
                        except Exception:
                            continue
                if norm_url in seen:
                    continue
                seen.add(norm_url)
                platform = parsed.netloc.lower()
                if platform.startswith('www.'):
                    platform = platform[4:]
                clean.append({
                    'title': title,
                    'url': norm_url,
                    'thumbnail': item.get('thumbnail', ''),
                    'source': item.get('source', platform.split('.')[0]),
                    'platform': platform,
                    'language': item.get('language', 'en')
                })
                if len(clean) >= limit:
                    break
            except Exception:
                continue
        return clean



