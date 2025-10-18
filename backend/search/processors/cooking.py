import logging
from typing import List, Dict, Tuple
from models.summarizer import summarizer
import re

logger = logging.getLogger(__name__)

class CookingSearchProcessor:
    """Process and enhance cooking search results"""
    
    def __init__(self):
        # Enhanced cooking keywords with categories
        self.cooking_keywords = {
            'primary': [
                'recipe', 'cooking', 'baking', 'roasting', 'grilling', 'frying', 'boiling', 'steaming',
                'sautéing', 'braising', 'poaching', 'broiling', 'searing', 'simmering'
            ],
            'ingredients': [
                'ingredients', 'seasoning', 'spices', 'herbs', 'sauce', 'marinade', 'dressing',
                'oil', 'butter', 'flour', 'sugar', 'salt', 'pepper', 'garlic', 'onion',
                'vegetables', 'meat', 'chicken', 'beef', 'pork', 'fish', 'seafood'
            ],
            'techniques': [
                'technique', 'method', 'temperature', 'timing', 'preparation', 'cooking time',
                'prep time', 'total time', 'servings', 'difficulty', 'skill level'
            ],
            'equipment': [
                'oven', 'stovetop', 'grill', 'pan', 'pot', 'skillet', 'knife', 'cutting',
                'mixing', 'stirring', 'chopping', 'dicing', 'slicing', 'whisking'
            ],
            'dietary': [
                'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', 'diet',
                'healthy', 'low-carb', 'low-fat', 'protein', 'fiber'
            ],
            'meal_types': [
                'appetizer', 'main course', 'dessert', 'breakfast', 'lunch', 'dinner',
                'snack', 'side dish', 'soup', 'salad', 'pasta', 'pizza'
            ],
            'cuisines': [
                'italian', 'chinese', 'mexican', 'french', 'indian', 'thai', 'japanese',
                'mediterranean', 'american', 'asian', 'european', 'fusion'
            ],
            'modifications': [
                'substitution', 'alternative', 'variation', 'modification', 'adaptation',
                'troubleshooting', 'tips', 'tricks', 'hacks', 'mistakes', 'common errors'
            ]
        }
        
        # Flatten all keywords for easy lookup
        self.all_cooking_keywords = []
        for category, keywords in self.cooking_keywords.items():
            self.all_cooking_keywords.extend(keywords)
    
    def process_results(self, results: List[Dict], user_query: str) -> Tuple[str, Dict[int, str]]:
        """Process search results and create comprehensive cooking summary"""
        if not results:
            return "", {}
        
        # Filter and rank results by cooking relevance
        relevant_results = self._filter_cooking_results(results, user_query)
        
        if not relevant_results:
            logger.warning("No cooking-relevant results found")
            return "", {}
        
        # Extract and summarize content
        summarized_results = self._summarize_results(relevant_results, user_query)
        
        # Create comprehensive summary
        combined_summary = self._create_combined_summary(summarized_results, user_query)
        
        # Create URL mapping for citations
        url_mapping = self._create_url_mapping(relevant_results)
        
        return combined_summary, url_mapping
    
    def _filter_cooking_results(self, results: List[Dict], user_query: str) -> List[Dict]:
        """Filter results by cooking relevance"""
        relevant_results = []
        
        for result in results:
            relevance_score = self._calculate_relevance_score(result, user_query)
            
            if relevance_score > 0.3:  # Threshold for cooking relevance
                result['relevance_score'] = relevance_score
                relevant_results.append(result)
        
        # Sort by relevance score
        relevant_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Limit to top results
        return relevant_results[:10]
    
    def _calculate_relevance_score(self, result: Dict, user_query: str) -> float:
        """Calculate enhanced cooking relevance score for a result"""
        score = 0.0
        
        # Check title and content relevance
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        query_lower = user_query.lower()
        
        # Direct query match in title (highest priority)
        query_words = query_lower.split()
        title_matches = sum(1 for word in query_words if word in title)
        if title_matches > 0:
            score += min(title_matches * 0.15, 0.4)
        
        # Direct query match in content
        content_matches = sum(1 for word in query_words if word in content)
        if content_matches > 0:
            score += min(content_matches * 0.05, 0.2)
        
        # Enhanced cooking keyword scoring by category
        for category, keywords in self.cooking_keywords.items():
            category_matches = sum(1 for keyword in keywords if keyword in title)
            if category_matches > 0:
                # Different weights for different categories
                if category == 'primary':
                    score += min(category_matches * 0.08, 0.25)
                elif category == 'ingredients':
                    score += min(category_matches * 0.06, 0.2)
                elif category == 'techniques':
                    score += min(category_matches * 0.07, 0.2)
                elif category == 'cuisines':
                    score += min(category_matches * 0.05, 0.15)
                else:
                    score += min(category_matches * 0.04, 0.1)
        
        # Domain credibility for cooking sources (enhanced list)
        url = result.get('url', '').lower()
        credible_domains = [
            'allrecipes.com', 'foodnetwork.com', 'epicurious.com', 'seriouseats.com',
            'bonappetit.com', 'cooking.nytimes.com', 'tasteofhome.com', 'food.com',
            'bbcgoodfood.com', 'jamieoliver.com', 'gordonramsay.com', 'marthastewart.com',
            'kingarthurbaking.com', 'sallysbakingaddiction.com', 'smittenkitchen.com',
            'food52.com', 'cookinglight.com', 'eatingwell.com', 'delish.com',
            'tasty.co', 'buzzfeed.com/food', 'foodandwine.com', 'saveur.com'
        ]
        
        if any(domain in url for domain in credible_domains):
            score += 0.25
        
        # Source type bonus for cooking
        source = result.get('source', '')
        if 'cooking' in source or 'recipe' in source or any(domain in source for domain in credible_domains):
            score += 0.15
        
        # Recipe-specific content bonus
        if any(word in title for word in ['recipe', 'how to', 'tutorial', 'guide']):
            score += 0.1
        
        # URL path analysis for cooking content
        if any(path in url for path in ['/recipe/', '/recipes/', '/cooking/', '/food/']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _summarize_results(self, results: List[Dict], user_query: str) -> List[Dict]:
        """Summarize content from search results"""
        summarized_results = []
        
        for i, result in enumerate(results):
            try:
                content = result.get('content', '')
                if not content:
                    continue
                
                # Create focused summary
                summary = summarizer.summarize_for_query(content, user_query, max_length=300)
                
                if summary:
                    summarized_results.append({
                        'id': i + 1,
                        'url': result['url'],
                        'title': result['title'],
                        'summary': summary,
                        'relevance_score': result.get('relevance_score', 0)
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to summarize result {i}: {e}")
                continue
        
        return summarized_results
    
    def _create_combined_summary(self, summarized_results: List[Dict], user_query: str) -> str:
        """Create a comprehensive summary from all results with proper source attribution"""
        if not summarized_results:
            return ""
        
        logger.info(f"Creating combined summary from {len(summarized_results)} results")
        
        # Group by topic/similarity
        topic_groups = self._group_by_topic(summarized_results)
        
        summary_parts = []
        citation_counter = 1
        
        for topic, results in topic_groups.items():
            if not results:
                continue
            
            logger.info(f"Processing {topic} topic with {len(results)} results")
            
            # Create topic summary with source attribution
            topic_summary = self._create_topic_summary(topic, results, user_query, citation_counter)
            if topic_summary:
                summary_parts.append(topic_summary)
                # Update citation counter for next topic
                citation_counter += len([r for r in results if r.get('summary')])
        
        # Combine all parts
        combined_summary = "\n\n".join(summary_parts)
        
        # Don't over-summarize - keep source attribution intact
        if len(combined_summary) > 2000:
            # Only truncate if absolutely necessary, but preserve structure
            lines = combined_summary.split('\n')
            truncated_lines = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) > 2000:
                    break
                truncated_lines.append(line)
                current_length += len(line)
            
            combined_summary = '\n'.join(truncated_lines)
            if len(truncated_lines) < len(lines):
                combined_summary += "\n\n*[Additional information available from multiple sources]*"
        
        logger.info(f"Final combined summary length: {len(combined_summary)} characters")
        return combined_summary
    
    def _group_by_topic(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group results by enhanced cooking topics"""
        topics = {
            'recipes': [],
            'techniques': [],
            'ingredients': [],
            'equipment': [],
            'tips_tricks': [],
            'general': []
        }
        
        for result in results:
            title_lower = result['title'].lower()
            summary_lower = result.get('summary', '').lower()
            content_lower = f"{title_lower} {summary_lower}"
            
            # Enhanced categorization by content
            if any(word in content_lower for word in ['recipe', 'ingredients', 'instructions', 'steps', 'how to make']):
                topics['recipes'].append(result)
            elif any(word in content_lower for word in ['technique', 'method', 'how to cook', 'cooking method', 'preparation']):
                topics['techniques'].append(result)
            elif any(word in content_lower for word in ['ingredients', 'substitution', 'alternative', 'variation', 'seasoning', 'spices']):
                topics['ingredients'].append(result)
            elif any(word in content_lower for word in ['equipment', 'tools', 'knife', 'pan', 'pot', 'oven', 'grill']):
                topics['equipment'].append(result)
            elif any(word in content_lower for word in ['tips', 'tricks', 'hacks', 'mistakes', 'troubleshooting', 'advice']):
                topics['tips_tricks'].append(result)
            else:
                topics['general'].append(result)
        
        return topics
    
    def _create_topic_summary(self, topic: str, results: List[Dict], user_query: str, citation_start: int = 1) -> str:
        """Create summary for a specific topic with source attribution"""
        if not results:
            return ""
        
        # Add topic header
        topic_headers = {
            'recipes': "**🍳 Recipes and Instructions:**",
            'techniques': "**👨‍🍳 Cooking Techniques:**",
            'ingredients': "**🥘 Ingredients and Substitutions:**",
            'equipment': "**🔪 Equipment and Tools:**",
            'tips_tricks': "**💡 Tips and Tricks:**",
            'general': "**📚 General Information:**"
        }
        
        header = topic_headers.get(topic, "**Information:**")
        summary_parts = [header]
        
        # Process each result individually to maintain source attribution
        for i, result in enumerate(results[:3]):  # Limit to top 3 per topic
            summary = result.get('summary', '')
            if not summary:
                continue
            
            # Extract domain from URL for source attribution
            url = result.get('url', '')
            domain = self._extract_domain(url)
            
            # Use proper citation number
            citation_num = citation_start + i
            
            # Add source attribution
            summary_with_source = f"* {summary} <#{citation_num}>"
            summary_parts.append(summary_with_source)
        
        return "\n".join(summary_parts)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _create_url_mapping(self, results: List[Dict]) -> Dict[int, str]:
        """Create URL mapping for citations"""
        url_mapping = {}
        
        for i, result in enumerate(results):
            url_mapping[i + 1] = result['url']
        
        logger.info(f"Created URL mapping for {len(url_mapping)} sources")
        return url_mapping
