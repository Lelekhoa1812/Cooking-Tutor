import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
import re
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Extract and clean content from web pages"""
    
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.timeout = timeout
        
        # Cooking content indicators
        self.cooking_indicators = [
            'recipe', 'ingredients', 'instructions', 'cooking', 'baking', 'roasting',
            'grilling', 'frying', 'boiling', 'steaming', 'sautéing', 'braising',
            'seasoning', 'spices', 'herbs', 'sauce', 'marinade', 'dressing',
            'temperature', 'timing', 'preparation', 'technique', 'method',
            'oven', 'stovetop', 'grill', 'pan', 'pot', 'skillet', 'knife',
            'cutting', 'chopping', 'dicing', 'slicing', 'mixing', 'stirring',
            'servings', 'cook time', 'prep time', 'total time', 'difficulty'
        ]
    
    def extract(self, url: str, max_length: int = 2000) -> Optional[str]:
        """Extract content from a URL with cooking focus"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            self._remove_unwanted_elements(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            if not content:
                return None
            
            # Clean and process content
            cleaned_content = self._clean_content(content)
            
            # Focus on cooking content if possible
            cooking_content = self._extract_cooking_content(cleaned_content)
            
            # Truncate to max length
            final_content = self._truncate_content(cooking_content or cleaned_content, max_length)
            
            return final_content if final_content else None
            
        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
            return None
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """Remove unwanted HTML elements"""
        unwanted_tags = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'advertisement', 'ads', 'sidebar', 'menu', 'navigation',
            'social', 'share', 'comment', 'comments', 'related',
            'cookie', 'privacy', 'terms', 'disclaimer'
        ]
        
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with unwanted classes/ids
        unwanted_selectors = [
            '[class*="ad"]', '[class*="advertisement"]', '[class*="sidebar"]',
            '[class*="menu"]', '[class*="nav"]', '[class*="social"]',
            '[class*="share"]', '[class*="comment"]', '[class*="related"]',
            '[id*="ad"]', '[id*="sidebar"]', '[id*="menu"]', '[id*="nav"]'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Priority order for content extraction
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.main-content',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.page-content',
            'body'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Get the largest content element
                largest_element = max(elements, key=lambda x: len(x.get_text()))
                content = largest_element.get_text(separator=' ', strip=True)
                if len(content) > 100:  # Minimum content length
                    return content
        
        # Fallback: get all text
        return soup.get_text(separator=' ', strip=True)
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        artifacts = [
            r'Cookie\s+Policy',
            r'Privacy\s+Policy',
            r'Terms\s+of\s+Service',
            r'Subscribe\s+to\s+our\s+newsletter',
            r'Follow\s+us\s+on',
            r'Share\s+this\s+article',
            r'Related\s+articles',
            r'Advertisement',
            r'Ad\s+content'
        ]
        
        for artifact in artifacts:
            content = re.sub(artifact, '', content, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        content = re.sub(r'[!]{2,}', '!', content)
        content = re.sub(r'[?]{2,}', '?', content)
        
        return content.strip()
    
    def _extract_cooking_content(self, content: str) -> Optional[str]:
        """Extract cooking-focused content from the text"""
        if not content:
            return None
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        cooking_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            # Check if sentence contains cooking indicators
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in self.cooking_indicators):
                cooking_sentences.append(sentence)
        
        if cooking_sentences:
            # Return cooking sentences, prioritizing longer ones
            cooking_sentences.sort(key=len, reverse=True)
            return '. '.join(cooking_sentences[:15]) + '.'  # More sentences for cooking content
        
        return None
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to max length while preserving sentences"""
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > max_length * 0.7:  # If we can find a good break point
            return content[:last_sentence_end + 1]
        
        # Fallback: truncate at word boundary
        words = truncated.split()
        if len(words) > 1:
            return ' '.join(words[:-1]) + '...'
        
        return truncated + '...'
    
    def extract_multiple(self, urls: list, max_length: int = 2000) -> Dict[str, str]:
        """Extract content from multiple URLs"""
        results = {}
        
        for url in urls:
            try:
                content = self.extract(url, max_length)
                if content:
                    results[url] = content
                time.sleep(0.5)  # Be respectful to servers
            except Exception as e:
                logger.warning(f"Failed to extract content from {url}: {e}")
                continue
        
        return results
