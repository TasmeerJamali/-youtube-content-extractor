-- Database Schema for YouTube Content Extractor

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
CREATE TYPE content_type_enum AS ENUM (
    'tutorial', 'review', 'vlog', 'animation', 'music', 'gaming', 
    'news', 'comedy', 'documentary', 'educational', 'entertainment', 'other'
);

CREATE TYPE search_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Users table for tracking search history and preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search queries table
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_idea TEXT NOT NULL,
    processed_keywords TEXT[],
    search_parameters JSONB,
    status search_status_enum DEFAULT 'pending',
    total_results INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- YouTube channels table
CREATE TABLE youtube_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id VARCHAR(255) UNIQUE NOT NULL,
    channel_title VARCHAR(255),
    subscriber_count BIGINT,
    video_count INTEGER,
    view_count BIGINT,
    description TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    thumbnail_url VARCHAR(500),
    country VARCHAR(10),
    language VARCHAR(10),
    credibility_score DECIMAL(3,2) DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- YouTube videos table
CREATE TABLE youtube_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id VARCHAR(255) UNIQUE NOT NULL,
    channel_id UUID REFERENCES youtube_channels(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    duration INTEGER, -- in seconds
    view_count BIGINT DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    thumbnail_url VARCHAR(500),
    language VARCHAR(10),
    category_id INTEGER,
    content_type content_type_enum,
    tags TEXT[],
    quality_score DECIMAL(3,2) DEFAULT 0.0,
    engagement_rate DECIMAL(5,4) DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search results table - links queries to videos with relevance scores
CREATE TABLE search_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query_id UUID REFERENCES search_queries(id) ON DELETE CASCADE,
    video_id UUID REFERENCES youtube_videos(id),
    relevance_score DECIMAL(5,4) NOT NULL,
    semantic_similarity DECIMAL(5,4),
    keyword_match_score DECIMAL(5,4),
    quality_bonus DECIMAL(5,4) DEFAULT 0.0,
    final_rank INTEGER,
    match_reasons JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video transcripts table (if available)
CREATE TABLE video_transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES youtube_videos(id) ON DELETE CASCADE,
    transcript_text TEXT,
    language VARCHAR(10),
    auto_generated BOOLEAN DEFAULT false,
    -- processed_embeddings VECTOR(384), -- For semantic search (requires pgvector extension)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content analysis cache
CREATE TABLE content_analysis_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_result JSONB,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(100) NOT NULL,
    quota_used INTEGER DEFAULT 1,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trend analysis data
CREATE TABLE trend_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(255) NOT NULL,
    content_type content_type_enum,
    search_volume INTEGER,
    competition_score DECIMAL(3,2),
    trending_score DECIMAL(5,4),
    time_period DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX idx_search_queries_created_at ON search_queries(created_at DESC);
CREATE INDEX idx_search_queries_status ON search_queries(status);

CREATE INDEX idx_youtube_channels_channel_id ON youtube_channels(channel_id);
CREATE INDEX idx_youtube_channels_credibility ON youtube_channels(credibility_score DESC);

CREATE INDEX idx_youtube_videos_video_id ON youtube_videos(video_id);
CREATE INDEX idx_youtube_videos_channel_id ON youtube_videos(channel_id);
CREATE INDEX idx_youtube_videos_published_at ON youtube_videos(published_at DESC);
CREATE INDEX idx_youtube_videos_view_count ON youtube_videos(view_count DESC);
CREATE INDEX idx_youtube_videos_content_type ON youtube_videos(content_type);
CREATE INDEX idx_youtube_videos_quality_score ON youtube_videos(quality_score DESC);
CREATE INDEX idx_youtube_videos_tags ON youtube_videos USING GIN(tags);

CREATE INDEX idx_search_results_query_id ON search_results(search_query_id);
CREATE INDEX idx_search_results_video_id ON search_results(video_id);
CREATE INDEX idx_search_results_relevance ON search_results(relevance_score DESC);
CREATE INDEX idx_search_results_rank ON search_results(final_rank);

CREATE INDEX idx_video_transcripts_video_id ON video_transcripts(video_id);

CREATE INDEX idx_content_cache_hash ON content_analysis_cache(content_hash);
CREATE INDEX idx_content_cache_expires ON content_analysis_cache(expires_at);

CREATE INDEX idx_api_usage_endpoint ON api_usage_logs(endpoint);
CREATE INDEX idx_api_usage_created_at ON api_usage_logs(created_at DESC);

CREATE INDEX idx_trend_data_keyword ON trend_data(keyword);
CREATE INDEX idx_trend_data_time_period ON trend_data(time_period DESC);

-- Full-text search indexes
CREATE INDEX idx_youtube_videos_title_fts ON youtube_videos USING gin(to_tsvector('english', title));
CREATE INDEX idx_youtube_videos_description_fts ON youtube_videos USING gin(to_tsvector('english', description));

-- Trigram indexes for fuzzy matching
CREATE INDEX idx_youtube_videos_title_trgm ON youtube_videos USING gin(title gin_trgm_ops);

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_youtube_channels_updated_at BEFORE UPDATE ON youtube_channels 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_youtube_videos_updated_at BEFORE UPDATE ON youtube_videos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for calculating engagement rate
CREATE OR REPLACE FUNCTION calculate_engagement_rate(
    likes INTEGER, 
    comments INTEGER, 
    views BIGINT
) RETURNS DECIMAL(5,4) AS $$
BEGIN
    IF views = 0 THEN
        RETURN 0.0;
    END IF;
    RETURN LEAST(((likes + comments * 2.0) / views), 1.0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function for updating video engagement rates
CREATE OR REPLACE FUNCTION update_video_engagement_rate()
RETURNS TRIGGER AS $$
BEGIN
    NEW.engagement_rate = calculate_engagement_rate(
        NEW.like_count, 
        NEW.comment_count, 
        NEW.view_count
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic engagement rate calculation
CREATE TRIGGER update_video_engagement_rate_trigger 
    BEFORE INSERT OR UPDATE OF like_count, comment_count, view_count 
    ON youtube_videos
    FOR EACH ROW EXECUTE FUNCTION update_video_engagement_rate();

-- Insert initial data for content types
INSERT INTO trend_data (keyword, content_type, search_volume, competition_score, trending_score, time_period)
VALUES 
    ('tutorial', 'tutorial', 1000000, 0.8, 0.9, CURRENT_DATE),
    ('review', 'review', 500000, 0.7, 0.8, CURRENT_DATE),
    ('how to', 'tutorial', 800000, 0.9, 0.95, CURRENT_DATE),
    ('unboxing', 'review', 300000, 0.6, 0.7, CURRENT_DATE),
    ('vlog', 'vlog', 200000, 0.5, 0.6, CURRENT_DATE);

-- Create materialized view for popular content
CREATE MATERIALIZED VIEW popular_content_summary AS
SELECT 
    content_type,
    COUNT(*) as video_count,
    AVG(view_count) as avg_views,
    AVG(quality_score) as avg_quality,
    AVG(engagement_rate) as avg_engagement
FROM youtube_videos 
WHERE published_at > NOW() - INTERVAL '30 days'
GROUP BY content_type;

-- Create index on materialized view
CREATE INDEX idx_popular_content_type ON popular_content_summary(content_type);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO youtube_extractor_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO youtube_extractor_user;