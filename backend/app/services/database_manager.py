"""
Database manager with connection handling and operations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Type, Union
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncpg

from app.core.config import get_settings, get_database_url
from app.models.database import Base, SearchQuery, YouTubeVideo, YouTubeChannel, SearchResult
from app.utils.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    """
    Comprehensive database manager with async support, connection pooling,
    and intelligent caching mechanisms.
    """
    
    def __init__(self):
        self.async_engine = None
        self.sync_engine = None
        self.async_session_factory = None
        self.sync_session_factory = None
        self.cache_manager = None
        self.connected = False
        
        # Connection pool settings
        self.pool_settings = {
            'pool_size': settings.connection_pool_size,
            'max_overflow': settings.max_overflow,
            'pool_pre_ping': True,
            'pool_recycle': 3600,  # 1 hour
        }
    
    async def initialize(self):
        """Initialize database connections and session factories."""
        try:
            database_url = get_database_url()
            
            # Create async engine for main operations
            async_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            self.async_engine = create_async_engine(
                async_url,
                poolclass=QueuePool,
                **self.pool_settings,
                echo=settings.debug
            )
            
            # Create sync engine for migrations and admin operations
            self.sync_engine = create_engine(
                database_url,
                poolclass=QueuePool,
                **self.pool_settings,
                echo=settings.debug
            )
            
            # Create session factories
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                expire_on_commit=False
            )
            
            # Initialize cache manager
            self.cache_manager = await get_cache_manager()
            
            # Test connection
            await self._test_connection()
            
            self.connected = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def _test_connection(self):
        """Test database connectivity."""
        try:
            async with self.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_async_session(self):
        """Get async database session with automatic cleanup."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_sync_session(self):
        """Get sync database session with automatic cleanup."""
        with self.sync_session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                session.close()
    
    # Search Query Operations
    async def save_search_query(
        self,
        original_idea: str,
        processed_keywords: List[str],
        search_parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Save a search query and return its ID."""
        try:
            async with self.get_async_session() as session:
                search_query = SearchQuery(
                    user_id=user_id,
                    original_idea=original_idea,
                    processed_keywords=processed_keywords,
                    search_parameters=search_parameters,
                    status="processing"
                )
                
                session.add(search_query)
                await session.flush()
                await session.refresh(search_query)
                
                query_id = str(search_query.id)
                logger.info(f"Saved search query: {query_id}")
                return query_id
                
        except Exception as e:
            logger.error(f"Failed to save search query: {e}")
            raise
    
    async def update_search_query_status(
        self,
        query_id: str,
        status: str,
        total_results: Optional[int] = None
    ):
        """Update search query status and results count."""
        try:
            async with self.get_async_session() as session:
                result = await session.execute(
                    text("UPDATE search_queries SET status = :status, "
                         "total_results = COALESCE(:total_results, total_results), "
                         "completed_at = CASE WHEN :status = 'completed' THEN NOW() ELSE completed_at END "
                         "WHERE id = :query_id"),
                    {
                        "status": status,
                        "total_results": total_results,
                        "query_id": query_id
                    }
                )
                
                if result.rowcount == 0:
                    logger.warning(f"Search query not found: {query_id}")
                else:
                    logger.info(f"Updated search query {query_id} status to {status}")
                    
        except Exception as e:
            logger.error(f"Failed to update search query status: {e}")
            raise
    
    # Video Operations
    async def save_video_data(
        self,
        video_data: Dict[str, Any],
        channel_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save video data and return video UUID."""
        try:
            async with self.get_async_session() as session:
                # Save or update channel if provided
                channel_uuid = None
                if channel_data:
                    channel_uuid = await self._save_channel_data(session, channel_data)
                
                # Check if video already exists
                existing_video = await session.execute(
                    text("SELECT id FROM youtube_videos WHERE video_id = :video_id"),
                    {"video_id": video_data.get("id")}
                )
                
                video_row = existing_video.fetchone()
                
                if video_row:
                    # Update existing video
                    video_uuid = str(video_row[0])
                    await self._update_video_data(session, video_uuid, video_data, channel_uuid)
                else:
                    # Create new video
                    video_uuid = await self._create_video_data(session, video_data, channel_uuid)
                
                logger.info(f"Saved video data: {video_uuid}")
                return video_uuid
                
        except Exception as e:
            logger.error(f"Failed to save video data: {e}")
            raise
    
    async def _save_channel_data(self, session: AsyncSession, channel_data: Dict[str, Any]) -> str:
        """Save or update channel data."""
        channel_id = channel_data.get("id")
        
        # Check if channel exists
        existing_channel = await session.execute(
            text("SELECT id FROM youtube_channels WHERE channel_id = :channel_id"),
            {"channel_id": channel_id}
        )
        
        channel_row = existing_channel.fetchone()
        
        if channel_row:
            channel_uuid = str(channel_row[0])
            # Update existing channel
            await session.execute(
                text("""
                    UPDATE youtube_channels SET
                        channel_title = :title,
                        subscriber_count = :subscriber_count,
                        video_count = :video_count,
                        view_count = :view_count,
                        description = :description,
                        thumbnail_url = :thumbnail_url,
                        country = :country,
                        last_updated = NOW()
                    WHERE id = :uuid
                """),
                {
                    "uuid": channel_uuid,
                    "title": channel_data.get("snippet", {}).get("title"),
                    "subscriber_count": int(channel_data.get("statistics", {}).get("subscriberCount", 0)),
                    "video_count": int(channel_data.get("statistics", {}).get("videoCount", 0)),
                    "view_count": int(channel_data.get("statistics", {}).get("viewCount", 0)),
                    "description": channel_data.get("snippet", {}).get("description"),
                    "thumbnail_url": channel_data.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url"),
                    "country": channel_data.get("snippet", {}).get("country")
                }
            )
        else:
            # Create new channel
            channel = YouTubeChannel(
                channel_id=channel_id,
                channel_title=channel_data.get("snippet", {}).get("title"),
                subscriber_count=int(channel_data.get("statistics", {}).get("subscriberCount", 0)),
                video_count=int(channel_data.get("statistics", {}).get("videoCount", 0)),
                view_count=int(channel_data.get("statistics", {}).get("viewCount", 0)),
                description=channel_data.get("snippet", {}).get("description"),
                thumbnail_url=channel_data.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url"),
                country=channel_data.get("snippet", {}).get("country")
            )
            
            session.add(channel)
            await session.flush()
            await session.refresh(channel)
            channel_uuid = str(channel.id)
        
        return channel_uuid
    
    async def _create_video_data(
        self,
        session: AsyncSession,
        video_data: Dict[str, Any],
        channel_uuid: Optional[str]
    ) -> str:
        """Create new video record."""
        snippet = video_data.get("snippet", {})
        statistics = video_data.get("statistics", {})
        
        video = YouTubeVideo(
            video_id=video_data.get("id"),
            channel_id=channel_uuid,
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            published_at=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")) if snippet.get("publishedAt") else None,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            language=snippet.get("defaultLanguage"),
            category_id=int(snippet.get("categoryId", 0)) if snippet.get("categoryId") else None,
            tags=snippet.get("tags", [])
        )
        
        session.add(video)
        await session.flush()
        await session.refresh(video)
        
        return str(video.id)
    
    async def _update_video_data(
        self,
        session: AsyncSession,
        video_uuid: str,
        video_data: Dict[str, Any],
        channel_uuid: Optional[str]
    ):
        """Update existing video record."""
        snippet = video_data.get("snippet", {})
        statistics = video_data.get("statistics", {})
        
        await session.execute(
            text("""
                UPDATE youtube_videos SET
                    channel_id = COALESCE(:channel_id, channel_id),
                    title = :title,
                    description = :description,
                    view_count = :view_count,
                    like_count = :like_count,
                    comment_count = :comment_count,
                    thumbnail_url = :thumbnail_url,
                    tags = :tags,
                    last_updated = NOW()
                WHERE id = :uuid
            """),
            {
                "uuid": video_uuid,
                "channel_id": channel_uuid,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "tags": snippet.get("tags", [])
            }
        )
    
    # Search Results Operations
    async def save_search_results(
        self,
        query_id: str,
        results: List[Dict[str, Any]]
    ):
        """Save search results for a query."""
        try:
            async with self.get_async_session() as session:
                # Clear existing results for this query
                await session.execute(
                    text("DELETE FROM search_results WHERE search_query_id = :query_id"),
                    {"query_id": query_id}
                )
                
                # Insert new results
                for rank, result in enumerate(results, 1):
                    search_result = SearchResult(
                        search_query_id=query_id,
                        video_id=result.get("video_uuid"),
                        relevance_score=result.get("relevance_score", 0.0),
                        semantic_similarity=result.get("semantic_similarity"),
                        keyword_match_score=result.get("keyword_match_score"),
                        quality_bonus=result.get("quality_bonus", 0.0),
                        final_rank=rank,
                        match_reasons=result.get("match_reasons")
                    )
                    
                    session.add(search_result)
                
                logger.info(f"Saved {len(results)} search results for query {query_id}")
                
        except Exception as e:
            logger.error(f"Failed to save search results: {e}")
            raise
    
    # Query Operations
    async def get_search_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get search history with optional user filtering."""
        try:
            async with self.get_async_session() as session:
                where_clause = "WHERE user_id = :user_id" if user_id else ""
                
                result = await session.execute(
                    text(f"""
                        SELECT 
                            id, original_idea, status, total_results, 
                            created_at, completed_at
                        FROM search_queries 
                        {where_clause}
                        ORDER BY created_at DESC 
                        LIMIT :limit OFFSET :offset
                    """),
                    {"user_id": user_id, "limit": limit, "offset": offset}
                )
                
                return [
                    {
                        "id": str(row[0]),
                        "original_idea": row[1],
                        "status": row[2],
                        "total_results": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "completed_at": row[5].isoformat() if row[5] else None
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            return []
    
    async def get_trending_content(
        self,
        content_type: Optional[str] = None,
        time_period: int = 7,  # days
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get trending content based on recent search patterns."""
        try:
            async with self.get_async_session() as session:
                content_filter = "AND v.content_type = :content_type" if content_type else ""
                
                result = await session.execute(
                    text(f"""
                        SELECT 
                            v.video_id, v.title, v.view_count, v.engagement_rate,
                            v.quality_score, v.content_type,
                            COUNT(sr.id) as search_frequency
                        FROM youtube_videos v
                        JOIN search_results sr ON v.id = sr.video_id
                        JOIN search_queries sq ON sr.search_query_id = sq.id
                        WHERE sq.created_at >= NOW() - INTERVAL '{time_period} days'
                        {content_filter}
                        GROUP BY v.id, v.video_id, v.title, v.view_count, 
                                v.engagement_rate, v.quality_score, v.content_type
                        ORDER BY search_frequency DESC, v.view_count DESC
                        LIMIT :limit
                    """),
                    {"content_type": content_type, "limit": limit}
                )
                
                return [
                    {
                        "video_id": row[0],
                        "title": row[1],
                        "view_count": row[2],
                        "engagement_rate": float(row[3]) if row[3] else 0.0,
                        "quality_score": float(row[4]) if row[4] else 0.0,
                        "content_type": row[5],
                        "search_frequency": row[6]
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get trending content: {e}")
            return []
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get overall content statistics."""
        try:
            async with self.get_async_session() as session:
                # Total counts
                totals = await session.execute(
                    text("""
                        SELECT 
                            (SELECT COUNT(*) FROM youtube_videos) as total_videos,
                            (SELECT COUNT(*) FROM youtube_channels) as total_channels,
                            (SELECT COUNT(*) FROM search_queries) as total_searches,
                            (SELECT COUNT(*) FROM search_results) as total_results
                    """)
                )
                
                total_row = totals.fetchone()
                
                # Content type distribution
                content_types = await session.execute(
                    text("""
                        SELECT content_type, COUNT(*) 
                        FROM youtube_videos 
                        WHERE content_type IS NOT NULL
                        GROUP BY content_type
                        ORDER BY COUNT(*) DESC
                    """)
                )
                
                # Quality distribution
                quality_dist = await session.execute(
                    text("""
                        SELECT 
                            CASE 
                                WHEN quality_score >= 0.8 THEN 'excellent'
                                WHEN quality_score >= 0.6 THEN 'good'
                                WHEN quality_score >= 0.4 THEN 'average'
                                ELSE 'poor'
                            END as quality_tier,
                            COUNT(*)
                        FROM youtube_videos
                        WHERE quality_score IS NOT NULL
                        GROUP BY quality_tier
                    """)
                )
                
                return {
                    "totals": {
                        "videos": total_row[0],
                        "channels": total_row[1],
                        "searches": total_row[2],
                        "results": total_row[3]
                    },
                    "content_type_distribution": {
                        row[0]: row[1] for row in content_types.fetchall()
                    },
                    "quality_distribution": {
                        row[0]: row[1] for row in quality_dist.fetchall()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get content statistics: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to maintain database performance."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with self.get_async_session() as session:
                # Clean up old search queries and results
                result = await session.execute(
                    text("""
                        DELETE FROM search_queries 
                        WHERE created_at < :cutoff_date 
                        AND status IN ('completed', 'failed')
                    """),
                    {"cutoff_date": cutoff_date}
                )
                
                deleted_queries = result.rowcount
                
                # Clean up old API usage logs
                result = await session.execute(
                    text("""
                        DELETE FROM api_usage_logs 
                        WHERE created_at < :cutoff_date
                    """),
                    {"cutoff_date": cutoff_date}
                )
                
                deleted_logs = result.rowcount
                
                # Clean up expired cache entries
                result = await session.execute(
                    text("""
                        DELETE FROM content_analysis_cache 
                        WHERE expires_at < NOW()
                    """)
                )
                
                deleted_cache = result.rowcount
                
                logger.info(f"Cleanup completed: {deleted_queries} queries, {deleted_logs} logs, {deleted_cache} cache entries")
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
            
            if self.sync_engine:
                self.sync_engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database manager instance
database_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
    """Get database manager instance."""
    if not database_manager.connected:
        await database_manager.initialize()
    return database_manager