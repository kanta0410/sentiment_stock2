"""
予測APIルート
GET /api/predict/quick?ticker=7203.T&days=30
"""
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    AnalysisDetails,
    PredictionResponse,
    PredictionScores,
    SentimentResult,
    StockPricePoint,
)
from app.services.scraper.tdnet_scraper import fetch_primary_news
from app.services.scraper.reddit_scraper import fetch_reddit_sentiment
from app.services.sentiment.gemini_analyzer import analyze_sentiment
from app.services.stock.price_fetcher import fetch_stock_info, fetch_price_history

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/quick", response_model=PredictionResponse)
async def predict_quick(
    ticker: str = Query(..., description="ティッカーシンボル (例: 7203.T, AAPL)"),
    days: int = Query(30, ge=7, le=90, description="株価履歴の日数"),
):
    ticker = ticker.upper().strip()
    logger.info(f"Prediction request: ticker={ticker}, days={days}")

    # 並行してデータ取得
    try:
        primary_task = fetch_primary_news(ticker)
        social_task = fetch_reddit_sentiment(ticker)
        stock_info_task = asyncio.get_event_loop().run_in_executor(
            None, fetch_stock_info, ticker
        )
        price_history_task = asyncio.get_event_loop().run_in_executor(
            None, fetch_price_history, ticker, days
        )

        primary_articles, social_posts, stock_info, raw_price_history = await asyncio.gather(
            primary_task,
            social_task,
            stock_info_task,
            price_history_task,
        )
    except Exception as e:
        logger.error(f"Data fetch error for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")

    logger.info(
        f"{ticker}: primary={len(primary_articles)}, social={len(social_posts)}, "
        f"price_history={len(raw_price_history)}"
    )

    # センチメント分析 (Gemini API)
    try:
        analysis_result = await analyze_sentiment(ticker, primary_articles, social_posts)
    except Exception as e:
        logger.error(f"Gemini analysis error for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"AI分析エラー: {str(e)}")

    # スキーマへ変換
    # Geminiが返すsourceを正規化
    _source_map = {
        "primary": "tdnet", "secondary": "reddit",
        "news": "tdnet", "official_news": "tdnet", "sec_filing": "tdnet",
        "press_release": "tdnet", "earnings": "tdnet", "kabutan": "tdnet",
        "sns": "reddit", "social": "reddit", "twitter": "reddit",
    }
    news_articles = []
    for a in analysis_result.get("articles", []):
        label = a.get("label", "neutral")
        if label not in ("positive", "neutral", "negative"):
            label = "neutral"
        raw_source = a.get("source", "tdnet")
        source = _source_map.get(raw_source, raw_source)
        if source not in ("tdnet", "reddit", "kabutan"):
            source = "tdnet"
        news_articles.append(
            SentimentResult(
                title=a.get("title", ""),
                score=round(float(a.get("score", 0.0)), 4),
                label=label,
                explanation=a.get("explanation", ""),
                source=source,
            )
        )

    price_history = [
        StockPricePoint(**p) for p in raw_price_history
    ]

    # 現在値のフォールバック（price_historyから取得）
    current_price = stock_info.get("current_price", 0.0)
    if current_price == 0.0 and price_history:
        current_price = price_history[-1].close

    # direction のクリーニング
    direction = analysis_result.get("predicted_direction", "neutral")
    if direction not in ("up", "down", "neutral"):
        direction = "neutral"
    sentiment_label = analysis_result.get("sentiment_label", "neutral")
    if sentiment_label not in ("positive", "neutral", "negative"):
        sentiment_label = "neutral"
    judgment = analysis_result.get("judgment", "HOLD")
    if judgment not in ("BUY", "HOLD", "WATCH"):
        judgment = "HOLD"

    return PredictionResponse(
        ticker=ticker,
        company_name=stock_info.get("company_name"),
        current_price=current_price,
        predicted_direction=direction,
        predicted_change_pct=analysis_result.get("predicted_change_pct", 0.0),
        confidence=analysis_result.get("confidence", 0.30),
        sentiment_score=analysis_result.get("final_score", 0.0),
        sentiment_label=sentiment_label,
        analysis=AnalysisDetails(
            fundamental_reason=analysis_result.get("fundamental_reason", ""),
            social_insight=analysis_result.get("social_insight", ""),
            risk_factor=analysis_result.get("risk_factor", ""),
        ),
        scores=PredictionScores(
            fundamental=analysis_result.get("fundamental_score", 0.0),
            social=analysis_result.get("social_score", 0.0),
            gap=round(
                analysis_result.get("fundamental_score", 0.0)
                - analysis_result.get("social_score", 0.0),
                4,
            ),
        ),
        judgment=judgment,
        sentiment_summary=analysis_result.get("summary", ""),
        news_articles=news_articles,
        price_history=price_history,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
