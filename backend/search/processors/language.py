import re
import logging
from typing import List, Dict, Tuple, Optional
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0

class LanguageProcessor:
    """Process and enhance queries for multilingual cooking search"""
    
    def __init__(self):
        # Cooking keywords in different languages
        self.cooking_keywords = {
            'en': [
                'recipe', 'cooking', 'baking', 'roasting', 'grilling', 'frying', 'boiling', 'steaming',
                'ingredients', 'seasoning', 'spices', 'herbs', 'sauce', 'marinade', 'dressing',
                'technique', 'method', 'temperature', 'timing', 'preparation', 'cooking time',
                'oven', 'stovetop', 'grill', 'pan', 'pot', 'skillet', 'knife', 'cutting',
                'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', 'diet',
                'appetizer', 'main course', 'dessert', 'breakfast', 'lunch', 'dinner',
                'cuisine', 'italian', 'chinese', 'mexican', 'french', 'indian', 'thai',
                'substitution', 'alternative', 'variation', 'modification', 'adaptation',
                'troubleshooting', 'tips', 'tricks', 'hacks', 'mistakes', 'common errors'
            ],
            'vi': [
                'công thức', 'nấu ăn', 'nướng', 'rang', 'nướng vỉ', 'chiên', 'luộc', 'hấp',
                'nguyên liệu', 'gia vị', 'thảo mộc', 'nước sốt', 'tẩm ướp', 'dressing',
                'kỹ thuật', 'phương pháp', 'nhiệt độ', 'thời gian', 'chuẩn bị', 'thời gian nấu',
                'lò nướng', 'bếp', 'vỉ nướng', 'chảo', 'nồi', 'dao', 'cắt',
                'chay', 'thuần chay', 'không gluten', 'không sữa', 'keto', 'paleo',
                'khai vị', 'món chính', 'tráng miệng', 'sáng', 'trưa', 'tối',
                'ẩm thực', 'ý', 'trung', 'mexico', 'pháp', 'ấn', 'thái',
                'thay thế', 'biến tấu', 'sửa đổi', 'thích ứng',
                'khắc phục', 'mẹo', 'thủ thuật', 'lỗi thường gặp'
            ],
            'zh': [
                '食谱', '烹饪', '烘焙', '烤', '烧烤', '炸', '煮', '蒸',
                '食材', '调料', '香料', '香草', '酱汁', '腌料', '调料',
                '技巧', '方法', '温度', '时间', '准备', '烹饪时间',
                '烤箱', '炉灶', '烤架', '平底锅', '锅', '刀', '切',
                '素食', '纯素', '无麸质', '无乳制品', '生酮', '古法',
                '开胃菜', '主菜', '甜点', '早餐', '午餐', '晚餐',
                '菜系', '意大利', '中国', '墨西哥', '法国', '印度', '泰国',
                '替代', '变化', '修改', '适应',
                '故障排除', '技巧', '窍门', '常见错误'
            ]
        }
        
        # Language-specific search enhancements
        self.language_enhancements = {
            'vi': {
                'common_terms': ['là gì', 'cách nấu', 'công thức', 'nguyên liệu'],
                'cooking_context': ['nấu ăn', 'ẩm thực', 'bếp', 'đầu bếp']
            },
            'zh': {
                'common_terms': ['是什么', '怎么做', '食谱', '食材'],
                'cooking_context': ['烹饪', '美食', '厨房', '厨师']
            },
            'en': {
                'common_terms': ['what is', 'how to cook', 'recipe', 'ingredients'],
                'cooking_context': ['cooking', 'culinary', 'kitchen', 'chef']
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        if not text or not text.strip():
            return 'en'  # Default to English
        
        try:
            # Clean text for better detection
            cleaned_text = re.sub(r'[^\w\s]', ' ', text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            if len(cleaned_text) < 3:
                return 'en'
            
            detected = detect(cleaned_text)
            
            # Map detected language to our supported languages
            language_mapping = {
                'vi': 'vi',  # Vietnamese
                'zh-cn': 'zh',  # Chinese Simplified
                'zh-tw': 'zh',  # Chinese Traditional
                'zh': 'zh',     # Chinese
                'en': 'en'      # English
            }
            
            return language_mapping.get(detected, 'en')
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            return 'en'
    
    def enhance_query(self, query: str, target_language: str = None) -> Dict[str, str]:
        """Enhance query for better search results in multiple languages"""
        if not query or not query.strip():
            return {}
        
        # Detect source language
        source_language = self.detect_language(query)
        
        # If target language not specified, use source language
        if target_language is None:
            target_language = source_language
        
        enhanced_queries = {}
        
        # Original query
        enhanced_queries[source_language] = query
        
        # Enhance for source language
        if source_language in self.language_enhancements:
            enhanced_queries[source_language] = self._enhance_for_language(
                query, source_language
            )
        
        # Create translations for other languages if needed
        if target_language != source_language:
            enhanced_queries[target_language] = self._translate_query(
                query, source_language, target_language
            )
        
        # Add English version for comprehensive search
        if 'en' not in enhanced_queries:
            if source_language != 'en':
                enhanced_queries['en'] = self._translate_query(query, source_language, 'en')
            else:
                enhanced_queries['en'] = query
        
        return enhanced_queries
    
    def _enhance_for_language(self, query: str, language: str) -> str:
        """Enhance query for a specific language"""
        enhancements = self.language_enhancements.get(language, {})
        common_terms = enhancements.get('common_terms', [])
        cooking_context = enhancements.get('cooking_context', [])
        
        # Check if query already contains cooking context
        query_lower = query.lower()
        has_cooking_context = any(term in query_lower for term in cooking_context)
        
        # If no cooking context, add it
        if not has_cooking_context and cooking_context:
            # Add the most relevant cooking context term
            query += f" {cooking_context[0]}"
        
        # Check if query is a question and add relevant terms
        if any(term in query_lower for term in ['là gì', '是什么', 'what is', 'how', 'tại sao', '为什么', 'why']):
            if common_terms:
                query += f" {common_terms[0]}"  # Add "causes" or equivalent
        
        return query.strip()
    
    def _translate_query(self, query: str, source_lang: str, target_lang: str) -> str:
        """Simple keyword-based translation for cooking terms"""
        # This is a basic implementation - in production, you'd use a proper translation service
        
        # Cooking term translations
        translations = {
            ('vi', 'en'): {
                'công thức': 'recipe',
                'nấu ăn': 'cooking',
                'nguyên liệu': 'ingredients',
                'gia vị': 'seasoning',
                'kỹ thuật': 'technique',
                'nướng': 'baking',
                'chiên': 'frying',
                'luộc': 'boiling',
                'hấp': 'steaming',
                'nước sốt': 'sauce'
            },
            ('zh', 'en'): {
                '食谱': 'recipe',
                '烹饪': 'cooking',
                '食材': 'ingredients',
                '调料': 'seasoning',
                '技巧': 'technique',
                '烘焙': 'baking',
                '炸': 'frying',
                '煮': 'boiling',
                '蒸': 'steaming',
                '酱汁': 'sauce'
            },
            ('en', 'vi'): {
                'recipe': 'công thức',
                'cooking': 'nấu ăn',
                'ingredients': 'nguyên liệu',
                'seasoning': 'gia vị',
                'technique': 'kỹ thuật',
                'baking': 'nướng',
                'frying': 'chiên',
                'boiling': 'luộc',
                'steaming': 'hấp',
                'sauce': 'nước sốt'
            },
            ('en', 'zh'): {
                'recipe': '食谱',
                'cooking': '烹饪',
                'ingredients': '食材',
                'seasoning': '调料',
                'technique': '技巧',
                'baking': '烘焙',
                'frying': '炸',
                'boiling': '煮',
                'steaming': '蒸',
                'sauce': '酱汁'
            }
        }
        
        translation_map = translations.get((source_lang, target_lang), {})
        
        # Simple word-by-word translation
        translated_query = query
        for source_term, target_term in translation_map.items():
            translated_query = translated_query.replace(source_term, target_term)
        
        return translated_query
    
    def get_cooking_relevance_score(self, text: str, language: str) -> float:
        """Calculate cooking relevance score for text in a specific language"""
        if not text:
            return 0.0
        
        keywords = self.cooking_keywords.get(language, [])
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Normalize by text length and keyword count
        score = matches / max(len(keywords), 1)
        
        # Boost score for longer matches
        if matches > 0:
            score *= (1 + matches * 0.1)
        
        return min(score, 1.0)
    
    def filter_by_language(self, results: List[Dict], target_language: str) -> List[Dict]:
        """Filter results by language preference"""
        if not results:
            return results
        
        # Score results by language match
        scored_results = []
        for result in results:
            result_language = result.get('language', 'en')
            language_score = 1.0 if result_language == target_language else 0.5
            
            # Add language score to result
            result_copy = result.copy()
            result_copy['language_score'] = language_score
            scored_results.append(result_copy)
        
        # Sort by language score (prefer target language)
        scored_results.sort(key=lambda x: x.get('language_score', 0), reverse=True)
        
        return scored_results
