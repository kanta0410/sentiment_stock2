"""
Gemini API センチメント分析エンジン（ロジック強化版）
時系列・SNS影響度・信頼度をプロンプトベースで統合
"""
import json
import logging
import re
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 基本設定
FUNDAMENTAL_WEIGHT = 0.70
SOCIAL_WEIGHT = 0.30
GEMINI_MODEL = "gemini-2.0-flash"

def _build_prompt(ticker: str, primary_articles: list[dict], social_posts: list[dict]) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"あなたは世界的なクオンツアナリストです。銘柄 {ticker} について、以下の情報を分析し、将来的な株価センチメントを予測してください。",
        f"【分析基準日（現在）】: {now_str}",
        "",
        "## 一次情報（公式ニュース・決算・適時開示等）",
    ]
    
    for i, a in enumerate(primary_articles[:10], 1):
        date = a.get("date", "不明")
        lines.append(f"{i}. [{date}] {a['title']}")

    if social_posts:
        lines.append("")
        lines.append("## 二次情報（Reddit SNS投稿等）")
        for i, p in enumerate(social_posts[:8], 1):
            upvotes = p.get("score_upvotes", 0)
            lines.append(f"{i}. [↑{upvotes} upvotes] {p['title']}")

    lines += [
        "",
        "### 分析と重み付けの指示",
        "以下の基準に基づき、加重平均を用いた最終スコアを算出してください：",
        "1. **Recency Weighting (時系列重み付け)**:",
        f"   基準日({now_str})からの経過時間に応じ、24時間以内は 1.2x、1週間以内は 1.0x、それ以前は 0.5〜0.8x の係数を適用してください。",
        "2. **Social Influence (SNS影響度)**:",
        "   二次情報（Reddit）については、upvotes 数が多い投稿の重みを高めて評価してください。",
        "3. **Reliability (信頼度)**:",
        "   最終的な確信度として、『情報のソースの質 × 全体的な文脈の一致度（情報の整合性）』を 0.0〜1.0 で数値化してください。",
        "",
        "必ず以下の純粋なJSON形式のみを返してください。解説不要。",
        """{
  "articles": [
    {"title": "記事タイトル", "score": 0.5, "label": "positive", "explanation": "根拠", "source": "tdnet"}
  ],
  "summary": "総合分析（日本語・3〜4文）",
  "fundamental_reason": "一次情報の分析（日本語・2文）",
  "social_insight": "SNSの反応と整合性（日本語・2文）",
  "risk_factor": "リスク要因（日本語・1〜2文）",
  "fundamental_score": 0.0,
  "social_score": 0.0,
  "final_score": 0.0,
  "confidence_score": 0.0,
  "judgment": "BUY/HOLD/WATCH"
}""",
    ]
    return "\n".join(lines)

def _parse_response(raw: str, primary_articles: list[dict], social_posts: list[dict]) -> dict[str, Any]:
    # JSONのパースとフォールバック
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)
    
    try:
        return json.loads(cleaned)
    except:
        logger.warning("Gemini parsing failed, using fallback")
        return {
            "articles": [], "summary": "解析中にエラーが発生しました。",
            "fundamental_reason": "データ処理中", "social_insight": "データ処理中",
            "risk_factor": "評価不能", "fundamental_score": 0.0,
            "social_score": 0.0, "final_score": 0.0, "confidence_score": 0.30,
            "judgment": "HOLD"
        }

async def analyze_sentiment(
    ticker: str,
    primary_articles: list[dict],
    social_posts: list[dict],
) -> dict[str, Any]:
    """Gemini REST APIを使ってセンチメント分析"""
    settings = get_settings()

    if not primary_articles and not social_posts:
        return {
            "articles": [], "summary": "銘柄データが不足しています。",
            "fundamental_reason": "なし", "social_insight": "なし", "risk_factor": "なし",
            "fundamental_score": 0.0, "social_score": 0.0, "final_score": 0.0,
            "confidence": 0.20, "predicted_change_pct": 0.0, "judgment": "HOLD",
            "predicted_direction": "neutral", "sentiment_label": "neutral",
        }

    prompt = _build_prompt(ticker, primary_articles, social_posts)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={settings.gemini_api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}})
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Gemini API analysis success for {ticker}")
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raw_text = ""

    parsed = _parse_response(raw_text, primary_articles, social_posts)
    
    # UI互換性の保持（confidence フィールドへ信頼度を格納）
    final_score = float(parsed.get("final_score", 0.0))
    confidence_val = float(parsed.get("confidence_score", 0.50))
    
    predicted_change_pct = round(final_score * 8.0 * confidence_val, 2)
    predicted_direction = "up" if final_score > 0.12 else "down" if final_score < -0.12 else "neutral"
    sentiment_label = "positive" if final_score > 0.12 else "negative" if final_score < -0.12 else "neutral"

    return {
        "articles": parsed.get("articles", []),
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
