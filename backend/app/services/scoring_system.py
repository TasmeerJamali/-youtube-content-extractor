"""
Advanced relevance scoring and ranking algorithms for YouTube content.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.semantic_matcher import SimilarityMatch
from app.services.content_analyzer import ContentAnalysis, QualityTier
from app.services.input_processor import ProcessedQuery

logger = logging.getLogger(__name__)


class ScoringModel(Enum):
    """Different scoring models available."""
    BALANCED = "balanced"           # Equal weight to all factors
    RELEVANCE_FOCUSED = "relevance"  # Prioritize relevance over quality
    QUALITY_FOCUSED = "quality"     # Prioritize quality over relevance
    ENGAGEMENT_FOCUSED = "engagement"  # Focus on engagement metrics
    FRESHNESS_FOCUSED = "freshness"   # Prioritize recent content


@dataclass
class ScoringWeights:
    """Weights for different scoring factors."""
    semantic_similarity: float = 0.25
    keyword_relevance: float = 0.20
    content_quality: float = 0.20
    engagement_metrics: float = 0.15
    channel_authority: float = 0.10
    content_freshness: float = 0.05
    user_preferences: float = 0.05


@dataclass
class VideoScore:
    """Comprehensive scoring result for a video."""
    video_id: str
    final_score: float
    relevance_score: float
    quality_score: float
    engagement_score: float
    authority_score: float
    freshness_score: float
    preference_score: float
    ranking_position: int
    score_breakdown: Dict[str, float]
    confidence: float
    boost_factors: List[str]
    penalty_factors: List[str]


class AdvancedScoringSystem:
    """
    Advanced multi-factor scoring and ranking system that combines
    semantic relevance, content quality, engagement metrics, and user preferences.
    """
    
    def __init__(self):
        self.scoring_models = {
            ScoringModel.BALANCED: ScoringWeights(),
            ScoringModel.RELEVANCE_FOCUSED: ScoringWeights(
                semantic_similarity=0.35,
                keyword_relevance=0.30,
                content_quality=0.15,
                engagement_metrics=0.10,
                channel_authority=0.05,
                content_freshness=0.03,
                user_preferences=0.02
            ),
            ScoringModel.QUALITY_FOCUSED: ScoringWeights(
                semantic_similarity=0.20,
                keyword_relevance=0.15,
                content_quality=0.35,
                engagement_metrics=0.15,
                channel_authority=0.10,
                content_freshness=0.03,
                user_preferences=0.02
            ),
            ScoringModel.ENGAGEMENT_FOCUSED: ScoringWeights(
                semantic_similarity=0.20,
                keyword_relevance=0.15,
                content_quality=0.15,
                engagement_metrics=0.35,
                channel_authority=0.10,
                content_freshness=0.03,
                user_preferences=0.02
            ),
            ScoringModel.FRESHNESS_FOCUSED: ScoringWeights(
                semantic_similarity=0.25,
                keyword_relevance=0.20,
                content_quality=0.15,
                engagement_metrics=0.15,
                channel_authority=0.05,
                content_freshness=0.15,
                user_preferences=0.05
            )
        }
        
        # Quality tier multipliers
        self.quality_multipliers = {
            QualityTier.EXCELLENT: 1.2,
            QualityTier.GOOD: 1.0,
            QualityTier.AVERAGE: 0.8,
            QualityTier.POOR: 0.6
        }
        
        # Engagement rate thresholds for scoring
        self.engagement_thresholds = {
            'excellent': 0.05,  # 5%
            'good': 0.02,       # 2%
            'average': 0.01,    # 1%
            'poor': 0.005       # 0.5%
        }
        
        # View count normalization factors
        self.view_count_factors = {
            'viral': 10000000,    # 10M+ views
            'popular': 1000000,   # 1M+ views
            'good': 100000,       # 100K+ views
            'average': 10000,     # 10K+ views
            'low': 1000          # 1K+ views
        }
    
    async def score_videos(
        self,
        query: ProcessedQuery,
        videos_data: List[Dict[str, Any]],
        similarity_matches: List[SimilarityMatch],
        content_analyses: List[ContentAnalysis],
        user_preferences: Optional[Dict[str, Any]] = None,
        scoring_model: ScoringModel = ScoringModel.BALANCED
    ) -> List[VideoScore]:
        """
        Score and rank videos based on multiple factors.
        """
        if not videos_data:
            return []
        
        weights = self.scoring_models[scoring_model]
        video_scores = []
        
        # Create lookup dictionaries for efficiency
        similarity_lookup = {match.video_id: match for match in similarity_matches}
        analysis_lookup = {analysis.video_id: analysis for analysis in content_analyses}
        
        for video_data in videos_data:
            video_id = video_data.get('id', video_data.get('video_id', ''))
            
            try:
                score = await self._score_single_video(
                    video_id,
                    video_data,
                    query,
                    similarity_lookup.get(video_id),
                    analysis_lookup.get(video_id),
                    user_preferences,
                    weights
                )
                
                if score:
                    video_scores.append(score)
                    
            except Exception as e:
                logger.warning(f"Failed to score video {video_id}: {e}")
                continue
        
        # Rank videos by final score
        ranked_scores = self._rank_videos(video_scores)
        
        logger.info(f"Scored and ranked {len(ranked_scores)} videos using {scoring_model.value} model")
        return ranked_scores
    
    async def _score_single_video(
        self,
        video_id: str,
        video_data: Dict[str, Any],
        query: ProcessedQuery,
        similarity_match: Optional[SimilarityMatch],
        content_analysis: Optional[ContentAnalysis],
        user_preferences: Optional[Dict[str, Any]],
        weights: ScoringWeights
    ) -> Optional[VideoScore]:
        """Score a single video based on all factors."""
        
        # Extract video metadata
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        published_at = snippet.get('publishedAt', '')
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # 1. Semantic Similarity Score
        semantic_score = 0.0
        if similarity_match:
            semantic_score = similarity_match.similarity_score
        
        # 2. Keyword Relevance Score
        keyword_score = self._calculate_keyword_relevance(
            title, description, query.keywords
        )
        
        # 3. Content Quality Score
        quality_score = 0.5  # Default
        if content_analysis:
            quality_score = content_analysis.overall_score
        
        # 4. Engagement Score
        engagement_score = self._calculate_engagement_score(
            view_count, like_count, comment_count
        )
        
        # 5. Channel Authority Score
        authority_score = 0.5  # Default
        if content_analysis:
            authority_score = content_analysis.credibility_score
        
        # 6. Content Freshness Score
        freshness_score = self._calculate_freshness_score(published_at)
        
        # 7. User Preference Score
        preference_score = self._calculate_preference_score(
            video_data, user_preferences
        )
        
        # Apply quality multiplier
        quality_multiplier = 1.0
        if content_analysis:
            quality_multiplier = self.quality_multipliers.get(
                content_analysis.quality_tier, 1.0
            )
        
        # Calculate weighted final score
        final_score = (
            weights.semantic_similarity * semantic_score +
            weights.keyword_relevance * keyword_score +
            weights.content_quality * quality_score +
            weights.engagement_metrics * engagement_score +
            weights.channel_authority * authority_score +
            weights.content_freshness * freshness_score +
            weights.user_preferences * preference_score
        ) * quality_multiplier
        
        # Apply boost and penalty factors
        boost_factors, penalty_factors = self._calculate_boost_penalty_factors(
            video_data, query, content_analysis
        )
        
        final_score = self._apply_boost_penalty(
            final_score, boost_factors, penalty_factors
        )
        
        # Calculate confidence based on data availability
        confidence = self._calculate_score_confidence(
            similarity_match, content_analysis, statistics
        )
        
        return VideoScore(
            video_id=video_id,
            final_score=max(0.0, min(1.0, final_score)),
            relevance_score=max(semantic_score, keyword_score),
            quality_score=quality_score,
            engagement_score=engagement_score,
            authority_score=authority_score,
            freshness_score=freshness_score,
            preference_score=preference_score,
            ranking_position=0,  # Will be set during ranking
            score_breakdown={
                'semantic': semantic_score,
                'keyword': keyword_score,
                'quality': quality_score,
                'engagement': engagement_score,
                'authority': authority_score,
                'freshness': freshness_score,
                'preference': preference_score,
                'quality_multiplier': quality_multiplier
            },
            confidence=confidence,
            boost_factors=boost_factors,
            penalty_factors=penalty_factors
        )
    
    def _calculate_keyword_relevance(
        self, 
        title: str, 
        description: str, 
        keywords: List[str]
    ) -> float:
        """Calculate keyword relevance score."""
        if not keywords:
            return 0.0
        
        text = f"{title} {description}".lower()
        matched_keywords = 0
        total_matches = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text:
                matched_keywords += 1
                # Count frequency with diminishing returns
                frequency = text.count(keyword_lower)
                total_matches += min(frequency, 3)  # Cap at 3 for each keyword
        
        # Calculate score based on keyword coverage and frequency
        coverage_score = matched_keywords / len(keywords)
        frequency_score = min(total_matches / (len(keywords) * 2), 1.0)
        
        return (coverage_score * 0.7) + (frequency_score * 0.3)
    
    def _calculate_engagement_score(
        self, 
        view_count: int, 
        like_count: int, 
        comment_count: int
    ) -> float:
        """Calculate engagement score based on metrics."""
        if view_count == 0:
            return 0.0
        
        # Calculate engagement rate
        total_engagement = like_count + (comment_count * 2)  # Comments weighted more
        engagement_rate = total_engagement / view_count
        
        # Normalize engagement rate
        if engagement_rate >= self.engagement_thresholds['excellent']:
            return 1.0
        elif engagement_rate >= self.engagement_thresholds['good']:
            return 0.8
        elif engagement_rate >= self.engagement_thresholds['average']:
            return 0.6
        elif engagement_rate >= self.engagement_thresholds['poor']:
            return 0.4
        else:
            return 0.2
    
    def _calculate_freshness_score(self, published_at: str) -> float:
        """Calculate content freshness score."""
        if not published_at:
            return 0.5  # Default for unknown date
        
        try:
            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            days_old = (datetime.now(published_date.tzinfo) - published_date).days
            
            # Decay function: fresher content gets higher scores
            if days_old <= 7:
                return 1.0  # Very fresh
            elif days_old <= 30:
                return 0.8  # Recent
            elif days_old <= 90:
                return 0.6  # Somewhat recent
            elif days_old <= 365:
                return 0.4  # Within a year
            else:
                return 0.2  # Old content
                
        except Exception:
            return 0.5  # Default for parsing errors
    
    def _calculate_preference_score(
        self, 
        video_data: Dict[str, Any], 
        user_preferences: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate user preference matching score."""
        if not user_preferences:
            return 0.5  # Neutral when no preferences
        
        score = 0.5
        snippet = video_data.get('snippet', {})
        
        # Language preference
        if 'language' in user_preferences:
            video_language = snippet.get('defaultLanguage', 'en')
            if video_language == user_preferences['language']:
                score += 0.2
        
        # Content type preference
        if 'preferred_content_types' in user_preferences:
            # This would need content type from analysis
            # For now, use basic heuristics
            title = snippet.get('title', '').lower()
            for content_type in user_preferences['preferred_content_types']:
                if content_type.lower() in title:
                    score += 0.1
        
        # Duration preference
        if 'preferred_duration' in user_preferences:
            # Would need video duration from contentDetails
            pass
        
        # Channel preference
        if 'preferred_channels' in user_preferences:
            channel_id = snippet.get('channelId', '')
            if channel_id in user_preferences['preferred_channels']:
                score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _calculate_boost_penalty_factors(
        self,
        video_data: Dict[str, Any],
        query: ProcessedQuery,
        content_analysis: Optional[ContentAnalysis]
    ) -> Tuple[List[str], List[str]]:
        """Calculate boost and penalty factors."""
        boost_factors = []
        penalty_factors = []
        
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        view_count = int(statistics.get('viewCount', 0))
        
        # Boost factors
        if view_count >= self.view_count_factors['viral']:
            boost_factors.append('viral_content')
        
        if any(keyword.lower() in title for keyword in query.keywords[:3]):
            boost_factors.append('keyword_in_title')
        
        if content_analysis and content_analysis.quality_tier == QualityTier.EXCELLENT:
            boost_factors.append('excellent_quality')
        
        # Check for tutorial indicators if user wants to learn
        if query.intent == 'learn' and any(word in title for word in ['tutorial', 'how to', 'guide']):
            boost_factors.append('tutorial_match')
        
        # Penalty factors
        if view_count < self.view_count_factors['low']:
            penalty_factors.append('low_views')
        
        # Check for clickbait indicators
        clickbait_words = ['shocking', 'unbelievable', 'you won\'t believe', 'insane']
        if any(word in title for word in clickbait_words):
            penalty_factors.append('potential_clickbait')
        
        # Check for excessive caps in title
        if title and sum(1 for c in title if c.isupper()) / len(title) > 0.3:
            penalty_factors.append('excessive_caps')
        
        if content_analysis and content_analysis.quality_tier == QualityTier.POOR:
            penalty_factors.append('poor_quality')
        
        return boost_factors, penalty_factors
    
    def _apply_boost_penalty(
        self, 
        base_score: float, 
        boost_factors: List[str], 
        penalty_factors: List[str]
    ) -> float:
        """Apply boost and penalty factors to the base score."""
        score = base_score
        
        # Apply boosts (multiplicative, but capped)
        boost_multiplier = 1.0
        for factor in boost_factors:
            if factor == 'viral_content':
                boost_multiplier *= 1.1
            elif factor == 'keyword_in_title':
                boost_multiplier *= 1.05
            elif factor == 'excellent_quality':
                boost_multiplier *= 1.08
            elif factor == 'tutorial_match':
                boost_multiplier *= 1.06
        
        # Cap boost at 25%
        boost_multiplier = min(boost_multiplier, 1.25)
        score *= boost_multiplier
        
        # Apply penalties (multiplicative)
        penalty_multiplier = 1.0
        for factor in penalty_factors:
            if factor == 'low_views':
                penalty_multiplier *= 0.9
            elif factor == 'potential_clickbait':
                penalty_multiplier *= 0.85
            elif factor == 'excessive_caps':
                penalty_multiplier *= 0.9
            elif factor == 'poor_quality':
                penalty_multiplier *= 0.8
        
        score *= penalty_multiplier
        
        return score
    
    def _calculate_score_confidence(
        self,
        similarity_match: Optional[SimilarityMatch],
        content_analysis: Optional[ContentAnalysis],
        statistics: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the scoring result."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if we have semantic similarity data
        if similarity_match:
            confidence += 0.2 * similarity_match.confidence
        
        # Higher confidence if we have content analysis
        if content_analysis:
            confidence += 0.2
        
        # Higher confidence if we have engagement statistics
        if statistics.get('viewCount') and statistics.get('likeCount'):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _rank_videos(self, video_scores: List[VideoScore]) -> List[VideoScore]:
        """Rank videos by score and assign positions."""
        # Sort by final score (descending)
        ranked_scores = sorted(
            video_scores, 
            key=lambda x: x.final_score, 
            reverse=True
        )
        
        # Assign ranking positions
        for i, score in enumerate(ranked_scores, 1):
            score.ranking_position = i
        
        return ranked_scores
    
    async def rerank_by_user_feedback(
        self,
        video_scores: List[VideoScore],
        user_feedback: Dict[str, Any]
    ) -> List[VideoScore]:
        """Rerank videos based on user feedback and preferences."""
        # This would implement machine learning-based reranking
        # based on user click patterns, preferences, etc.
        
        # For now, apply simple preference-based adjustments
        for score in video_scores:
            # If user clicked on similar content, boost similar videos
            if 'clicked_videos' in user_feedback:
                # Implementation would analyze similarity to clicked videos
                pass
            
            # If user has content type preferences
            if 'preferred_types' in user_feedback:
                # Boost videos matching preferred types
                pass
        
        # Re-sort after adjustments
        return self._rank_videos(video_scores)
    
    def get_scoring_insights(
        self, 
        video_scores: List[VideoScore]
    ) -> Dict[str, Any]:
        """Generate insights from scoring results."""
        if not video_scores:
            return {'total_videos': 0}
        
        scores = [vs.final_score for vs in video_scores]
        confidences = [vs.confidence for vs in video_scores]
        
        # Score distribution
        high_scores = [s for s in scores if s >= 0.7]
        medium_scores = [s for s in scores if 0.5 <= s < 0.7]
        low_scores = [s for s in scores if s < 0.5]
        
        # Common boost/penalty factors
        all_boosts = []
        all_penalties = []
        for vs in video_scores:
            all_boosts.extend(vs.boost_factors)
            all_penalties.extend(vs.penalty_factors)
        
        boost_counts = {}
        for boost in all_boosts:
            boost_counts[boost] = boost_counts.get(boost, 0) + 1
        
        penalty_counts = {}
        for penalty in all_penalties:
            penalty_counts[penalty] = penalty_counts.get(penalty, 0) + 1
        
        return {
            'total_videos': len(video_scores),
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
            'score_distribution': {
                'high_quality': len(high_scores),
                'medium_quality': len(medium_scores),
                'low_quality': len(low_scores)
            },
            'common_boost_factors': dict(sorted(boost_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'common_penalty_factors': dict(sorted(penalty_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'top_ranked_videos': [
                {
                    'video_id': vs.video_id,
                    'final_score': vs.final_score,
                    'ranking_position': vs.ranking_position,
                    'confidence': vs.confidence
                }
                for vs in video_scores[:10]
            ]
        }


# Global scoring system instance
scoring_system = AdvancedScoringSystem()


def get_scoring_system() -> AdvancedScoringSystem:
    """Get scoring system instance."""
    return scoring_system