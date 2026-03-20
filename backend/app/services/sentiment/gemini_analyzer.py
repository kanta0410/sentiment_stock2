"""
Gemini API センチメント分析エンジン（REST API直接呼び出し版）

スコアリングアルゴリズム:
  final_score = 0.70 * fundamental_score + 0.30 * social_score
"""
import json
import logging
import re
import statistics
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

FUNDAMENTAL_WEIGHT = 0.70
SOCIAL_WEIGHT = 0.30
GEMINI_MODEL = "gemini-2.5-flash"


def _build_prompt(ticker: str, primary_articles: list[dict], social_posts: list[dict]) -> str:
    lines = [
        f"あなたはクオンツアナリストです。銘柄 {ticker} の以下のニュース・SNS投稿を分析してください。",
        "",
        "## 一次情報（公式ニュース・決算・適時開示）",
    ]
    for i, a in enumerate(primary_articles[:8], 1):
        lines.append(f"{i}. {a['title']}")

    if social_posts:
        lines.append("")
        lines.append("## 二次情報（Reddit SNS投稿）")
        for i, p in enumerate(social_posts[:5], 1):
            upvotes = p.get("score_upvotes", 0)
            lines.append(f"{i}. [r/{p.get('subreddit', 'reddit')} ↑{upvotes}] {p['title']}")

    lines += [
        "",
        "## 分析指示",
        "各情報ソースについて評価し、JSON形式で返してください。",
        "",
        "- score: -1.0（極めて悲観的）〜 +1.0（極めて楽観的）",
        "- label: 'positive'(>0.1) / 'neutral'(-0.1〜0.1) / 'negative'(<-0.1)",
        "- explanation: 日本語50-100字の根拠",
        f"- final_score: {FUNDAMENTAL_WEIGHT}×fundamental_score + {SOCIAL_WEIGHT}×social_score",
        "",
        "- source: 一次情報は'tdnet'、Reddit SNS投稿は'reddit'を使用",
        "",
        "純粋なJSONのみ返してください（コードブロック不要）:",
        """{
  "articles": [
    {"title": "一次情報の記事タイトル", "score": 0.5, "label": "positive", "explanation": "根拠", "source": "tdnet"},
    {"title": "Reddit投稿タイトル", "score": 0.3, "label": "positive", "explanation": "根拠", "source": "reddit"}
  ],
  "summary": "3〜4文の総合分析（日本語）",
  "fundamental_reason": "一次情報の主要要因（日本語・2文）",
  "social_insight": "SNS世論の概要（日本語・1〜2文）",
  "risk_factor": "主要リスク（日本語・1〜2文）",
  "fundamental_score": 0.0,
  "social_score": 0.0,
  "final_score": 0.0
}""",
    ]
    return "\n".join(lines)


def _parse_response(raw: str, primary_articles: list[dict], social_posts: list[dict]) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini JSON")
        articles = [
            {"title": a["title"], "score": 0.0, "label": "neutral",
             "explanation": "解析エラー", "source": a.get("source", "tdnet")}
            for a in primary_articles
        ] + [
            {"title": p["title"], "score": 0.0, "label": "neutral",
             "explanation": "解析エラー", "source": "reddit"}
            for p in social_posts
        ]
        return {
            "articles": articles,
            "summary": "分析データを処理中です。",
            "fundamental_reason": "データ処理中",
            "social_insight": "データ処理中",
            "risk_factor": "データ不足",
            "fundamental_score": 0.0,
            "social_score": 0.0,
            "final_score": 0.0,
        }


def _compute_confidence(scores: list[float]) -> float:
    if not scores:
        return 0.30
    n = len(scores)
    mean = sum(scores) / n
    std = statistics.stdev(scores) if n >= 2 else 0.5
    consistency = max(0.0, 1.0 - std)
    signal_strength = min(abs(mean) * 2.0, 1.0)
    n_factor = min(n / 10.0, 1.0)
    confidence = 0.40 * consistency + 0.40 * signal_strength + 0.20 * n_factor
    return round(max(0.15, min(0.99, confidence)), 3)


def _compute_judgment(final_score: float, confidence: float) -> str:
    if final_score >= 0.35 and confidence >= 0.55:
        return "BUY"
    elif final_score <= -0.35 and confidence >= 0.55:
        return "WATCH"
    return "HOLD"


async def analyze_sentiment(
    ticker: str,
    primary_articles: list[dict],
    social_posts: list[dict],
) -> dict[str, Any]:
    """Gemini REST APIを使ってセンチメント分析"""
    settings = get_settings()

    if not primary_articles and not social_posts:
        return {
            "articles": [], "summary": f"{ticker} のデータが取得できませんでした。",
            "fundamental_reason": "データなし", "social_insight": "データなし",
            "risk_factor": "データ不足", "fundamental_score": 0.0,
            "social_score": 0.0, "final_score": 0.0, "confidence": 0.20,
            "predicted_change_pct": 0.0, "judgment": "HOLD",
            "predicted_direction": "neutral", "sentiment_label": "neutral",
        }

    prompt = _build_prompt(ticker, primary_articles, social_posts)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
    }

    raw = ""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Gemini response: {len(raw)} chars for {ticker}")
    except Exception as e:
        logger.error(f"Gemini API error for {ticker}: {e}")

    parsed = _parse_response(raw, primary_articles, social_posts)

    analyzed = parsed.get("articles", [])
    fundamental_score = float(parsed.get("fundamental_score", 0.0))
    social_score = float(parsed.get("social_score", 0.0))
    final_score = float(parsed.get("final_score", 0.0))

    if fundamental_score == 0.0 and social_score == 0.0 and analyzed:
        fund_scores = [a["score"] for a in analyzed if a.get("source") in ("tdnet", "kabutan")]
        soc_scores = [a["score"] for a in analyzed if a.get("source") == "reddit"]
        if fund_scores:
            fundamental_score = sum(fund_scores) / len(fund_scores)
        if soc_scores:
            social_score = sum(soc_scores) / len(soc_scores)
        if fund_scores and soc_scores:
            final_score = FUNDAMENTAL_WEIGHT * fundamental_score + SOCIAL_WEIGHT * social_score
        elif fund_scores:
            final_score = fundamental_score
        elif soc_scores:
            final_score = social_score

    fundamental_score = max(-1.0, min(1.0, fundamental_score))
    social_score = max(-1.0, min(1.0, social_score))
    final_score = max(-1.0, min(1.0, final_score))

    all_scores = [a["score"] for a in analyzed if isinstance(a.get("score"), (int, float))]
    confidence = _compute_confidence(all_scores)

    predicted_direction = "up" if final_score > 0.12 else "down" if final_score < -0.12 else "neutral"
    sentiment_label = "positive" if final_score > 0.12 else "negative" if final_score < -0.12 else "neutral"
    predicted_change_pct = round(final_score * 8.0 * confidence, 2)
    judgment = _compute_judgment(final_score, confidence)

    for a in analyzed:
        if not a.get("source"):
            a["source"] = "tdnet"

    return {
        "articles": analyzed,
        "summary": parsed.get("summary", ""),
        "fundamental_reason": parsed.get("fundamental_reason", ""),
        "social_insight": parsed.get("social_insight", ""),
        "risk_factor": parsed.get("risk_factor", ""),
        "fundamental_score": round(fundamental_score, 4),
        "social_score": round(social_score, 4),
        "final_score": round(final_score, 4),
        "confidence": confidence,
        "predicted_change_pct": predicted_change_pct,
        "judgment": judgment,
        "predicted_direction": predicted_direction,
        "sentiment_label": sentiment_label,
    }
