"""
TREND MONITOR - Filters Package
================================
Módulos para filtragem e scoring de trends.
"""

from .relevance import RelevanceFilter, calculate_relevance_score

__all__ = ["RelevanceFilter", "calculate_relevance_score"]
