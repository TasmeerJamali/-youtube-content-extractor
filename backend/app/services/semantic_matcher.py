"""
Advanced semantic similarity matching using NLP techniques.
"""

import asyncio
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

from app.core.config import get_settings
from app.utils.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SimilarityMatch:
    """Container for similarity match results."""
    video_id: str
    similarity_score: float
    match_type: str  # 'semantic', 'keyword', 'hybrid'
    match_details: Dict[str, Any]
    confidence: float


@dataclass
class EmbeddingCache:
    """Cache for text embeddings."""
    text_hash: str
    embedding: np.ndarray
    model_version: str
    created_at: datetime


class SemanticMatcher:
    """
    Advanced semantic similarity matching using state-of-the-art NLP techniques.
    Combines sentence transformers, TF-IDF, and spaCy for comprehensive matching.
    """
    
    def __init__(self):
        self.sentence_transformer = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english',
            lowercase=True,
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b'
        )
        self.nlp = None
        self.cache_manager = None
        
        # Model configurations
        self.embedding_model_name = settings.sentence_transformer_model
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        self.similarity_threshold = 0.3  # Minimum similarity score
        
        # Weights for hybrid matching
        self.weights = {
            'semantic': 0.5,      # Sentence transformer similarity
            'keyword': 0.3,       # TF-IDF keyword similarity  
            'structural': 0.2     # Structure-based similarity
        }
        
        # Embedding cache
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.max_cache_size = 1000
    
    async def initialize(self):
        """Initialize all NLP models and components."""
        try:
            # Initialize sentence transformer
            logger.info(f"Loading sentence transformer model: {self.embedding_model_name}")
            self.sentence_transformer = SentenceTransformer(self.embedding_model_name)
            self.embedding_dimension = self.sentence_transformer.get_sentence_embedding_dimension()
            
            # Initialize spaCy
            logger.info(f"Loading spaCy model: {settings.spacy_model}")
            self.nlp = spacy.load(settings.spacy_model)
            
            # Initialize cache manager
            self.cache_manager = await get_cache_manager()
            
            logger.info("Semantic matcher initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic matcher: {e}")
            raise
    
    async def compute_similarity(
        self,
        query_text: str,
        content_items: List[Dict[str, Any]],
        match_fields: List[str] = None,
        use_cache: bool = True
    ) -> List[SimilarityMatch]:
        """
        Compute semantic similarity between query and content items.
        
        Args:
            query_text: User's search query/idea
            content_items: List of video/content items to match against
            match_fields: Fields to use for matching (title, description, etc.)
            use_cache: Whether to use embedding cache
        
        Returns:
            List of similarity matches sorted by score
        """
        if not content_items:
            return []
        
        match_fields = match_fields or ['title', 'description']
        
        # Prepare query embedding
        query_embedding = await self._get_embedding(query_text, use_cache)
        
        # Prepare content embeddings and metadata
        content_data = []
        content_embeddings = []
        
        for item in content_items:
            # Combine text from specified fields
            combined_text = self._combine_text_fields(item, match_fields)
            
            if combined_text.strip():
                content_embedding = await self._get_embedding(combined_text, use_cache)
                content_embeddings.append(content_embedding)
                content_data.append({
                    'item': item,
                    'text': combined_text,
                    'video_id': item.get('video_id', item.get('id', ''))
                })
        
        if not content_embeddings:
            return []
        
        # Compute similarities
        matches = await self._compute_all_similarities(
            query_text,
            query_embedding,
            content_data,
            content_embeddings
        )
        
        # Filter and sort results
        filtered_matches = [
            match for match in matches 
            if match.similarity_score >= self.similarity_threshold
        ]
        
        return sorted(filtered_matches, key=lambda x: x.similarity_score, reverse=True)
    
    async def _get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get text embedding with caching."""
        if not text.strip():
            return np.zeros(self.embedding_dimension)
        
        # Create cache key
        text_hash = str(hash(text.lower().strip()))
        cache_key = f"embedding:{self.embedding_model_name}:{text_hash}"
        
        # Try cache first
        if use_cache and self.cache_manager:
            try:
                cached_embedding = await self.cache_manager.get(cache_key)
                if cached_embedding is not None:
                    return np.array(cached_embedding)
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        # Check in-memory cache
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        # Compute embedding
        try:
            embedding = self.sentence_transformer.encode(
                text, 
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Store in caches
            if use_cache:
                # Store in Redis cache
                if self.cache_manager:
                    try:
                        await self.cache_manager.set(
                            cache_key, 
                            embedding.tolist(), 
                            ttl=86400  # 24 hours
                        )
                    except Exception as e:
                        logger.warning(f"Cache storage failed: {e}")
                
                # Store in memory cache (with size limit)
                if len(self.embedding_cache) >= self.max_cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self.embedding_cache))
                    del self.embedding_cache[oldest_key]
                
                self.embedding_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to compute embedding for text: {e}")
            return np.zeros(self.embedding_dimension)
    
    def _combine_text_fields(self, item: Dict[str, Any], fields: List[str]) -> str:
        """Combine multiple text fields from an item."""
        text_parts = []
        
        for field in fields:
            # Handle nested fields (e.g., 'snippet.title')
            value = item
            for key in field.split('.'):
                if isinstance(value, dict):
                    value = value.get(key, '')
                else:
                    value = ''
                    break
            
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
            elif isinstance(value, list):
                # Handle lists (e.g., tags)
                text_parts.extend([str(v) for v in value if v])
        
        return ' '.join(text_parts)
    
    async def _compute_all_similarities(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        content_data: List[Dict[str, Any]],
        content_embeddings: List[np.ndarray]
    ) -> List[SimilarityMatch]:
        """Compute all types of similarities and combine them."""
        matches = []
        
        # Convert embeddings to matrix for efficient computation
        content_matrix = np.vstack(content_embeddings)
        
        # 1. Semantic similarity (sentence transformers)
        semantic_scores = cosine_similarity(
            query_embedding.reshape(1, -1), 
            content_matrix
        )[0]
        
        # 2. Keyword similarity (TF-IDF)
        keyword_scores = await self._compute_keyword_similarity(
            query_text, 
            [data['text'] for data in content_data]
        )
        
        # 3. Structural similarity (spaCy-based)
        structural_scores = await self._compute_structural_similarity(
            query_text,
            [data['text'] for data in content_data]
        )
        
        # Combine similarities
        for i, data in enumerate(content_data):
            # Weighted combination
            combined_score = (
                self.weights['semantic'] * semantic_scores[i] +
                self.weights['keyword'] * keyword_scores[i] +
                self.weights['structural'] * structural_scores[i]
            )
            
            # Calculate confidence based on score consistency
            score_variance = np.var([
                semantic_scores[i], 
                keyword_scores[i], 
                structural_scores[i]
            ])
            confidence = 1.0 - min(score_variance * 2, 0.5)  # Lower variance = higher confidence
            
            match = SimilarityMatch(
                video_id=data['video_id'],
                similarity_score=float(combined_score),
                match_type='hybrid',
                match_details={
                    'semantic_score': float(semantic_scores[i]),
                    'keyword_score': float(keyword_scores[i]),
                    'structural_score': float(structural_scores[i]),
                    'weights_used': self.weights,
                    'text_length': len(data['text']),
                    'query_length': len(query_text)
                },
                confidence=float(confidence)
            )
            
            matches.append(match)
        
        return matches
    
    async def _compute_keyword_similarity(
        self, 
        query_text: str, 
        content_texts: List[str]
    ) -> np.ndarray:
        """Compute TF-IDF based keyword similarity."""
        try:
            # Prepare texts
            all_texts = [query_text] + content_texts
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Compute similarities
            query_vector = tfidf_matrix[0:1]  # First row is query
            content_vectors = tfidf_matrix[1:]  # Rest are content
            
            similarities = cosine_similarity(query_vector, content_vectors)[0]
            
            return similarities
            
        except Exception as e:
            logger.warning(f"TF-IDF similarity computation failed: {e}")
            return np.zeros(len(content_texts))
    
    async def _compute_structural_similarity(
        self,
        query_text: str,
        content_texts: List[str]
    ) -> np.ndarray:
        """Compute structural similarity using spaCy."""
        if not self.nlp:
            return np.zeros(len(content_texts))
        
        try:
            # Process query
            query_doc = self.nlp(query_text)
            query_features = self._extract_structural_features(query_doc)
            
            similarities = []
            
            for content_text in content_texts:
                try:
                    content_doc = self.nlp(content_text)
                    content_features = self._extract_structural_features(content_doc)
                    
                    # Compute structural similarity
                    similarity = self._compare_structural_features(
                        query_features, 
                        content_features
                    )
                    similarities.append(similarity)
                    
                except Exception as e:
                    logger.warning(f"Structural analysis failed for text: {e}")
                    similarities.append(0.0)
            
            return np.array(similarities)
            
        except Exception as e:
            logger.warning(f"Structural similarity computation failed: {e}")
            return np.zeros(len(content_texts))
    
    def _extract_structural_features(self, doc) -> Dict[str, Any]:
        """Extract structural features from spaCy document."""
        features = {
            'entities': set(),
            'pos_tags': {},
            'dependency_patterns': set(),
            'noun_chunks': set(),
            'key_terms': set()
        }
        
        # Named entities
        for ent in doc.ents:
            features['entities'].add((ent.text.lower(), ent.label_))
        
        # POS tag distribution
        for token in doc:
            pos = token.pos_
            features['pos_tags'][pos] = features['pos_tags'].get(pos, 0) + 1
        
        # Dependency patterns
        for token in doc:
            if token.dep_ != 'ROOT':
                pattern = f"{token.pos_}_{token.dep_}_{token.head.pos_}"
                features['dependency_patterns'].add(pattern)
        
        # Noun chunks
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Limit chunk size
                features['noun_chunks'].add(chunk.text.lower())
        
        # Key terms (important nouns, verbs, adjectives)
        for token in doc:
            if (token.pos_ in ['NOUN', 'VERB', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                features['key_terms'].add(token.lemma_.lower())
        
        return features
    
    def _compare_structural_features(
        self, 
        features1: Dict[str, Any], 
        features2: Dict[str, Any]
    ) -> float:
        """Compare structural features between two documents."""
        total_similarity = 0.0
        weights = {
            'entities': 0.3,
            'key_terms': 0.3,
            'noun_chunks': 0.2,
            'pos_tags': 0.1,
            'dependency_patterns': 0.1
        }
        
        # Entity similarity
        if features1['entities'] or features2['entities']:
            entity_sim = len(features1['entities'] & features2['entities']) / \
                        max(len(features1['entities'] | features2['entities']), 1)
            total_similarity += weights['entities'] * entity_sim
        
        # Key terms similarity
        if features1['key_terms'] or features2['key_terms']:
            terms_sim = len(features1['key_terms'] & features2['key_terms']) / \
                       max(len(features1['key_terms'] | features2['key_terms']), 1)
            total_similarity += weights['key_terms'] * terms_sim
        
        # Noun chunks similarity
        if features1['noun_chunks'] or features2['noun_chunks']:
            chunks_sim = len(features1['noun_chunks'] & features2['noun_chunks']) / \
                        max(len(features1['noun_chunks'] | features2['noun_chunks']), 1)
            total_similarity += weights['noun_chunks'] * chunks_sim
        
        # POS distribution similarity (simplified)
        pos_sim = self._compute_distribution_similarity(
            features1['pos_tags'], 
            features2['pos_tags']
        )
        total_similarity += weights['pos_tags'] * pos_sim
        
        # Dependency pattern similarity
        if features1['dependency_patterns'] or features2['dependency_patterns']:
            dep_sim = len(features1['dependency_patterns'] & features2['dependency_patterns']) / \
                     max(len(features1['dependency_patterns'] | features2['dependency_patterns']), 1)
            total_similarity += weights['dependency_patterns'] * dep_sim
        
        return total_similarity
    
    def _compute_distribution_similarity(
        self, 
        dist1: Dict[str, int], 
        dist2: Dict[str, int]
    ) -> float:
        """Compute similarity between two distributions."""
        all_keys = set(dist1.keys()) | set(dist2.keys())
        
        if not all_keys:
            return 0.0
        
        # Normalize distributions
        total1 = sum(dist1.values()) or 1
        total2 = sum(dist2.values()) or 1
        
        # Compute cosine similarity of normalized distributions
        dot_product = 0.0
        norm1 = norm2 = 0.0
        
        for key in all_keys:
            val1 = dist1.get(key, 0) / total1
            val2 = dist2.get(key, 0) / total2
            
            dot_product += val1 * val2
            norm1 += val1 * val1
            norm2 += val2 * val2
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (np.sqrt(norm1) * np.sqrt(norm2))
    
    async def find_similar_content(
        self,
        reference_content: Dict[str, Any],
        candidate_content: List[Dict[str, Any]],
        similarity_threshold: float = None,
        max_results: int = 10
    ) -> List[SimilarityMatch]:
        """Find content similar to a reference item."""
        threshold = similarity_threshold or self.similarity_threshold
        
        # Extract text from reference content
        reference_text = self._combine_text_fields(
            reference_content, 
            ['title', 'description', 'tags']
        )
        
        # Compute similarities
        matches = await self.compute_similarity(
            reference_text,
            candidate_content,
            match_fields=['title', 'description', 'tags']
        )
        
        # Filter and limit results
        filtered_matches = [
            match for match in matches
            if match.similarity_score >= threshold
        ]
        
        return filtered_matches[:max_results]
    
    async def batch_similarity_computation(
        self,
        query_texts: List[str],
        content_items: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, List[SimilarityMatch]]:
        """Compute similarities for multiple queries in batches."""
        results = {}
        
        # Process content embeddings once
        content_data = []
        content_embeddings = []
        
        for item in content_items:
            combined_text = self._combine_text_fields(item, ['title', 'description'])
            if combined_text.strip():
                content_embedding = await self._get_embedding(combined_text)
                content_embeddings.append(content_embedding)
                content_data.append({
                    'item': item,
                    'text': combined_text,
                    'video_id': item.get('video_id', item.get('id', ''))
                })
        
        # Process queries in batches
        for i in range(0, len(query_texts), batch_size):
            batch_queries = query_texts[i:i + batch_size]
            
            for query in batch_queries:
                query_embedding = await self._get_embedding(query)
                matches = await self._compute_all_similarities(
                    query,
                    query_embedding,
                    content_data,
                    content_embeddings
                )
                
                # Filter results
                filtered_matches = [
                    match for match in matches
                    if match.similarity_score >= self.similarity_threshold
                ]
                
                results[query] = sorted(
                    filtered_matches, 
                    key=lambda x: x.similarity_score, 
                    reverse=True
                )
            
            # Small delay between batches to prevent overload
            await asyncio.sleep(0.1)
        
        return results
    
    async def get_similarity_insights(
        self, 
        matches: List[SimilarityMatch]
    ) -> Dict[str, Any]:
        """Generate insights from similarity results."""
        if not matches:
            return {'total_matches': 0}
        
        # Calculate statistics
        scores = [match.similarity_score for match in matches]
        confidences = [match.confidence for match in matches]
        
        # Analyze match types
        match_types = {}
        for match in matches:
            match_type = match.match_type
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        # Analyze score distribution
        high_quality_matches = [m for m in matches if m.similarity_score >= 0.7]
        medium_quality_matches = [m for m in matches if 0.5 <= m.similarity_score < 0.7]
        low_quality_matches = [m for m in matches if m.similarity_score < 0.5]
        
        return {
            'total_matches': len(matches),
            'score_statistics': {
                'mean': float(np.mean(scores)),
                'median': float(np.median(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            },
            'confidence_statistics': {
                'mean': float(np.mean(confidences)),
                'median': float(np.median(confidences))
            },
            'quality_distribution': {
                'high_quality': len(high_quality_matches),
                'medium_quality': len(medium_quality_matches),
                'low_quality': len(low_quality_matches)
            },
            'match_type_distribution': match_types,
            'top_matches': [
                {
                    'video_id': match.video_id,
                    'score': match.similarity_score,
                    'confidence': match.confidence,
                    'semantic_score': match.match_details.get('semantic_score', 0),
                    'keyword_score': match.match_details.get('keyword_score', 0)
                }
                for match in matches[:5]
            ]
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.embedding_cache.clear()
        logger.info("Semantic matcher cache cleared")


# Global semantic matcher instance
semantic_matcher = SemanticMatcher()


async def get_semantic_matcher() -> SemanticMatcher:
    """Get semantic matcher instance."""
    if semantic_matcher.sentence_transformer is None:
        await semantic_matcher.initialize()
    return semantic_matcher