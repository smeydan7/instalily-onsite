"""Insight-generation stage — turn a scored candidate into recommendations."""
from app.pipeline.insights.generator import generate_insights

__all__ = ["generate_insights"]
