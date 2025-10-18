# api/retrieval.py
import os
import re
import time
import requests
import numpy as np
import logging
from typing import List, Dict
# Database removed - cooking tutor uses web search only
from models import summarizer

logger = logging.getLogger("retrieval-bot")

class RetrievalEngine:
    def __init__(self):
        # Database removed - cooking tutor uses web search only
        self._reranker = None

    def _get_reranker(self):
        """Initialize the NVIDIA reranker on first use."""
        if self._reranker is None:
            self._reranker = _NvidiaReranker()
        return self._reranker
    
    @staticmethod
    def _is_cooking_guide_text(text: str) -> bool:
        """Heuristic to detect cooking guide content."""
        if not text:
            return False
        keywords = [
            # common cooking guide indicators
            r"\bguideline(s)?\b", r"\bcooking practice\b", r"\brecommend(ation|ed|s)?\b",
            r"\bshould\b", r"\bmust\b", r"\bstrongly (recommend|suggest)\b",
            r"\brecipe\b", r"\btechnique\b", r"\bmethod\b", r"\binstruction\b",
            r"\btemperature\b", r"\btiming\b", r"\bmeasurement\b"
        ]
        text_lc = text.lower()
        return any(re.search(p, text_lc, flags=re.IGNORECASE) for p in keywords)
    
    @staticmethod
    def _extract_cooking_guide_sentences(text: str) -> str:
        """Extract likely cooking guide sentences to reduce conversational/noisy content before summarization."""
        if not text:
            return ""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        keep_patterns = [
            r"\b(recommend|should|must|preferred|first-choice|consider)\b",
            r"\b(temperature|timing|measurement|portion|serving)\b",
            r"\b(ingredient|seasoning|spice|herb|sauce|marinade)\b",
            r"\b(prepare|cook|bake|roast|grill|fry|boil|steam)\b"
        ]
        kept = []
        for s in sentences:
            s_norm = s.strip()
            if not s_norm:
                continue
            if any(re.search(p, s_norm, flags=re.IGNORECASE) for p in keep_patterns):
                kept.append(s_norm)
        # Fallback: if filtering too aggressive, keep truncated original
        if not kept:
            return text[:1200]
        return " ".join(kept)[:2000]
    
    def retrieve_cooking_info(self, query: str, k: int = 5, min_sim: float = 0.8) -> list:
        """
        Retrieve cooking information - placeholder for web search integration
        """
        # This method is kept for compatibility but cooking tutor uses web search
        logger.info(f"[Retrieval] Cooking info retrieval requested for: {query}")
        return [""]
    
    def retrieve_recipe_suggestions(self, ingredient_text: str, top_k: int = 5, min_sim: float = 0.5) -> list:
        """
        Retrieve recipe suggestions from ingredients - placeholder for web search integration
        """
        # This method is kept for compatibility but cooking tutor uses web search
        logger.info(f"[Retrieval] Recipe suggestions requested for ingredients: {ingredient_text}")
        return [""]

# Global retrieval engine instance
retrieval_engine = RetrievalEngine()


class _NvidiaReranker:
    """Simple client for NVIDIA NIM reranking: nvidia/rerank-qa-mistral-4b"""
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_URI")
        # Use provider doc model identifier
        self.model = os.getenv("NVIDIA_RERANK_MODEL", "nv-rerank-qa-mistral-4b:1")
        # NIM rerank endpoint (subject to environment); keep configurable
        self.base_url = os.getenv("NVIDIA_RERANK_ENDPOINT", "https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking")
        self.timeout_s = 30

    def rerank(self, query: str, documents: List[str]) -> List[Dict]:
        if not self.api_key:
            raise ValueError("NVIDIA_URI not set for reranker")
        if not documents:
            return []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Truncate and limit candidates to avoid 4xx
        docs = documents[:10]
        docs = [d[:2000] for d in docs if isinstance(d, str)]
        # Two payload shapes based on provider doc
        payloads = [
            {
                "model": self.model,
                "query": {"text": query},
                "passages": [{"text": d} for d in docs],
            },
            {
                "model": self.model,
                "query": query,
                "documents": [{"text": d} for d in docs],
            },
        ]
        try:
            data = None
            for p in payloads:
                resp = requests.post(self.base_url, headers=headers, json=p, timeout=self.timeout_s)
                if resp.status_code >= 400:
                    # try next shape
                    continue
                data = resp.json()
                break
            if data is None:
                # last attempt for diagnostics
                resp.raise_for_status()
            # Expecting a list with scores and indices or texts
            results = []
            entries = data.get("results") or data.get("data") or []
            if isinstance(entries, list) and entries:
                for entry in entries:
                    # Common patterns: {index, score} or {text, score}
                    idx = entry.get("index")
                    text = entry.get("text") if entry.get("text") else (documents[idx] if idx is not None and idx < len(documents) else None)
                    score = entry.get("score", 0)
                    if text:
                        results.append({"text": text, "score": float(score)})
            else:
                # Fallback: if API returns scores aligned to input order
                scores = data.get("scores")
                if isinstance(scores, list) and len(scores) == len(documents):
                    for t, s in zip(documents, scores):
                        results.append({"text": t, "score": float(s)})
            # Sort by score desc
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results
        except Exception as e:
            logger.warning(f"[Reranker] Failed calling NVIDIA reranker: {e}")
            # On failure, return original order with neutral scores
            return [{"text": d, "score": 0.0} for d in documents]
