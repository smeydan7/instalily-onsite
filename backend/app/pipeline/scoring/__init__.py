"""Scoring stage — assign a 0..100 lead score to each candidate."""
from app.pipeline.scoring.scorer import score_candidate

__all__ = ["score_candidate"]
