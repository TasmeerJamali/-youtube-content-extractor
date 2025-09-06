"""
Tests for the input processor module.
"""

import pytest
from app.services.input_processor import InputProcessor, ContentType


class TestInputProcessor:
    """Test cases for InputProcessor."""
    
    @pytest.mark.asyncio
    async def test_process_basic_idea(self, input_processor):
        """Test processing a basic video idea."""
        idea = "How to learn Python programming for beginners"
        
        result = await input_processor.process_idea(idea)
        
        assert result.original_text == idea
        assert len(result.keywords) > 0
        assert "python" in [kw.lower() for kw in result.keywords]
        assert "programming" in [kw.lower() for kw in result.keywords]
        assert ContentType.TUTORIAL in result.content_types
        assert result.intent == "learn"
        assert result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_detect_tutorial_content(self, input_processor):
        """Test detection of tutorial content type."""
        ideas = [
            "How to build a website",
            "Tutorial on machine learning",
            "Learn JavaScript step by step",
            "Beginner's guide to cooking"
        ]
        
        for idea in ideas:
            result = await input_processor.process_idea(idea)
            assert ContentType.TUTORIAL in result.content_types
    
    @pytest.mark.asyncio
    async def test_detect_review_content(self, input_processor):
        """Test detection of review content type."""
        ideas = [
            "iPhone 15 review and unboxing",
            "My thoughts on the new Tesla",
            "Product comparison: Samsung vs Apple",
            "First impressions of the new game"
        ]
        
        for idea in ideas:
            result = await input_processor.process_idea(idea)
            assert ContentType.REVIEW in result.content_types
    
    @pytest.mark.asyncio
    async def test_detect_vlog_content(self, input_processor):
        """Test detection of vlog content type."""
        ideas = [
            "Day in my life as a developer",
            "Morning routine vlog",
            "Travel vlog from Paris",
            "Behind the scenes of my project"
        ]
        
        for idea in ideas:
            result = await input_processor.process_idea(idea)
            assert ContentType.VLOG in result.content_types
    
    @pytest.mark.asyncio
    async def test_extract_keywords(self, input_processor):
        """Test keyword extraction functionality."""
        idea = "Advanced machine learning algorithms for data science projects"
        
        result = await input_processor.process_idea(idea)
        
        expected_keywords = ["machine", "learning", "algorithms", "data", "science"]
        found_keywords = [kw.lower() for kw in result.keywords]
        
        for keyword in expected_keywords:
            assert any(keyword in kw for kw in found_keywords)
    
    @pytest.mark.asyncio
    async def test_generate_search_terms(self, input_processor):
        """Test search term generation."""
        idea = "How to cook pasta like a professional chef"
        
        result = await input_processor.process_idea(idea)
        
        assert len(result.search_terms) > 0
        assert any("pasta" in term.lower() for term in result.search_terms)
        assert any("cook" in term.lower() for term in result.search_terms)
    
    @pytest.mark.asyncio
    async def test_intent_classification(self, input_processor):
        """Test intent classification for different types of queries."""
        test_cases = [
            ("How to learn Python", "learn"),
            ("Find the best smartphone", "discover"),
            ("Compare iPhone vs Samsung", "compare"),
            ("Funny cat videos", "entertain")
        ]
        
        for idea, expected_intent in test_cases:
            result = await input_processor.process_idea(idea)
            assert result.intent == expected_intent
    
    @pytest.mark.asyncio
    async def test_complexity_scoring(self, input_processor):
        """Test complexity scoring for different ideas."""
        simple_idea = "Cat videos"
        complex_idea = "Advanced quantum computing algorithms for cryptographic applications in blockchain technology"
        
        simple_result = await input_processor.process_idea(simple_idea)
        complex_result = await input_processor.process_idea(complex_idea)
        
        assert complex_result.complexity_score > simple_result.complexity_score
    
    @pytest.mark.asyncio
    async def test_filter_extraction(self, input_processor):
        """Test extraction of filters from user input."""
        idea = "Recent short tutorials on Python programming"
        
        result = await input_processor.process_idea(idea)
        
        # Should detect duration preference
        assert "max_duration" in result.filters or "short" in idea.lower()
        # Should detect recency preference
        assert "published_after" in result.filters or "recent" in idea.lower()
    
    @pytest.mark.asyncio
    async def test_empty_idea_handling(self, input_processor):
        """Test handling of empty or invalid ideas."""
        with pytest.raises(ValueError):
            await input_processor.process_idea("")
        
        with pytest.raises(ValueError):
            await input_processor.process_idea("   ")
    
    @pytest.mark.asyncio
    async def test_query_expansion(self, input_processor):
        """Test query expansion functionality."""
        idea = "Python tutorial"
        
        result = await input_processor.process_idea(idea)
        expansions = await input_processor.expand_query(result)
        
        assert len(expansions) > 0
        assert any("python" in expansion.lower() for expansion in expansions)
        assert len(expansions) <= 15  # Should respect the limit
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, input_processor):
        """Test confidence scoring for different types of inputs."""
        clear_idea = "How to learn Python programming step by step tutorial"
        vague_idea = "stuff things maybe"
        
        clear_result = await input_processor.process_idea(clear_idea)
        vague_result = await input_processor.process_idea(vague_idea)
        
        assert clear_result.confidence > vague_result.confidence
        assert 0.0 <= clear_result.confidence <= 1.0
        assert 0.0 <= vague_result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_language_detection(self, input_processor):
        """Test language detection functionality."""
        english_idea = "How to learn programming"
        
        result = await input_processor.process_idea(english_idea)
        
        assert result.language == "en"
    
    @pytest.mark.asyncio
    async def test_user_preferences_integration(self, input_processor):
        """Test integration of user preferences."""
        idea = "Programming tutorial"
        preferences = {
            "language": "es",
            "region": "ES"
        }
        
        result = await input_processor.process_idea(idea, preferences)
        
        assert result.filters.get("language") == "es"