"""
Input processing module for natural language video idea interpretation.
"""

import re
import asyncio
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")


class ContentType(Enum):
    """Enumeration of content types that can be detected."""
    TUTORIAL = "tutorial"
    REVIEW = "review"
    VLOG = "vlog"
    ANIMATION = "animation"
    MUSIC = "music"
    GAMING = "gaming"
    NEWS = "news"
    COMEDY = "comedy"
    DOCUMENTARY = "documentary"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


@dataclass
class ProcessedQuery:
    """Container for processed query information."""
    original_text: str
    keywords: List[str]
    main_topics: List[str]
    content_types: List[ContentType]
    intent: str
    complexity_score: float
    search_terms: List[str]
    filters: Dict[str, Any]
    confidence: float
    language: str


class InputProcessor:
    """
    Advanced natural language processing for video idea interpretation.
    """
    
    def __init__(self):
        self.nlp = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Content type indicators
        self.content_type_keywords = {
            ContentType.TUTORIAL: [
                'tutorial', 'how to', 'guide', 'learn', 'teach', 'step by step',
                'beginner', 'instructions', 'walkthrough', 'demo', 'training',
                'course', 'lesson', 'explain', 'show', 'demonstrate'
            ],
            ContentType.REVIEW: [
                'review', 'opinion', 'thoughts', 'reaction', 'first impressions',
                'unboxing', 'test', 'comparison', 'vs', 'versus', 'critique',
                'analysis', 'breakdown', 'evaluation', 'rating', 'pros and cons'
            ],
            ContentType.VLOG: [
                'vlog', 'daily', 'day in my life', 'routine', 'lifestyle',
                'personal', 'diary', 'blog', 'journey', 'experience',
                'behind the scenes', 'update', 'story time'
            ],
            ContentType.ANIMATION: [
                'animation', 'animated', 'cartoon', 'anime', 'motion graphics',
                '2d', '3d', 'animated story', 'animated movie', 'animated series'
            ],
            ContentType.MUSIC: [
                'music', 'song', 'album', 'artist', 'band', 'concert',
                'performance', 'cover', 'remix', 'instrumental', 'lyrics',
                'music video', 'musical', 'singing', 'guitar', 'piano'
            ],
            ContentType.GAMING: [
                'gaming', 'gameplay', 'let\'s play', 'playthrough', 'speedrun',
                'game review', 'game', 'video game', 'mobile game', 'pc game',
                'console', 'stream', 'twitch', 'esports', 'multiplayer'
            ],
            ContentType.NEWS: [
                'news', 'breaking', 'update', 'current events', 'politics',
                'world news', 'local news', 'report', 'journalism', 'investigation',
                'press conference', 'announcement', 'latest'
            ],
            ContentType.COMEDY: [
                'comedy', 'funny', 'humor', 'jokes', 'stand up', 'sketch',
                'parody', 'satire', 'meme', 'react', 'reaction', 'funny video',
                'comedy show', 'comedian', 'hilarious', 'laugh'
            ],
            ContentType.DOCUMENTARY: [
                'documentary', 'documentary film', 'investigation', 'history',
                'biography', 'true story', 'real life', 'facts', 'research',
                'deep dive', 'exposé', 'investigation', 'science'
            ],
            ContentType.EDUCATIONAL: [
                'educational', 'education', 'school', 'university', 'academic',
                'science', 'math', 'physics', 'chemistry', 'biology',
                'history', 'geography', 'literature', 'study', 'exam'
            ],
            ContentType.ENTERTAINMENT: [
                'entertainment', 'fun', 'viral', 'trending', 'popular',
                'celebrity', 'gossip', 'interview', 'talk show', 'variety show'
            ]
        }
        
        # Intent patterns
        self.intent_patterns = {
            'learn': [
                'how to', 'learn', 'teach me', 'explain', 'tutorial',
                'guide', 'instructions', 'step by step', 'beginner'
            ],
            'discover': [
                'find', 'discover', 'explore', 'search for', 'looking for',
                'recommendations', 'suggest', 'show me', 'what are'
            ],
            'compare': [
                'compare', 'vs', 'versus', 'difference between', 'better',
                'best', 'which', 'pros and cons', 'review'
            ],
            'entertain': [
                'funny', 'entertainment', 'fun', 'watch', 'enjoy',
                'relaxing', 'interesting', 'cool', 'awesome'
            ]
        }
        
        # Quality indicators
        self.quality_indicators = {
            'high': ['professional', 'expert', 'detailed', 'comprehensive', 'thorough'],
            'medium': ['good', 'decent', 'basic', 'simple', 'clear'],
            'low': ['quick', 'fast', 'simple', 'basic', 'short']
        }
        
        # Time-related keywords
        self.time_keywords = {
            'recent': ['recent', 'new', 'latest', 'updated', '2024', '2023'],
            'classic': ['classic', 'old', 'vintage', 'retro', 'throwback'],
            'duration': ['short', 'long', 'quick', 'detailed', 'brief', 'extended']
        }
    
    async def initialize(self):
        """Initialize spaCy model and other resources."""
        try:
            self.nlp = spacy.load(settings.spacy_model)
            logger.info(f"Loaded spaCy model: {settings.spacy_model}")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            # Fallback to basic processing
            self.nlp = None
    
    async def process_idea(self, idea: str, user_preferences: Optional[Dict] = None) -> ProcessedQuery:
        """
        Process a natural language video idea into structured query parameters.
        """
        if not idea or not idea.strip():
            raise ValueError("Empty idea provided")
        
        idea = idea.strip()
        logger.info(f"Processing idea: {idea[:100]}...")
        
        # Basic text cleaning
        cleaned_text = self._clean_text(idea)
        
        # Extract keywords and topics
        keywords = await self._extract_keywords(cleaned_text)
        main_topics = await self._extract_main_topics(cleaned_text)
        
        # Detect content types
        content_types = await self._detect_content_types(cleaned_text)
        
        # Determine intent
        intent = await self._determine_intent(cleaned_text)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(cleaned_text)
        
        # Generate search terms
        search_terms = await self._generate_search_terms(cleaned_text, keywords, main_topics)
        
        # Extract filters
        filters = await self._extract_filters(cleaned_text, user_preferences)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(keywords, content_types, intent)
        
        # Detect language
        language = self._detect_language(cleaned_text)
        
        return ProcessedQuery(
            original_text=idea,
            keywords=keywords,
            main_topics=main_topics,
            content_types=content_types,
            intent=intent,
            complexity_score=complexity_score,
            search_terms=search_terms,
            filters=filters,
            confidence=confidence,
            language=language
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\-\.,\?\!]', '', text)
        
        # Normalize quotes
        text = re.sub(r'[""''`]', '"', text)
        
        return text.strip()
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from the text."""
        keywords = []
        
        # Use spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'WORK_OF_ART', 'EVENT']:
                    keywords.append(ent.text.lower())
            
            # Extract important noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit phrase length
                    keywords.append(chunk.text.lower())
            
            # Extract important tokens
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2):
                    keywords.append(token.lemma_.lower())
        
        # Fallback to NLTK
        else:
            tokens = word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            for word, pos in pos_tags:
                if (pos in ['NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS'] and
                    word not in self.stop_words and
                    len(word) > 2):
                    lemmatized = self.lemmatizer.lemmatize(word)
                    keywords.append(lemmatized)
        
        # Remove duplicates and sort by importance
        keywords = list(set(keywords))
        
        # Score keywords by frequency and position
        keyword_scores = {}
        words = text.lower().split()
        
        for keyword in keywords:
            score = 0
            # Frequency score
            score += text.lower().count(keyword) * 2
            
            # Position score (earlier = more important)
            try:
                first_position = words.index(keyword) if keyword in words else len(words)
                score += max(0, 10 - (first_position / len(words)) * 10)
            except:
                pass
            
            keyword_scores[keyword] = score
        
        # Sort by score and return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, score in sorted_keywords[:20]]  # Top 20 keywords
    
    async def _extract_main_topics(self, text: str) -> List[str]:
        """Extract main topics/themes from the text."""
        topics = []
        text_lower = text.lower()
        
        # Technology topics
        tech_topics = [
            'programming', 'coding', 'software', 'app development', 'web development',
            'artificial intelligence', 'machine learning', 'data science',
            'cybersecurity', 'blockchain', 'cryptocurrency'
        ]
        
        # Creative topics
        creative_topics = [
            'art', 'drawing', 'painting', 'photography', 'design',
            'music production', 'video editing', 'writing', 'creative writing'
        ]
        
        # Lifestyle topics
        lifestyle_topics = [
            'cooking', 'fitness', 'health', 'travel', 'fashion',
            'beauty', 'lifestyle', 'productivity', 'self-improvement'
        ]
        
        # Business topics
        business_topics = [
            'business', 'entrepreneurship', 'marketing', 'sales',
            'finance', 'investing', 'real estate', 'e-commerce'
        ]
        
        # Education topics
        education_topics = [
            'science', 'mathematics', 'physics', 'chemistry', 'biology',
            'history', 'geography', 'language learning', 'literature'
        ]
        
        all_topic_categories = {
            'Technology': tech_topics,
            'Creative': creative_topics,
            'Lifestyle': lifestyle_topics,
            'Business': business_topics,
            'Education': education_topics
        }
        
        for category, topic_list in all_topic_categories.items():
            for topic in topic_list:
                if topic in text_lower or any(word in text_lower for word in topic.split()):
                    topics.append(topic)
        
        return topics[:10]  # Return top 10 topics
    
    async def _detect_content_types(self, text: str) -> List[ContentType]:
        """Detect likely content types based on keywords and patterns."""
        detected_types = []
        text_lower = text.lower()
        
        type_scores = {}
        
        for content_type, keywords in self.content_type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Exact match gets higher score
                    if keyword == text_lower:
                        score += 10
                    # Phrase match
                    elif ' ' in keyword and keyword in text_lower:
                        score += 5
                    # Word match
                    elif keyword in text_lower.split():
                        score += 3
                    # Partial match
                    else:
                        score += 1
            
            if score > 0:
                type_scores[content_type] = score
        
        # Sort by score and return top types
        if type_scores:
            sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            detected_types = [content_type for content_type, score in sorted_types[:3]]
        
        # Default to OTHER if no types detected
        if not detected_types:
            detected_types = [ContentType.OTHER]
        
        return detected_types
    
    async def _determine_intent(self, text: str) -> str:
        """Determine the user's intent from the text."""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += text_lower.count(pattern)
            
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return 'discover'  # Default intent
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score based on text characteristics."""
        score = 0.0
        
        # Length factor
        word_count = len(text.split())
        if word_count > 20:
            score += 0.3
        elif word_count > 10:
            score += 0.2
        else:
            score += 0.1
        
        # Technical terms
        technical_terms = ['api', 'algorithm', 'framework', 'database', 'architecture']
        tech_count = sum(1 for term in technical_terms if term in text.lower())
        score += min(tech_count * 0.1, 0.3)
        
        # Question complexity
        question_words = ['how', 'why', 'what', 'when', 'where', 'which']
        question_count = sum(1 for word in question_words if word in text.lower())
        score += min(question_count * 0.1, 0.2)
        
        # Specificity indicators
        specific_terms = ['advanced', 'detailed', 'comprehensive', 'professional', 'expert']
        specificity = sum(1 for term in specific_terms if term in text.lower())
        score += min(specificity * 0.1, 0.2)
        
        return min(score, 1.0)
    
    async def _generate_search_terms(
        self, 
        text: str, 
        keywords: List[str], 
        topics: List[str]
    ) -> List[str]:
        """Generate optimized search terms for YouTube API."""
        search_terms = []
        
        # Use original text as primary search term
        search_terms.append(text)
        
        # Combine top keywords
        if len(keywords) >= 2:
            search_terms.append(' '.join(keywords[:3]))
        
        # Topic-based searches
        for topic in topics[:2]:
            search_terms.append(topic)
        
        # Generate variations
        for keyword in keywords[:3]:
            # Add "how to" prefix for tutorials
            if any(word in text.lower() for word in ['learn', 'tutorial', 'guide']):
                search_terms.append(f"how to {keyword}")
            
            # Add topic combinations
            for topic in topics[:2]:
                if keyword != topic:
                    search_terms.append(f"{keyword} {topic}")
        
        # Remove duplicates and limit length
        unique_terms = []
        for term in search_terms:
            if term not in unique_terms and len(term) > 3:
                unique_terms.append(term)
        
        return unique_terms[:10]  # Return top 10 search terms
    
    async def _extract_filters(
        self, 
        text: str, 
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Extract filtering criteria from text and user preferences."""
        filters = {}
        text_lower = text.lower()
        
        # Duration filters
        if any(word in text_lower for word in ['short', 'quick', 'brief']):
            filters['max_duration'] = 300  # 5 minutes
        elif any(word in text_lower for word in ['long', 'detailed', 'comprehensive']):
            filters['min_duration'] = 600  # 10 minutes
        
        # Quality filters
        if any(word in text_lower for word in ['professional', 'expert', 'high quality']):
            filters['min_view_count'] = 10000
            filters['min_like_ratio'] = 0.9
        
        # Recency filters
        if any(word in text_lower for word in ['recent', 'new', 'latest', '2024']):
            filters['published_after'] = '2023-01-01'
        elif any(word in text_lower for word in ['classic', 'old', 'vintage']):
            filters['published_before'] = '2020-01-01'
        
        # Language filter
        if user_preferences and 'language' in user_preferences:
            filters['language'] = user_preferences['language']
        
        # Region filter
        if user_preferences and 'region' in user_preferences:
            filters['region'] = user_preferences['region']
        
        return filters
    
    def _calculate_confidence(
        self, 
        keywords: List[str], 
        content_types: List[ContentType], 
        intent: str
    ) -> float:
        """Calculate confidence score for the processed query."""
        confidence = 0.0
        
        # Keyword confidence
        if keywords:
            confidence += min(len(keywords) * 0.05, 0.3)
        
        # Content type confidence
        if content_types and content_types[0] != ContentType.OTHER:
            confidence += 0.3
        
        # Intent confidence
        if intent != 'discover':  # Non-default intent
            confidence += 0.2
        
        # Base confidence
        confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        # Simple language detection based on common words
        # In a production system, you might want to use a proper language detection library
        
        # Check for common English words
        english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        english_count = sum(1 for word in english_indicators if word in text.lower().split())
        
        if english_count >= 2:
            return 'en'
        
        # Add more language detection logic here
        # For now, default to English
        return 'en'
    
    async def expand_query(self, processed_query: ProcessedQuery) -> List[str]:
        """Expand a processed query into multiple search variations."""
        expansions = []
        
        # Original terms
        expansions.extend(processed_query.search_terms)
        
        # Synonym expansion
        synonyms = {
            'tutorial': ['guide', 'walkthrough', 'how-to', 'lesson'],
            'review': ['analysis', 'opinion', 'thoughts', 'critique'],
            'music': ['song', 'audio', 'track', 'sound'],
            'game': ['gaming', 'gameplay', 'playthrough'],
            'cooking': ['recipe', 'food', 'kitchen', 'chef']
        }
        
        for keyword in processed_query.keywords[:5]:
            if keyword in synonyms:
                for synonym in synonyms[keyword]:
                    expansions.append(f"{synonym} {' '.join(processed_query.main_topics[:2])}")
        
        # Content type specific expansions
        for content_type in processed_query.content_types[:2]:
            if content_type != ContentType.OTHER:
                expansions.append(f"{content_type.value} {processed_query.keywords[0]}")
        
        # Remove duplicates
        unique_expansions = list(set(expansions))
        
        return unique_expansions[:15]  # Return top 15 expansions


# Global input processor instance
input_processor = InputProcessor()


async def get_input_processor() -> InputProcessor:
    """Get input processor instance."""
    if input_processor.nlp is None:
        await input_processor.initialize()
    return input_processor