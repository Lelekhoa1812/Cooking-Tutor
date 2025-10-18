# api/chatbot.py
import re
import logging
from typing import Dict, List
from google import genai
from .config import gemini_flash_api_key
from memory import MemoryManager
from utils import translate_query
from search import search_comprehensive

logger = logging.getLogger("cooking-tutor")

class GeminiClient:
    """Gemini API client for generating responses"""
    
    def __init__(self):
        if not gemini_flash_api_key:
            logger.warning("FlashAPI not set - Gemini client will use fallback responses")
            self.client = None
        else:
            self.client = genai.Client(api_key=gemini_flash_api_key)
    
    def generate_content(self, prompt: str, model: str = "gemini-2.5-flash", temperature: float = 0.7) -> str:
        """Generate content using Gemini API"""
        if not self.client:
            return self._generate_fallback_response(prompt)
        
        try:
            response = self.client.models.generate_content(model=model, contents=prompt)
            return response.text
        except Exception as e:
            logger.error(f"[LLM] ❌ Error calling Gemini API: {e}")
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a simple fallback response when Gemini API is not available"""
        # Extract the user's cooking question from the prompt
        if "User's cooking question:" in prompt:
            question_part = prompt.split("User's cooking question:")[-1].split("\n")[0].strip()
            return f"I'd be happy to help you with your cooking question: '{question_part}'. However, I'm currently unable to access my full cooking knowledge base. Please try again later or contact support."
        else:
            return "I'm a cooking tutor, but I'm currently unable to access my full knowledge base. Please try again later."

class CookingTutorChatbot:
    """Cooking tutor chatbot that uses only web search + memory."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.gemini_client = GeminiClient()
        self.memory = MemoryManager()

    def chat(
        self,
        user_id: str,
        user_query: str,
        lang: str = "EN",
        search_mode: bool = True,
        video_mode: bool = False,
        servings: int = None,
        dietary: list = None,
        allergens: list = None,
        equipment: list = None,
        time_limit_minutes: int = None,
        skill_level: str = None,
        cuisine: str = None,
        structured: bool = False,
    ) -> str:
        # Keep original language for native search - no translation needed
        # The search engines now support native language sources

        # Multilingual cooking relevance check
        cooking_keywords = {
            'en': ['recipe', 'cooking', 'baking', 'food', 'ingredient', 'kitchen', 'chef', 'meal', 'dish', 'cuisine', 'cook', 'bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'season', 'spice', 'herb', 'sauce', 'marinade', 'dressing', 'appetizer', 'main course', 'dessert', 'breakfast', 'lunch', 'dinner'],
            'vi': ['công thức', 'nấu ăn', 'nướng', 'thức ăn', 'nguyên liệu', 'bếp', 'đầu bếp', 'bữa ăn', 'món ăn', 'ẩm thực', 'nấu', 'nướng', 'rang', 'nướng vỉ', 'chiên', 'luộc', 'hấp', 'gia vị', 'thảo mộc', 'nước sốt', 'tẩm ướp', 'khai vị', 'món chính', 'tráng miệng', 'sáng', 'trưa', 'tối', 'bún', 'phở', 'chả', 'nem', 'gỏi', 'canh', 'cháo', 'cơm', 'bánh', 'chè'],
            'zh': ['食谱', '烹饪', '烘焙', '食物', '食材', '厨房', '厨师', '餐', '菜', '菜系', '煮', '烤', '炒', '炸', '蒸', '调料', '香料', '酱汁', '开胃菜', '主菜', '甜点', '早餐', '午餐', '晚餐', '面条', '米饭', '汤', '饺子', '包子']
        }
        
        # Check cooking relevance in multiple languages
        query_lower = user_query.lower()
        is_cooking_related = False
        
        for language, keywords in cooking_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                is_cooking_related = True
                break
        
        if not is_cooking_related:
            logger.warning(f"[SAFETY] Non-cooking query detected: {user_query}")
            return "⚠️ I'm a cooking tutor! Please ask me about recipes, cooking techniques, ingredients, or anything food-related."

        # Conversation memory (recent turns)
        contextual_chunks = self.memory.get_contextual_chunks(user_id, user_query, lang)

        # Web search context
        search_context = ""
        url_mapping = {}
        source_aggregation = {}
        video_results = []

        if search_mode:
            try:
                # Use native language search for better results
                search_context, url_mapping, source_aggregation = search_comprehensive(
                    user_query,  # Use original query without English prefix
                    num_results=12,
                    target_language=lang,
                    include_videos=bool(video_mode),
                    include_images=True  # Always include images for visual appeal
                )
                if video_mode and source_aggregation:
                    video_results = source_aggregation.get('sources', []) or []
            except Exception as e:
                logger.error(f"[SEARCH] Failed: {e}")

        # Build prompt
        parts = [
            "You are a professional cooking tutor and recipe coach.",
            "Provide step-by-step, practical instructions with exact measurements, temperatures, and timings.",
            "Offer substitutions, variations, pantry-friendly swaps, and troubleshooting tips.",
            "Adapt guidance to different skill levels (beginner/intermediate/advanced).",
            "Use Markdown with headings, numbered steps, bullet lists, and short paragraphs.",
            "Always include a concise Ingredients list when relevant.",
            "Cite sources inline using <#ID> tags already present in the search context when applicable.",
        ]

        # Constraints block
        constraints = []
        if servings:
            constraints.append(f"Servings: {servings}")
        if dietary:
            constraints.append(f"Dietary preferences: {', '.join(dietary)}")
        if allergens:
            constraints.append(f"Avoid allergens: {', '.join(allergens)}")
        if equipment:
            constraints.append(f"Available equipment: {', '.join(equipment)}")
        if time_limit_minutes:
            constraints.append(f"Time limit: {time_limit_minutes} minutes")
        if skill_level:
            constraints.append(f"Skill level: {skill_level}")
        if cuisine:
            constraints.append(f"Cuisine: {cuisine}")

        if constraints:
            parts.append("Constraints to respect:\n- " + "\n- ".join(constraints))

        if contextual_chunks:
            parts.append("Relevant context from previous messages:\n" + contextual_chunks)
        if search_context:
            parts.append("Cooking knowledge from the web (with citations):\n" + search_context)

        parts.append(f"User's cooking question: {user_query}")
        parts.append(f"Language to generate answer: {lang}")

        if structured:
            parts.append(
                "Return a Markdown response with these sections if relevant:"
                "\n1. Title"
                "\n2. Summary (2-3 sentences)"
                "\n3. Ingredients (quantities in metric and US units)"
                "\n4. Equipment"
                "\n5. Step-by-step Instructions (numbered)"
                "\n6. Timing & Temperatures"
                "\n7. Variations & Substitutions"
                "\n8. Troubleshooting & Doneness Cues"
                "\n9. Storage & Reheating"
                "\n10. Sources"
            )

        prompt = "\n\n".join(parts)
        response = self.gemini_client.generate_content(prompt, model=self.model_name, temperature=0.6)

        # Process citations
        if url_mapping:
            response = self._process_citations(response, url_mapping)

        # Basic cooking relevance check for response
        if response and len(response) > 50:
            response_lower = response.lower()
            is_cooking_response = False
            
            # Check if response contains cooking keywords in any language
            for language, keywords in cooking_keywords.items():
                if any(keyword in response_lower for keyword in keywords):
                    is_cooking_response = True
                    break
            
            if not is_cooking_response:
                logger.warning(f"[SAFETY] Non-cooking response detected, redirecting to cooking topic")
                response = "⚠️ Let's stick to cooking-related topics. Try asking about recipes, techniques, or ingredients!"

        if user_id:
            self.memory.add_exchange(user_id, user_query, response, lang=lang)

        # Prepare response with media
        response_data = {
            'text': response.strip()
        }
        
        # Add videos if available
        if video_mode and video_results:
            response_data['videos'] = video_results
        
        # Process and integrate images for optimal frontend display
        if source_aggregation and 'images' in source_aggregation:
            images = source_aggregation['images']
            if images:
                # Create enhanced image data with better frontend integration
                enhanced_images = self._enhance_images_for_frontend(images[:3], user_query)
                response_data['images'] = enhanced_images
                
                # Create structured content with image placement suggestions
                structured_content = self._create_structured_content(response.strip(), enhanced_images)
                response_data['structured_content'] = structured_content
                
                # Keep original text for backward compatibility
                response_data['text'] = response.strip()
        
        # Return structured response if we have media, otherwise just text
        if len(response_data) > 1:
            return response_data
        return response.strip()
    
    def _enhance_images_for_frontend(self, images: List[Dict], query: str) -> List[Dict]:
        """Enhance image data for optimal frontend display"""
        enhanced_images = []
        
        for i, image in enumerate(images):
            # Extract key information
            image_url = image.get('url', '')
            title = image.get('title', '')
            source_url = image.get('source_url', '')
            source = image.get('source', 'unknown')
            image_type = image.get('image_type', 'general')
            query_context = image.get('query_context', 'general')
            
            # Set current image type for caption generation
            self._current_image_type = image_type
            
            # Generate contextual alt text and caption
            alt_text = self._generate_image_alt_text(title, query, i)
            caption = self._generate_image_caption(title, query, i)
            
            # Determine image placement context based on image type
            placement_context = self._determine_image_placement_by_type(image_type, query, i)
            
            enhanced_image = {
                'id': f"img_{i+1}",
                'url': image_url,
                'alt_text': alt_text,
                'caption': caption,
                'title': title,
                'source_url': source_url,
                'source': source,
                'placement_context': placement_context,
                'display_order': i + 1,
                'aspect_ratio': '16:9',  # Default, can be detected later
                'loading': 'lazy',  # For performance
                'type': 'cooking_image',
                'image_type': image_type,
                'query_context': query_context
            }
            
            enhanced_images.append(enhanced_image)
        
        return enhanced_images
    
    def _determine_image_placement_by_type(self, image_type: str, query: str, index: int) -> str:
        """Determine image placement based on image type for optimal inline display"""
        if image_type == 'ingredients':
            return 'after_ingredients'
        elif image_type == 'technique':
            return 'after_instructions'
        elif image_type == 'final_dish':
            return 'after_tips'
        else:
            # Fallback to original logic
            return self._determine_image_placement(query, index)
    
    def _generate_image_alt_text(self, title: str, query: str, index: int) -> str:
        """Generate descriptive alt text for accessibility"""
        if title and len(title) > 10:
            return f"Cooking image: {title}"
        
        # Generate based on query context
        query_lower = query.lower()
        if 'recipe' in query_lower or 'cook' in query_lower:
            return f"Recipe demonstration image {index + 1}"
        elif 'ingredient' in query_lower:
            return f"Ingredient showcase image {index + 1}"
        elif 'technique' in query_lower or 'method' in query_lower:
            return f"Cooking technique illustration {index + 1}"
        else:
            return f"Related cooking image {index + 1}"
    
    def _generate_image_caption(self, title: str, query: str, index: int) -> str:
        """Generate contextual caption for the image based on image type"""
        if title and len(title) > 5:
            return title
        
        # Generate contextual captions based on image type
        query_lower = query.lower()
        
        # Check if we have image type information
        image_type = getattr(self, '_current_image_type', 'general')
        
        if image_type == 'ingredients':
            if 'pad thai' in query_lower:
                return "Fresh ingredients for Pad Thai"
            elif 'fusion' in query_lower:
                return "Ingredients for fusion cooking"
            else:
                return f"Fresh ingredients {index + 1}"
        elif image_type == 'technique':
            if 'pad thai' in query_lower:
                return "Pad Thai cooking technique"
            elif 'fusion' in query_lower:
                return "Fusion cooking technique"
            else:
                return f"Cooking technique {index + 1}"
        elif image_type == 'final_dish':
            if 'pad thai' in query_lower:
                return "Completed Pad Thai dish"
            elif 'fusion' in query_lower:
                return "Fusion cooking result"
            else:
                return f"Final dish {index + 1}"
        else:
            # Fallback to original logic
            if 'pad thai' in query_lower:
                return f"Pad Thai cooking example {index + 1}"
            elif 'fusion' in query_lower:
                return f"Fusion cooking inspiration {index + 1}"
            elif 'western' in query_lower:
                return f"Western cooking technique {index + 1}"
            else:
                return f"Related cooking example {index + 1}"
    
    def _determine_image_placement(self, query: str, index: int) -> str:
        """Determine where the image should be placed in the text for optimal inline display"""
        query_lower = query.lower()
        
        # More intelligent placement based on content type and image index
        if index == 0:
            # First image: place early in the content for immediate visual impact
            if any(keyword in query_lower for keyword in ['ingredient', 'ingredients', 'what you need']):
                return 'after_ingredients'
            elif any(keyword in query_lower for keyword in ['technique', 'method', 'how to']):
                return 'after_technique_intro'
            elif any(keyword in query_lower for keyword in ['recipe', 'cook', 'make']):
                return 'after_intro'
            else:
                return 'after_intro'
        elif index == 1:
            # Second image: place in the middle of instructions
            return 'after_instructions'
        elif index == 2:
            # Third image: place after tips or at the end
            return 'after_tips'
        else:
            # Additional images: distribute evenly
            return 'after_instructions'
    
    def _integrate_images_inline(self, text: str, images: List[Dict]) -> str:
        """Integrate images inline with text using placeholders for frontend rendering"""
        if not images:
            return text
        
        # Split text into logical sections
        sections = self._split_text_into_sections(text)
        
        # Insert image placeholders at appropriate positions
        enhanced_text = self._insert_image_placeholders(sections, images)
        
        return enhanced_text
    
    def _split_text_into_sections(self, text: str) -> List[Dict]:
        """Split text into logical sections for image placement"""
        sections = []
        lines = text.split('\n')
        current_section = {'type': 'intro', 'content': '', 'images': []}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section types with more comprehensive patterns
            if any(keyword in line_lower for keyword in [
                'ingredients:', 'ingredient list:', 'what you need:', 'materials:', 
                'you will need:', 'ingredients list:', 'for this recipe:'
            ]):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'type': 'ingredients', 'content': line + '\n', 'images': []}
            elif any(keyword in line_lower for keyword in [
                'instructions:', 'directions:', 'how to cook:', 'steps:', 'method:',
                'cooking steps:', 'preparation:', 'how to make:', 'procedure:'
            ]):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'type': 'instructions', 'content': line + '\n', 'images': []}
            elif any(keyword in line_lower for keyword in [
                'tips:', 'troubleshooting:', 'notes:', 'variations:', 'suggestions:',
                'pro tips:', 'helpful hints:', 'cooking tips:', 'advice:'
            ]):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'type': 'tips', 'content': line + '\n', 'images': []}
            else:
                current_section['content'] += line + '\n'
        
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _insert_image_placeholders(self, sections: List[Dict], images: List[Dict]) -> str:
        """Insert image placeholders at appropriate positions in sections"""
        enhanced_sections = []
        image_index = 0
        
        for section in sections:
            enhanced_sections.append(section['content'])
            
            # Determine if this section should have an image
            should_place_image = False
            if image_index < len(images):
                placement_context = images[image_index]['placement_context']
                
                if (section['type'] == 'ingredients' and placement_context == 'after_ingredients') or \
                   (section['type'] == 'instructions' and placement_context == 'after_instructions') or \
                   (section['type'] == 'tips' and placement_context == 'after_tips') or \
                   (section['type'] == 'intro' and placement_context == 'after_intro'):
                    should_place_image = True
            
            if should_place_image and image_index < len(images):
                image = images[image_index]
                # Insert image placeholder that frontend can replace
                image_placeholder = f"\n\n[IMAGE_PLACEHOLDER:{image['id']}]\n\n"
                enhanced_sections.append(image_placeholder)
                image_index += 1
        
        return ''.join(enhanced_sections)
    
    def _create_structured_content(self, text: str, images: List[Dict]) -> List[Dict]:
        """Create structured content blocks for optimal frontend rendering"""
        if not images:
            return [{'type': 'text', 'content': text}]
        
        # Split text into logical sections
        sections = self._split_text_into_sections(text)
        structured_blocks = []
        
        image_index = 0
        
        for section in sections:
            # Add text section
            structured_blocks.append({
                'type': 'text',
                'content': section['content'].strip(),
                'section_type': section['type']
            })
            
            # Check if we should add an image after this section
            if image_index < len(images):
                image = images[image_index]
                placement_context = image['placement_context']
                
                should_add_image = (
                    (section['type'] == 'ingredients' and placement_context == 'after_ingredients') or
                    (section['type'] == 'instructions' and placement_context == 'after_instructions') or
                    (section['type'] == 'tips' and placement_context == 'after_tips') or
                    (section['type'] == 'intro' and placement_context == 'after_intro')
                )
                
                if should_add_image:
                    structured_blocks.append({
                        'type': 'image',
                        'image_data': image,
                        'placement': 'after_section',
                        'section_type': section['type']
                    })
                    image_index += 1
        
        # Add any remaining images at the end
        while image_index < len(images):
            image = images[image_index]
            structured_blocks.append({
                'type': 'image',
                'image_data': image,
                'placement': 'end'
            })
            image_index += 1
        
        return structured_blocks
    
    def _process_citations(self, response: str, url_mapping: Dict[int, str]) -> str:
        """Replace citation tags with actual URLs, handling various citation formats flexibly"""
        
        # More flexible pattern to match various citation formats
        citation_patterns = [
            r'<#([^>]+)>',           # Standard format: <#1>, <#1,2,3>
            r'<#ID\s*(\d+)>',       # Format: <#ID 1>, <#ID 3>
            r'<#\s*ID\s*(\d+)>',    # Format: <# ID 1>
            r'<#(\d+)>',            # Simple format: <#1>
            r'<#\s*(\d+)\s*>',      # Format with spaces: <# 1 >
        ]
        
        def extract_numeric_id(citation_id: str) -> int:
            """Extract numeric ID from various citation formats"""
            if not citation_id:
                return None
                
            # Remove common prefixes and suffixes
            cleaned = citation_id.strip()
            
            # Handle various formats
            if cleaned.upper().startswith('ID'):
                cleaned = cleaned[2:].strip()
            elif cleaned.startswith('#'):
                cleaned = cleaned[1:].strip()
                if cleaned.upper().startswith('ID'):
                    cleaned = cleaned[2:].strip()
            
            # Remove any remaining non-numeric characters except spaces
            import re
            cleaned = re.sub(r'[^\d\s]', '', cleaned).strip()
            
            # Extract first number found
            numbers = re.findall(r'\d+', cleaned)
            if numbers:
                return int(numbers[0])
            
            # Try direct conversion as fallback
            try:
                return int(cleaned)
            except ValueError:
                return None
        
        def replace_citation(match):
            citation_content = match.group(1)
            # Split by comma and clean up each citation ID
            citation_ids = [id_str.strip() for id_str in citation_content.split(',')]
            
            urls = []
            for citation_id in citation_ids:
                # Extract numeric ID from various formats
                doc_id = extract_numeric_id(citation_id)
                
                if doc_id is not None and doc_id in url_mapping:
                    url = url_mapping[doc_id]
                    urls.append(f'<{url}>')
                    logger.info(f"[CITATION] Replacing <#{citation_id}> with {url}")
                else:
                    if doc_id is None:
                        logger.warning(f"[CITATION] Could not extract numeric ID from: {citation_id}")
                    else:
                        logger.warning(f"[CITATION] No URL mapping found for document ID {doc_id}")
                    urls.append(f'<#{citation_id}>')  # Keep original if URL not found
            
            # Join multiple URLs with spaces
            return ' '.join(urls)
        
        # Process with each pattern
        processed_response = response
        total_citations_processed = 0
        
        for pattern in citation_patterns:
            # Count citations before processing
            citations_found = re.findall(pattern, processed_response)
            if citations_found:
                # Process citations with this pattern
                processed_response = re.sub(pattern, replace_citation, processed_response)
                total_citations_processed += sum(len([id_str.strip() for id_str in citation_content.split(',')]) 
                            for citation_content in citations_found)
                logger.info(f"[CITATION] Processed {len(citations_found)} citation groups with pattern: {pattern}")
        
        # Fallback: Handle any remaining malformed citations
        processed_response = self._handle_malformed_citations(processed_response, url_mapping)
        
        logger.info(f"[CITATION] Total citations processed: {total_citations_processed}, URL mappings available: {len(url_mapping)}")
        return processed_response
    
    def _handle_malformed_citations(self, text: str, url_mapping: Dict[int, str]) -> str:
        """Handle any remaining malformed citations that didn't match our patterns"""
        import re
        
        # Look for any remaining citation-like patterns
        malformed_patterns = [
            r'<#\s*ID\s*\d+\s*>',     # <# ID 1 >
            r'<#\s*ID\s*\d+>',        # <# ID 1>
            r'<#ID\s*\d+\s*>',        # <#ID 1 >
            r'<#\s*\d+\s*ID\s*>',     # <# 1 ID >
            r'<#\s*\d+\s*ID>',        # <# 1 ID>
        ]
        
        def clean_malformed_citation(match):
            citation_text = match.group(0)
            # Extract any number from the citation
            numbers = re.findall(r'\d+', citation_text)
            if numbers:
                doc_id = int(numbers[0])
                if doc_id in url_mapping:
                    url = url_mapping[doc_id]
                    logger.info(f"[CITATION] Fixed malformed citation {citation_text} -> {url}")
                    return f'<{url}>'
                else:
                    logger.warning(f"[CITATION] Malformed citation {citation_text} - no URL mapping for ID {doc_id}")
            else:
                logger.warning(f"[CITATION] Malformed citation {citation_text} - no number found")
            return citation_text  # Keep original if can't fix
        
        for pattern in malformed_patterns:
            text = re.sub(pattern, clean_malformed_citation, text)
        
        return text
