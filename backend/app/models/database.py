"""
Database models for YouTube Content Extractor.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User model for tracking search history and preferences."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(100), unique=True, nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")


class SearchQuery(Base):
    """Search queries table."""
    __tablename__ = "search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    original_idea = Column(Text, nullable=False)
    processed_keywords = Column(ARRAY(String), nullable=True)
    search_parameters = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    total_results = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="search_queries")
    search_results = relationship("SearchResult", back_populates="search_query", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_queries_user_id', 'user_id'),
        Index('idx_search_queries_created_at', 'created_at'),
        Index('idx_search_queries_status', 'status'),
    )


class YouTubeChannel(Base):
    """YouTube channels table."""
    __tablename__ = "youtube_channels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(String(255), unique=True, nullable=False)
    channel_title = Column(String(255), nullable=True)
    subscriber_count = Column(Integer, nullable=True)
    video_count = Column(Integer, nullable=True)
    view_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    country = Column(String(10), nullable=True)
    language = Column(String(10), nullable=True)
    credibility_score = Column(Numeric(3, 2), default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    videos = relationship("YouTubeVideo", back_populates="channel")
    
    # Indexes
    __table_args__ = (
        Index('idx_youtube_channels_channel_id', 'channel_id'),
        Index('idx_youtube_channels_credibility', 'credibility_score'),
    )


class YouTubeVideo(Base):
    """YouTube videos table."""
    __tablename__ = "youtube_videos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String(255), unique=True, nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("youtube_channels.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    thumbnail_url = Column(String(500), nullable=True)
    language = Column(String(10), nullable=True)
    category_id = Column(Integer, nullable=True)
    content_type = Column(String(50), nullable=True)  # tutorial, review, vlog, etc.
    tags = Column(ARRAY(String), nullable=True)
    quality_score = Column(Numeric(3, 2), default=0.0)
    engagement_rate = Column(Numeric(5, 4), default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    channel = relationship("YouTubeChannel", back_populates="videos")
    search_results = relationship("SearchResult", back_populates="video")
    transcript = relationship("VideoTranscript", back_populates="video", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_youtube_videos_video_id', 'video_id'),
        Index('idx_youtube_videos_channel_id', 'channel_id'),
        Index('idx_youtube_videos_published_at', 'published_at'),
        Index('idx_youtube_videos_view_count', 'view_count'),
        Index('idx_youtube_videos_content_type', 'content_type'),
        Index('idx_youtube_videos_quality_score', 'quality_score'),
        Index('idx_youtube_videos_tags', 'tags', postgresql_using='gin'),
    )


class SearchResult(Base):
    """Search results table - links queries to videos with relevance scores."""
    __tablename__ = "search_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_query_id = Column(UUID(as_uuid=True), ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(UUID(as_uuid=True), ForeignKey("youtube_videos.id"), nullable=True)
    relevance_score = Column(Numeric(5, 4), nullable=False)
    semantic_similarity = Column(Numeric(5, 4), nullable=True)
    keyword_match_score = Column(Numeric(5, 4), nullable=True)
    quality_bonus = Column(Numeric(5, 4), default=0.0)
    final_rank = Column(Integer, nullable=True)
    match_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    search_query = relationship("SearchQuery", back_populates="search_results")
    video = relationship("YouTubeVideo", back_populates="search_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_results_query_id', 'search_query_id'),
        Index('idx_search_results_video_id', 'video_id'),
        Index('idx_search_results_relevance', 'relevance_score'),
        Index('idx_search_results_rank', 'final_rank'),
    )


class VideoTranscript(Base):
    """Video transcripts table."""
    __tablename__ = "video_transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("youtube_videos.id", ondelete="CASCADE"), nullable=False)
    transcript_text = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    auto_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    video = relationship("YouTubeVideo", back_populates="transcript")
    
    # Indexes
    __table_args__ = (
        Index('idx_video_transcripts_video_id', 'video_id'),
    )


class ContentAnalysisCache(Base):
    """Content analysis cache."""
    __tablename__ = "content_analysis_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = Column(String(64), unique=True, nullable=False)
    analysis_type = Column(String(50), nullable=False)
    analysis_result = Column(JSON, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_content_cache_hash', 'content_hash'),
        Index('idx_content_cache_expires', 'expires_at'),
    )


class APIUsageLog(Base):
    """API usage tracking."""
    __tablename__ = "api_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String(100), nullable=False)
    quota_used = Column(Integer, default=1)
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_api_usage_endpoint', 'endpoint'),
        Index('idx_api_usage_created_at', 'created_at'),
    )


class TrendData(Base):
    """Trend analysis data."""
    __tablename__ = "trend_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=True)
    search_volume = Column(Integer, nullable=True)
    competition_score = Column(Numeric(3, 2), nullable=True)
    trending_score = Column(Numeric(5, 4), nullable=True)
    time_period = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_trend_data_keyword', 'keyword'),
        Index('idx_trend_data_time_period', 'time_period'),
    )