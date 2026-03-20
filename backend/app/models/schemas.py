from pydantic import BaseModel
from typing import Optional, Literal


class StockPricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class SentimentResult(BaseModel):
    title: str
    score: float
    label: Literal["positive", "neutral", "negative"]
    explanation: str
    source: str


class AnalysisDetails(BaseModel):
    fundamental_reason: str
    social_insight: str
    risk_factor: str


class PredictionScores(BaseModel):
    fundamental: float
    social: float
    gap: float


class PredictionResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: float
    predicted_direction: Literal["up", "down", "neutral"]
    predicted_change_pct: float
    confidence: float
    sentiment_score: float
    sentiment_label: Literal["positive", "neutral", "negative"]
    analysis: Optional[AnalysisDetails] = None
    scores: Optional[PredictionScores] = None
    judgment: Optional[Literal["BUY", "HOLD", "WATCH"]] = None
    sentiment_summary: str
    news_articles: list[SentimentResult] = []
    price_history: list[StockPricePoint] = []
    generated_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
