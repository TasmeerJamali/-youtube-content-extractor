"""
Content analysis engine for video classification and metadata processing.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

from app.core.config import get_settings
from app.services.input_processor import ContentType

logger = logging.getLogger(__name__)
settings = get_settings()


class QualityTier(Enum):
    """Quality tiers for content classification."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


@dataclass
class ContentFeatures:
    """Extracted features from video content."""
    title_length: int
    description_length: int
    tag_count: int
    view_to_subscriber_ratio: float
    engagement_rate: float
    content_freshness: float  # 0-1, 1 being newest
    title_quality_score: float
    description_quality_score: float
    channel_authority_score: float
    thumbnail_quality_score: float


@dataclass
class ContentAnalysis:
    """Complete content analysis result."""
    video_id: str
    content_type: ContentType
    quality_tier: QualityTier
    features: ContentFeatures
    topic_tags: List[str]
    sentiment_score: float
    credibility_score: float
    audience_match_score: float
    overall_score: float
    analysis_metadata: Dict[str, Any]


class ContentAnalyzer:
    """
    Advanced content analysis engine for video classification and quality assessment.
    """
    
    def __init__(self):
        self.nlp = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Content quality indicators
        self.quality_keywords = {
            'high': [
                'comprehensive', 'detailed', 'professional', 'expert', 'complete',
                'thorough', 'in-depth', 'masterclass', 'ultimate', 'definitive'
            ],
            'medium': [
                'good', 'solid', 'decent', 'useful', 'helpful', 'practical',
                'simple', 'clear', 'basic', 'introduction'
            ],
            'low': [
                'quick', 'fast', 'brief', 'short', 'easy', 'simple',
                'clickbait', 'shocking', 'unbelievable', 'insane'
            ]
        }
        
        # Spam/low-quality indicators
        self.spam_indicators = [
            'click here', 'subscribe now', 'like and subscribe', 'smash that like',
            'notification bell', 'giveaway', 'free money', 'get rich quick',
            'you won\'t believe', 'shocking truth', 'secret revealed'
        ]
        
        # Authority indicators for channels
        self.authority_indicators = [
            'official', 'verified', 'certified', 'expert', 'professor',
            'phd', 'doctor', 'company', 'organization', 'institution'
        ]
        
        # Content type patterns
        self.content_patterns = {
            ContentType.TUTORIAL: [
                r'how\s+to', r'tutorial', r'guide', r'step\s+by\s+step',
                r'learn', r'teach', r'course', r'lesson'
            ],
            ContentType.REVIEW: [
                r'review', r'unboxing', r'first\s+impression', r'vs\s+',
                r'comparison', r'test', r'opinion', r'thoughts'
            ],
            ContentType.VLOG: [
                r'vlog', r'day\s+in', r'daily', r'routine', r'lifestyle',
                r'behind\s+the\s+scenes', r'update', r'diary'
            ]
        }
        
        # Engagement thresholds
        self.engagement_thresholds = {
            'excellent': 0.05,  # 5% engagement rate
            'good': 0.02,       # 2% engagement rate
            'average': 0.01,    # 1% engagement rate
            'poor': 0.005       # 0.5% engagement rate
        }
    
    async def initialize(self):
        """Initialize NLP models and vectorizers."""
        try:
            self.nlp = spacy.load(settings.spacy_model)
            logger.info("Content analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content analyzer: {e}")
            self.nlp = None
    
    async def analyze_video(
        self,
        video_data: Dict[str, Any],
        channel_data: Optional[Dict[str, Any]] = None
    ) -> ContentAnalysis:
        """
        Perform comprehensive analysis of a video.
        """
        video_id = video_data.get('id', '')
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        
        # Extract basic information
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        tags = snippet.get('tags', [])
        channel_title = snippet.get('channelTitle', '')
        published_at = snippet.get('publishedAt', '')
        
        # Extract statistics
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # Channel statistics
        channel_subscriber_count = 0
        if channel_data:
            channel_stats = channel_data.get('statistics', {})
            channel_subscriber_count = int(channel_stats.get('subscriberCount', 0))
        
        # Content type classification
        content_type = await self._classify_content_type(title, description, tags)
        
        # Extract features
        features = await self._extract_features(
            title, description, tags, channel_title,
            view_count, like_count, comment_count,
            channel_subscriber_count, published_at
        )
        
        # Quality assessment
        quality_tier = await self._assess_quality(features, title, description)
        
        # Topic extraction
        topic_tags = await self._extract_topics(title, description)
        
        # Sentiment analysis
        sentiment_score = await self._analyze_sentiment(title, description)
        
        # Credibility scoring
        credibility_score = await self._calculate_credibility(
            channel_title, features, channel_data
        )
        
        # Audience match scoring (placeholder)
        audience_match_score = 0.8  # Would be based on user preferences
        
        # Overall scoring
        overall_score = await self._calculate_overall_score(
            features, quality_tier, credibility_score, sentiment_score
        )
        
        return ContentAnalysis(
            video_id=video_id,
            content_type=content_type,
            quality_tier=quality_tier,
            features=features,
            topic_tags=topic_tags,
            sentiment_score=sentiment_score,
            credibility_score=credibility_score,
            audience_match_score=audience_match_score,
            overall_score=overall_score,
            analysis_metadata={
                'analyzed_at': datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'processing_time_ms': 0  # Would be calculated in production
            }
        )
    
    async def _classify_content_type(
        self,
        title: str,
        description: str,
        tags: List[str]
    ) -> ContentType:
        """Classify the content type of a video."""
        text = f"{title} {description} {' '.join(tags)}".lower()
        
        type_scores = {}
        
        for content_type, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                type_scores[content_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return ContentType.OTHER
    
    async def _extract_features(
        self,
        title: str,
        description: str,
        tags: List[str],
        channel_title: str,
        view_count: int,
        like_count: int,
        comment_count: int,
        subscriber_count: int,
        published_at: str
    ) -> ContentFeatures:
        """Extract comprehensive features from video metadata."""
        
        # Basic metrics
        title_length = len(title)
        description_length = len(description)
        tag_count = len(tags)
        
        # Engagement metrics
        total_engagement = like_count + comment_count
        engagement_rate = total_engagement / max(view_count, 1)
        
        # View to subscriber ratio
        view_to_subscriber_ratio = view_count / max(subscriber_count, 1)
        
        # Content freshness (based on publish date)
        try:
            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            days_old = (datetime.now(published_date.tzinfo) - published_date).days
            content_freshness = max(0, 1 - (days_old / 365))  # Normalize to 0-1
        except:
            content_freshness = 0.5  # Default if date parsing fails
        
        # Quality scores
        title_quality_score = await self._assess_text_quality(title)
        description_quality_score = await self._assess_text_quality(description)
        
        # Channel authority score
        channel_authority_score = await self._assess_channel_authority(channel_title)
        
        # Placeholder for thumbnail quality (would use image analysis)
        thumbnail_quality_score = 0.7
        
        return ContentFeatures(
            title_length=title_length,
            description_length=description_length,
            tag_count=tag_count,
            view_to_subscriber_ratio=view_to_subscriber_ratio,
            engagement_rate=engagement_rate,
            content_freshness=content_freshness,
            title_quality_score=title_quality_score,
            description_quality_score=description_quality_score,
            channel_authority_score=channel_authority_score,
            thumbnail_quality_score=thumbnail_quality_score
        )
    
    async def _assess_quality(
        self,
        features: ContentFeatures,
        title: str,
        description: str
    ) -> QualityTier:
        """Assess overall content quality tier."""
        quality_score = 0.0
        
        # Title quality (weight: 0.2)
        if features.title_length > 10 and features.title_length < 100:
            quality_score += 0.2 * features.title_quality_score
        
        # Description quality (weight: 0.2)
        if features.description_length > 50:
            quality_score += 0.2 * features.description_quality_score
        
        # Engagement rate (weight: 0.3)
        if features.engagement_rate >= self.engagement_thresholds['excellent']:
            quality_score += 0.3
        elif features.engagement_rate >= self.engagement_thresholds['good']:
            quality_score += 0.25
        elif features.engagement_rate >= self.engagement_thresholds['average']:
            quality_score += 0.15
        else:
            quality_score += 0.05
        
        # Channel authority (weight: 0.15)
        quality_score += 0.15 * features.channel_authority_score
        
        # Content freshness (weight: 0.15)
        quality_score += 0.15 * features.content_freshness
        
        # Determine tier
        if quality_score >= 0.8:
            return QualityTier.EXCELLENT
        elif quality_score >= 0.6:
            return QualityTier.GOOD
        elif quality_score >= 0.4:
            return QualityTier.AVERAGE
        else:
            return QualityTier.POOR
    
    async def _assess_text_quality(self, text: str) -> float:
        """Assess the quality of text content."""
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        text_lower = text.lower()
        
        # Check for quality indicators
        for quality_level, keywords in self.quality_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if quality_level == 'high':
                        score += 0.2
                    elif quality_level == 'medium':
                        score += 0.1
                    else:  # low quality
                        score -= 0.1
        
        # Check for spam indicators
        for indicator in self.spam_indicators:
            if indicator in text_lower:
                score -= 0.2
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.3:
            score -= 0.2
        
        # Check for excessive punctuation
        punct_ratio = sum(1 for c in text if c in '!?') / max(len(text), 1)
        if punct_ratio > 0.05:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _assess_channel_authority(self, channel_title: str) -> float:
        """Assess channel authority based on name and indicators."""
        if not channel_title:
            return 0.3
        
        score = 0.5  # Base score
        channel_lower = channel_title.lower()
        
        # Check for authority indicators
        for indicator in self.authority_indicators:
            if indicator in channel_lower:
                score += 0.2
        
        # Check for professional naming patterns
        if any(word in channel_lower for word in ['tv', 'media', 'news', 'official']):
            score += 0.1
        
        # Penalize obvious spam/clickbait channels
        if any(word in channel_lower for word in ['best', 'top', 'viral', 'amazing']):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _extract_topics(self, title: str, description: str) -> List[str]:
        """Extract topic tags from content."""
        topics = []
        text = f"{title} {description}"
        
        if not self.nlp:
            # Fallback to simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            return list(set(words))[:10]
        
        # Use spaCy for better topic extraction
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG', 'WORK_OF_ART', 'EVENT']:
                topics.append(ent.text.lower())
        
        # Extract important noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 2:
                topics.append(chunk.text.lower())
        
        # Remove duplicates and limit
        unique_topics = list(set(topics))
        return unique_topics[:15]
    
    async def _analyze_sentiment(self, title: str, description: str) -> float:
        """Analyze sentiment of the content."""
        # Simplified sentiment analysis
        # In production, you'd use a proper sentiment analysis model
        
        positive_words = [
            'amazing', 'awesome', 'great', 'excellent', 'fantastic',
            'wonderful', 'perfect', 'incredible', 'outstanding', 'brilliant'
        ]
        
        negative_words = [
            'terrible', 'awful', 'horrible', 'bad', 'worst',
            'disappointing', 'failed', 'disaster', 'nightmare', 'trash'
        ]
        
        text = f"{title} {description}".lower()
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Normalize to -1 to 1 range
        total_words = len(text.split())
        sentiment = (positive_count - negative_count) / max(total_words, 1)
        
        # Convert to 0-1 range (0.5 is neutral)
        return max(0.0, min(1.0, sentiment + 0.5))
    
    async def _calculate_credibility(
        self,
        channel_title: str,
        features: ContentFeatures,
        channel_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate content credibility score."""
        score = 0.5  # Base credibility
        
        # Channel authority contributes to credibility
        score += 0.3 * features.channel_authority_score
        
        # Engagement rate indicates audience trust
        if features.engagement_rate > 0.02:
            score += 0.2
        elif features.engagement_rate > 0.01:
            score += 0.1
        
        # Channel metadata factors
        if channel_data:
            channel_stats = channel_data.get('statistics', {})
            subscriber_count = int(channel_stats.get('subscriberCount', 0))
            
            # Higher subscriber count generally indicates more credibility
            if subscriber_count > 1000000:
                score += 0.2
            elif subscriber_count > 100000:
                score += 0.15
            elif subscriber_count > 10000:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_overall_score(
        self,
        features: ContentFeatures,
        quality_tier: QualityTier,
        credibility_score: float,
        sentiment_score: float
    ) -> float:
        """Calculate overall content score."""
        # Quality tier base score
        quality_scores = {
            QualityTier.EXCELLENT: 0.9,
            QualityTier.GOOD: 0.7,
            QualityTier.AVERAGE: 0.5,
            QualityTier.POOR: 0.3
        }
        
        base_score = quality_scores[quality_tier]
        
        # Adjust based on other factors
        engagement_bonus = min(0.2, features.engagement_rate * 10)  # Max 0.2 bonus
        credibility_bonus = (credibility_score - 0.5) * 0.2  # -0.1 to +0.1
        freshness_bonus = features.content_freshness * 0.1  # Max 0.1 bonus
        
        overall_score = base_score + engagement_bonus + credibility_bonus + freshness_bonus
        
        return max(0.0, min(1.0, overall_score))
    
    async def batch_analyze_videos(
        self,
        videos_data: List[Dict[str, Any]],
        channels_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[ContentAnalysis]:
        """Analyze multiple videos in batch."""
        analyses = []
        
        for video_data in videos_data:
            try:
                channel_id = video_data.get('snippet', {}).get('channelId')
                channel_data = channels_data.get(channel_id) if channels_data else None
                
                analysis = await self.analyze_video(video_data, channel_data)
                analyses.append(analysis)
                
            except Exception as e:
                logger.error(f"Failed to analyze video {video_data.get('id', 'unknown')}: {e}")
                continue
        
        return analyses
    
    async def get_analysis_summary(
        self,
        analyses: List[ContentAnalysis]
    ) -> Dict[str, Any]:
        """Generate summary statistics from multiple analyses."""
        if not analyses:
            return {}
        
        # Content type distribution
        content_types = {}
        for analysis in analyses:
            content_type = analysis.content_type.value
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Quality distribution
        quality_tiers = {}
        for analysis in analyses:
            quality_tier = analysis.quality_tier.value
            quality_tiers[quality_tier] = quality_tiers.get(quality_tier, 0) + 1
        
        # Average scores
        avg_overall_score = sum(a.overall_score for a in analyses) / len(analyses)
        avg_credibility = sum(a.credibility_score for a in analyses) / len(analyses)
        avg_sentiment = sum(a.sentiment_score for a in analyses) / len(analyses)
        
        return {
            'total_analyzed': len(analyses),
            'content_type_distribution': content_types,
            'quality_tier_distribution': quality_tiers,
            'average_scores': {
                'overall': round(avg_overall_score, 3),
                'credibility': round(avg_credibility, 3),
                'sentiment': round(avg_sentiment, 3)
            },
            'top_topics': self._get_top_topics(analyses),
            'quality_insights': self._generate_quality_insights(analyses)
        }
    
    def _get_top_topics(self, analyses: List[ContentAnalysis]) -> List[str]:
        """Get most common topics across analyses."""
        topic_counts = {}
        
        for analysis in analyses:
            for topic in analysis.topic_tags:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by frequency and return top 10
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:10]]
    
    def _generate_quality_insights(self, analyses: List[ContentAnalysis]) -> List[str]:
        """Generate insights about content quality patterns."""
        insights = []
        
        excellent_count = sum(1 for a in analyses if a.quality_tier == QualityTier.EXCELLENT)
        poor_count = sum(1 for a in analyses if a.quality_tier == QualityTier.POOR)
        
        if excellent_count > len(analyses) * 0.3:
            insights.append("High proportion of excellent quality content found")
        
        if poor_count > len(analyses) * 0.3:
            insights.append("Consider filtering out low-quality content")
        
        high_engagement = [a for a in analyses if a.features.engagement_rate > 0.02]
        if high_engagement:
            insights.append(f"{len(high_engagement)} videos have high engagement rates")
        
        return insights


# Global content analyzer instance
content_analyzer = ContentAnalyzer()


async def get_content_analyzer() -> ContentAnalyzer:
    """Get content analyzer instance."""
    if content_analyzer.nlp is None:
        await content_analyzer.initialize()
    return content_analyzer