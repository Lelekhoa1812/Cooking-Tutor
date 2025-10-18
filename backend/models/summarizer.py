import re
import logging
from typing import List, Dict, Tuple
from .llama import NVIDIALLamaClient

logger = logging.getLogger(__name__)

class TextSummarizer:
    def __init__(self):
        try:
            self.llama_client = NVIDIALLamaClient()
        except Exception as e:
            logger.warning(f"Failed to initialize NVIDIA Llama client: {e}")
            self.llama_client = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for summarization"""
        if not text:
            return ""
        
        # Remove common conversation starters and fillers
        conversation_patterns = [
            r'\b(hi|hello|hey|sure|okay|yes|no|thanks|thank you)\b',
            r'\b(here is|this is|let me|i will|i can|i would)\b',
            r'\b(summarize|summary|here\'s|here is)\b',
            r'\b(please|kindly|would you|could you)\b',
            r'\b(um|uh|er|ah|well|so|like|you know)\b'
        ]
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        
        # Remove conversation patterns
        for pattern in conversation_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove extra punctuation and normalize
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key cooking phrases and terms"""
        if not text:
            return []
        
        # Cooking term patterns
        cooking_patterns = [
            r'\b(?:recipe|ingredients?|cooking|baking|roasting|grilling|frying|boiling|steaming)\b',
            r'\b(?:chef|cook|kitchen|cuisine|meal|dish|food|taste|flavor)\b',
            r'\b(?:temperature|timing|preparation|technique|method|seasoning|spices?|herbs?)\b',
            r'\b(?:oven|stovetop|grill|pan|pot|skillet|knife|cutting|chopping)\b',
            r'\b(?:sauce|marinade|dressing|garnish|presentation|serving)\b'
        ]
        
        key_phrases = []
        for pattern in cooking_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_phrases.extend(matches)
        
        return list(set(key_phrases))  # Remove duplicates
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize text using NVIDIA Llama model"""
        if not self.llama_client:
            return self._summarize_fallback(text, max_length)
        
        try:
            if not text or len(text.strip()) < 50:
                return text
            
            # Clean the text first
            cleaned_text = self.clean_text(text)
            
            # Extract key phrases for context
            key_phrases = self.extract_key_phrases(cleaned_text)
            key_phrases_str = ", ".join(key_phrases[:5]) if key_phrases else "cooking information"
            
            # Create optimized prompt
            prompt = f"""Summarize this cooking text in {max_length} characters or less. Focus only on key cooking facts, recipes, techniques, and ingredients. Do not include greetings, confirmations, or conversational elements.

Key terms: {key_phrases_str}

Text: {cleaned_text[:1500]}

Summary:"""

            summary = self.llama_client._call_llama(prompt)
            
            # Post-process summary
            summary = self.clean_text(summary)
            
            # Ensure it's within length limit
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return self._summarize_fallback(text, max_length)
    
    def _summarize_fallback(self, text: str, max_length: int = 200) -> str:
        """Fallback summarization when NVIDIA API is not available"""
        if not text:
            return ""
        
        cleaned_text = self.clean_text(text)
        if len(cleaned_text) <= max_length:
            return cleaned_text
        
        # Simple truncation with sentence boundary detection
        sentences = cleaned_text.split('. ')
        result = ""
        for sentence in sentences:
            if len(result + sentence) > max_length:
                break
            result += sentence + ". "
        
        return result.strip() or cleaned_text[:max_length] + "..."

    def summarize_for_query(self, text: str, query: str, max_length: int = 220) -> str:
        """Summarize text focusing strictly on information relevant to the query.
        Returns an empty string if nothing relevant is found.
        """
        if not self.llama_client:
            return self._summarize_for_query_fallback(text, query, max_length)
        
        try:
            if not text:
                return ""
            cleaned_text = self.clean_text(text)
            if not cleaned_text:
                return ""

            # Short, strict prompt to avoid verbosity; instruct to output NOTHING if irrelevant
            prompt = (
                f"You extract only cooking relevant facts that help answer: '{query}'. "
                f"Respond with a concise bullet list (<= {max_length} chars total). "
                "If the content is irrelevant, respond with EXACTLY: NONE.\n\n"
                f"Content: {cleaned_text[:1600]}\n\nRelevant facts:"
            )

            summary = self.llama_client._call_llama(prompt)
            summary = self.clean_text(summary)
            if not summary or summary.upper().strip() == "NONE":
                return ""
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            return summary
        except Exception as e:
            logger.warning(f"Query-focused summarization failed: {e}")
            return self._summarize_for_query_fallback(text, query, max_length)
    
    def _summarize_for_query_fallback(self, text: str, query: str, max_length: int = 220) -> str:
        """Fallback query-focused summarization when NVIDIA API is not available"""
        if not text:
            return ""
        
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return ""
        
        # Simple keyword matching for relevance
        query_words = set(query.lower().split())
        text_words = set(cleaned_text.lower().split())
        
        # Check if there's any overlap
        overlap = query_words.intersection(text_words)
        if not overlap:
            return ""
        
        # Return first few sentences that contain query words
        sentences = cleaned_text.split('. ')
        relevant_sentences = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if query_words.intersection(sentence_words):
                relevant_sentences.append(sentence)
                if len('. '.join(relevant_sentences)) > max_length:
                    break
        
        result = '. '.join(relevant_sentences)
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
        
        return result
    
    def summarize_documents(self, documents: List[Dict], user_query: str) -> Tuple[str, Dict[int, str]]:
        """Summarize multiple documents with URL mapping"""
        try:
            doc_summaries = []
            url_mapping = {}
            
            for doc in documents:
                doc_id = doc['id']
                url_mapping[doc_id] = doc['url']
                
                # Create focused summary for each document
                summary_prompt = f"""Summarize this cooking document in 2-3 sentences, focusing on information relevant to: "{user_query}"

Document: {doc['title']}
Content: {doc['content'][:800]}

Key cooking information:"""

                summary = self.llama_client._call_llama(summary_prompt)
                summary = self.clean_text(summary)
                
                doc_summaries.append(f"Document {doc_id}: {summary}")
            
            combined_summary = "\n\n".join(doc_summaries)
            return combined_summary, url_mapping
            
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return "", {}
    
    def summarize_conversation_chunk(self, chunk: str) -> str:
        """Summarize a conversation chunk for memory"""
        try:
            if not chunk or len(chunk.strip()) < 30:
                return chunk
            
            cleaned_chunk = self.clean_text(chunk)
            
            prompt = f"""Summarize this cooking conversation in 1-2 sentences. Focus only on cooking facts, recipes, techniques, or ingredients discussed. Remove greetings and conversational elements.

Conversation: {cleaned_chunk[:1000]}

Cooking summary:"""

            summary = self.llama_client._call_llama(prompt)
            return self.clean_text(summary)
            
        except Exception as e:
            logger.error(f"Conversation summarization failed: {e}")
            return self.clean_text(chunk)[:150]
    
    def chunk_response(self, response: str, max_chunk_size: int = 500) -> List[str]:
        """Split response into chunks and summarize each"""
        try:
            if not response or len(response) <= max_chunk_size:
                return [response]
            
            # Split by sentences first
            sentences = re.split(r'[.!?]+', response)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check if adding this sentence would exceed limit
                if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                    chunks.append(self.summarize_conversation_chunk(current_chunk))
                    current_chunk = sentence
                else:
                    current_chunk += sentence + ". "
            
            # Add the last chunk
            if current_chunk:
                chunks.append(self.summarize_conversation_chunk(current_chunk))
            
            return chunks
            
        except Exception as e:
            logger.error(f"Response chunking failed: {e}")
            return [response]

# Global summarizer instance
summarizer = TextSummarizer()

