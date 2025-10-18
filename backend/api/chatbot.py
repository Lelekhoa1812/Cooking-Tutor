# api/chatbot.py
import re
import logging
from typing import Dict
from google import genai
from .config import gemini_flash_api_key
from memory import MemoryManager
from utils import translate_query
from search import search_comprehensive
# Safety guard removed - cooking tutor doesn't need medical safety checks

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
        # Translate to English-centric search if needed
        if lang.upper() in {"VI", "ZH"}:
            user_query = translate_query(user_query, lang.lower())

        # Basic cooking relevance check
        cooking_keywords = ['recipe', 'cooking', 'baking', 'food', 'ingredient', 'kitchen', 'chef', 'meal', 'dish', 'cuisine', 'cook', 'bake', 'roast', 'grill', 'fry', 'boil', 'steam', 'season', 'spice', 'herb', 'sauce', 'marinade', 'dressing', 'appetizer', 'main course', 'dessert', 'breakfast', 'lunch', 'dinner']
        query_lower = user_query.lower()
        if not any(keyword in query_lower for keyword in cooking_keywords):
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
                search_context, url_mapping, source_aggregation = search_comprehensive(
                    f"cooking technique tutorial: {user_query}",
                    num_results=12,
                    target_language=lang,
                    include_videos=bool(video_mode)
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
            if not any(keyword in response_lower for keyword in cooking_keywords):
                logger.warning(f"[SAFETY] Non-cooking response detected, redirecting to cooking topic")
                response = "⚠️ Let's stick to cooking-related topics. Try asking about recipes, techniques, or ingredients!"

        if user_id:
            self.memory.add_exchange(user_id, user_query, response, lang=lang)

        if video_mode and video_results:
            return {
                'text': response.strip(),
                'videos': video_results
            }
        return response.strip()
    
    def _process_citations(self, response: str, url_mapping: Dict[int, str]) -> str:
        """Replace citation tags with actual URLs, handling both single and multiple references"""
        
        # Pattern to match both single citations <#1> and multiple citations <#1, #2, #5, #7, #9>
        citation_pattern = r'<#([^>]+)>'
        
        def replace_citation(match):
            citation_content = match.group(1)
            # Split by comma and clean up each citation ID
            citation_ids = [id_str.strip() for id_str in citation_content.split(',')]
            
            urls = []
            for citation_id in citation_ids:
                try:
                    doc_id = int(citation_id)
                    if doc_id in url_mapping:
                        url = url_mapping[doc_id]
                        urls.append(f'<{url}>')
                        logger.info(f"[CITATION] Replacing <#{doc_id}> with {url}")
                    else:
                        logger.warning(f"[CITATION] No URL mapping found for document ID {doc_id}")
                        urls.append(f'<#{doc_id}>')  # Keep original if URL not found
                except ValueError:
                    logger.warning(f"[CITATION] Invalid citation ID: {citation_id}")
                    urls.append(f'<#{citation_id}>')  # Keep original if invalid
            
            # Join multiple URLs with spaces
            return ' '.join(urls)
        
        # Replace citations with URLs
        processed_response = re.sub(citation_pattern, replace_citation, response)
        
        # Count total citations processed
        citations_found = re.findall(citation_pattern, response)
        total_citations = sum(len([id_str.strip() for id_str in citation_content.split(',')]) 
                            for citation_content in citations_found)
        
        logger.info(f"[CITATION] Processed {total_citations} citations from {len(citations_found)} citation groups, {len(url_mapping)} URL mappings available")
        return processed_response
