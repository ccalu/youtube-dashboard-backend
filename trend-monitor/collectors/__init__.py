"""
TREND MONITOR - Collectors Package
===================================
Módulos para coleta de dados de diferentes fontes.

FONTES GRATUITAS:
- Google Trends (pytrends) - sem credencial
- YouTube (API v3) - precisa API key
- Reddit (PRAW) - precisa client_id/secret
- Hacker News (API pública) - sem credencial
"""

from .google_trends import GoogleTrendsCollector
from .reddit import RedditCollector
from .youtube import YouTubeCollector
from .hackernews import HackerNewsCollector

__all__ = [
    "GoogleTrendsCollector",
    "RedditCollector",
    "YouTubeCollector",
    "HackerNewsCollector"
]
