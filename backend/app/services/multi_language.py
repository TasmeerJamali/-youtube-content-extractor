"""
Multi-language support and internationalization services.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from app.core.config import get_settings
from app.utils.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class SupportedLanguage(Enum):
    """Supported languages for content discovery."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    DUTCH = "nl"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    ARABIC = "ar"
    HINDI = "hi"
    TURKISH = "tr"


@dataclass
class LanguageConfig:
    """Configuration for a supported language."""
    code: str
    name: str
    native_name: str
    rtl: bool = False  # Right-to-left language
    default_region: str = "US"
    youtube_region_codes: List[str] = None


class MultiLanguageManager:
    """
    Comprehensive multi-language support for global content discovery.
    """
    
    def __init__(self):
        self.cache_manager = None
        
        # Language configurations
        self.language_configs = {
            SupportedLanguage.ENGLISH: LanguageConfig(
                code="en",
                name="English",
                native_name="English",
                default_region="US",
                youtube_region_codes=["US", "GB", "AU", "CA"]
            ),
            SupportedLanguage.SPANISH: LanguageConfig(
                code="es",
                name="Spanish",
                native_name="Español",
                default_region="ES",
                youtube_region_codes=["ES", "MX", "AR", "CO"]
            ),
            SupportedLanguage.FRENCH: LanguageConfig(
                code="fr",
                name="French",
                native_name="Français",
                default_region="FR",
                youtube_region_codes=["FR", "CA", "BE", "CH"]
            ),
            SupportedLanguage.GERMAN: LanguageConfig(
                code="de",
                name="German",
                native_name="Deutsch",
                default_region="DE",
                youtube_region_codes=["DE", "AT", "CH"]
            ),
            SupportedLanguage.ITALIAN: LanguageConfig(
                code="it",
                name="Italian",
                native_name="Italiano",
                default_region="IT",
                youtube_region_codes=["IT"]
            ),
            SupportedLanguage.PORTUGUESE: LanguageConfig(
                code="pt",
                name="Portuguese",
                native_name="Português",
                default_region="BR",
                youtube_region_codes=["BR", "PT"]
            ),
            SupportedLanguage.DUTCH: LanguageConfig(
                code="nl",
                name="Dutch",
                native_name="Nederlands",
                default_region="NL",
                youtube_region_codes=["NL", "BE"]
            ),
            SupportedLanguage.RUSSIAN: LanguageConfig(
                code="ru",
                name="Russian",
                native_name="Русский",
                default_region="RU",
                youtube_region_codes=["RU"]
            ),
            SupportedLanguage.JAPANESE: LanguageConfig(
                code="ja",
                name="Japanese",
                native_name="日本語",
                default_region="JP",
                youtube_region_codes=["JP"]
            ),
            SupportedLanguage.KOREAN: LanguageConfig(
                code="ko",
                name="Korean",
                native_name="한국어",
                default_region="KR",
                youtube_region_codes=["KR"]
            ),
            SupportedLanguage.CHINESE_SIMPLIFIED: LanguageConfig(
                code="zh-CN",
                name="Chinese (Simplified)",
                native_name="简体中文",
                default_region="CN",
                youtube_region_codes=["CN"]
            ),
            SupportedLanguage.CHINESE_TRADITIONAL: LanguageConfig(
                code="zh-TW",
                name="Chinese (Traditional)",
                native_name="繁體中文",
                default_region="TW",
                youtube_region_codes=["TW", "HK"]
            ),
            SupportedLanguage.ARABIC: LanguageConfig(
                code="ar",
                name="Arabic",
                native_name="العربية",
                rtl=True,
                default_region="SA",
                youtube_region_codes=["SA", "AE", "EG"]
            ),
            SupportedLanguage.HINDI: LanguageConfig(
                code="hi",
                name="Hindi",
                native_name="हिन्दी",
                default_region="IN",
                youtube_region_codes=["IN"]
            ),
            SupportedLanguage.TURKISH: LanguageConfig(
                code="tr",
                name="Turkish",
                native_name="Türkçe",
                default_region="TR",
                youtube_region_codes=["TR"]
            )
        }
        
        # Content type translations
        self.content_type_translations = {
            "en": {
                "tutorial": "tutorial",
                "review": "review", 
                "vlog": "vlog",
                "animation": "animation",
                "music": "music",
                "gaming": "gaming",
                "news": "news",
                "comedy": "comedy",
                "documentary": "documentary",
                "educational": "educational"
            },
            "es": {
                "tutorial": "tutorial",
                "review": "reseña",
                "vlog": "vlog", 
                "animation": "animación",
                "music": "música",
                "gaming": "gaming",
                "news": "noticias",
                "comedy": "comedia",
                "documentary": "documental",
                "educational": "educativo"
            },
            "fr": {
                "tutorial": "tutoriel",
                "review": "critique",
                "vlog": "vlog",
                "animation": "animation", 
                "music": "musique",
                "gaming": "gaming",
                "news": "actualités",
                "comedy": "comédie",
                "documentary": "documentaire",
                "educational": "éducatif"
            },
            "de": {
                "tutorial": "anleitung",
                "review": "bewertung",
                "vlog": "vlog",
                "animation": "animation",
                "music": "musik", 
                "gaming": "gaming",
                "news": "nachrichten",
                "comedy": "komödie",
                "documentary": "dokumentation",
                "educational": "bildung"
            },
            "ja": {
                "tutorial": "チュートリアル",
                "review": "レビュー",
                "vlog": "ブログ",
                "animation": "アニメーション",
                "music": "音楽",
                "gaming": "ゲーム",
                "news": "ニュース", 
                "comedy": "コメディ",
                "documentary": "ドキュメンタリー",
                "educational": "教育"
            },
            "ko": {
                "tutorial": "튜토리얼",
                "review": "리뷰",
                "vlog": "브이로그",
                "animation": "애니메이션",
                "music": "음악",
                "gaming": "게임",
                "news": "뉴스",
                "comedy": "코미디", 
                "documentary": "다큐멘터리",
                "educational": "교육"
            }
        }
        
        # Common search terms in different languages
        self.common_search_terms = {
            "en": {
                "how_to": ["how to", "tutorial", "guide", "learn", "step by step"],
                "review": ["review", "opinion", "thoughts", "first impressions"],
                "best": ["best", "top", "greatest", "finest", "recommended"]
            },
            "es": {
                "how_to": ["como", "tutorial", "guía", "aprender", "paso a paso"],
                "review": ["reseña", "opinión", "review", "primeras impresiones"],
                "best": ["mejor", "mejores", "top", "recomendado"]
            },
            "fr": {
                "how_to": ["comment", "tutoriel", "guide", "apprendre", "étape par étape"],
                "review": ["critique", "avis", "opinion", "premières impressions"],
                "best": ["meilleur", "meilleurs", "top", "recommandé"]
            },
            "de": {
                "how_to": ["wie", "anleitung", "tutorial", "lernen", "schritt für schritt"],
                "review": ["bewertung", "meinung", "test", "erste eindrücke"],
                "best": ["beste", "besten", "top", "empfohlen"]
            },
            "ja": {
                "how_to": ["方法", "やり方", "チュートリアル", "学ぶ", "ステップ"],
                "review": ["レビュー", "評価", "感想", "第一印象"],
                "best": ["最高", "ベスト", "おすすめ", "人気"]
            },
            "ko": {
                "how_to": ["방법", "하는법", "튜토리얼", "배우기", "단계별"],
                "review": ["리뷰", "평가", "후기", "첫인상"],
                "best": ["최고", "베스트", "추천", "인기"]
            }
        }
    
    async def initialize(self):
        """Initialize multi-language manager."""
        try:
            self.cache_manager = await get_cache_manager()
            logger.info("Multi-language manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multi-language manager: {e}")
            raise
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages."""
        return [
            {
                "code": config.code,
                "name": config.name,
                "native_name": config.native_name,
                "rtl": config.rtl,
                "default_region": config.default_region
            }
            for config in self.language_configs.values()
        ]
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text (simplified)."""
        # This is a basic implementation
        # In production, you'd use a proper language detection library
        
        text_lower = text.lower()
        
        # Check for language-specific patterns
        language_indicators = {
            "es": ["como", "que", "es", "el", "la", "de", "y", "a", "en", "un"],
            "fr": ["comme", "que", "est", "le", "la", "de", "et", "à", "dans", "un"],
            "de": ["wie", "das", "ist", "der", "die", "und", "zu", "in", "ein", "mit"],
            "ja": ["の", "に", "は", "を", "が", "と", "で", "から", "まで"],
            "ko": ["의", "에", "는", "을", "가", "와", "로", "부터", "까지"],
            "zh": ["的", "在", "是", "和", "与", "从", "到", "这", "那"],
            "ar": ["في", "من", "على", "إلى", "هذا", "التي", "التي"],
            "hi": ["में", "से", "पर", "के", "और", "यह", "वह"],
            "ru": ["в", "на", "с", "к", "и", "это", "то", "для"],
            "pt": ["como", "que", "é", "o", "a", "de", "e", "em", "um"],
            "it": ["come", "che", "è", "il", "la", "di", "e", "in", "un"],
            "nl": ["hoe", "dat", "is", "de", "het", "van", "en", "in", "een"],
            "tr": ["nasıl", "ki", "bu", "bir", "ve", "ile", "için"]
        }
        
        scores = {}
        words = text_lower.split()
        
        for lang, indicators in language_indicators.items():
            score = sum(1 for word in words if word in indicators)
            if score > 0:
                scores[lang] = score / len(words)
        
        if scores:
            detected_lang = max(scores.items(), key=lambda x: x[1])[0]
            return detected_lang
        
        return "en"  # Default to English
    
    async def translate_content_types(
        self, 
        content_types: List[str], 
        target_language: str
    ) -> List[str]:
        """Translate content types to target language."""
        translations = self.content_type_translations.get(target_language, {})
        
        if not translations:
            return content_types  # Return original if no translations available
        
        translated = []
        for content_type in content_types:
            translated_type = translations.get(content_type.lower(), content_type)
            translated.append(translated_type)
        
        return translated
    
    async def expand_query_for_language(
        self,
        original_query: str,
        target_language: str,
        intent: str = "discover"
    ) -> List[str]:
        """Expand query with language-specific terms."""
        expanded_queries = [original_query]
        
        # Get language-specific search terms
        search_terms = self.common_search_terms.get(target_language, {})
        
        if not search_terms:
            return expanded_queries
        
        # Add intent-specific expansions
        intent_terms = search_terms.get(intent, [])
        if intent_terms:
            for term in intent_terms[:3]:  # Use top 3 terms
                expanded_queries.append(f"{term} {original_query}")
        
        # Add "best" variations for discovery
        if intent == "discover":
            best_terms = search_terms.get("best", [])
            for term in best_terms[:2]:
                expanded_queries.append(f"{term} {original_query}")
        
        return expanded_queries
    
    def get_optimal_regions_for_language(self, language: str) -> List[str]:
        """Get optimal YouTube regions for a language."""
        for lang_enum in SupportedLanguage:
            config = self.language_configs.get(lang_enum)
            if config and config.code == language:
                return config.youtube_region_codes or [config.default_region]
        
        return ["US"]  # Default fallback
    
    async def get_localized_trending_content(
        self,
        language: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trending content for specific language/region."""
        # This would integrate with the YouTube API to get region-specific trending content
        # For now, return structure for implementation
        
        if not region:
            regions = self.get_optimal_regions_for_language(language)
            region = regions[0] if regions else "US"
        
        cache_key = f"trending:{language}:{region}"
        
        # Check cache first
        if self.cache_manager:
            cached_trends = await self.cache_manager.get(cache_key)
            if cached_trends:
                return cached_trends
        
        # This would call YouTube API for trending content
        trending_data = {
            "language": language,
            "region": region,
            "trending_videos": [],  # Would be populated from API
            "trending_keywords": [],  # Would be analyzed from trending content
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        # Cache the results
        if self.cache_manager:
            await self.cache_manager.set(cache_key, trending_data, ttl=3600)  # 1 hour
        
        return trending_data
    
    async def analyze_multi_language_content(
        self,
        videos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze content across multiple languages."""
        language_distribution = {}
        region_distribution = {}
        
        for video in videos:
            # Detect language from title/description
            snippet = video.get("snippet", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            
            detected_lang = self.detect_language(f"{title} {description}")
            language_distribution[detected_lang] = language_distribution.get(detected_lang, 0) + 1
            
            # Track regions if available
            default_language = snippet.get("defaultLanguage")
            if default_language:
                regions = self.get_optimal_regions_for_language(default_language)
                for region in regions:
                    region_distribution[region] = region_distribution.get(region, 0) + 1
        
        return {
            "total_videos": len(videos),
            "language_distribution": language_distribution,
            "region_distribution": region_distribution,
            "dominant_language": max(language_distribution.items(), key=lambda x: x[1])[0] if language_distribution else "en",
            "language_diversity_score": len(language_distribution) / max(len(videos), 1)
        }
    
    def get_language_config(self, language_code: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language."""
        for lang_enum in SupportedLanguage:
            config = self.language_configs.get(lang_enum)
            if config and config.code == language_code:
                return config
        return None
    
    async def optimize_search_for_language(
        self,
        query: str,
        language: str,
        intent: str = "discover"
    ) -> Dict[str, Any]:
        """Optimize search parameters for specific language."""
        config = self.get_language_config(language)
        if not config:
            return {"query": query, "language": language, "region": "US"}
        
        # Expand query with language-specific terms
        expanded_queries = await self.expand_query_for_language(query, language, intent)
        
        # Get optimal regions
        optimal_regions = self.get_optimal_regions_for_language(language)
        
        # Translate content types if available
        content_types = ["tutorial", "review", "vlog"]  # Example
        translated_types = await self.translate_content_types(content_types, language)
        
        return {
            "original_query": query,
            "expanded_queries": expanded_queries,
            "language": language,
            "optimal_regions": optimal_regions,
            "translated_content_types": translated_types,
            "is_rtl": config.rtl,
            "default_region": config.default_region
        }


# Global multi-language manager instance
multi_language_manager = MultiLanguageManager()


async def get_multi_language_manager() -> MultiLanguageManager:
    """Get multi-language manager instance."""
    if multi_language_manager.cache_manager is None:
        await multi_language_manager.initialize()
    return multi_language_manager