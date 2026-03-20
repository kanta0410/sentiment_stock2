"""
Gemini API センチメント分析エンジン（ロジック強化版）
時系列・SNS影響度・信頼度をプロンプトベースで統合
"""
import asyncio
import json
import logging
import math
import re
import time
from datetime import datetime
from typing import Any

import google.generativeai as genai
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 基本設定
FUNDAMENTAL_WEIGHT = 0.70
SOCIAL_WEIGHT = 0.30
GEMINI_MODEL = "gemini-3-flash-preview"


def _init_gemini() -> genai.GenerativeModel:
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def _recency_weight(created_utc: float) -> float:
    """投稿の新しさに応じた重み係数 (24h以内=1.2x, 1週間以内=1.0x, それ以前=0.6x)"""
    if created_utc <= 0:
        return 1.0
    age_hours = (time.time() - created_utc) / 3600
    if age_hours <= 24:
        return 1.2
    elif age_hours <= 168:  # 7日
        return 1.0
    else:
        return 0.6


def _upvote_weight(upvotes: int) -> float:
    """upvote数の対数スケール重み (1+でゼロ除算回避, 上限10x)"""
    return min(math.log1p(max(upvotes, 0)) / math.log1p(100), 10.0)


def _build_prompt(ticker: str, primary_articles: list[dict], social_posts: list[dict]) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"あなたは世界的なクオンツアナリストです。銘柄 {ticker} について、以下の情報を分析して株価センチメントを予測してください。",
        f"【分析基準日】: {now_str}",
        "",
        "## 一次情報（公式ニュース・決算・適時開示等）",
    ]

    for i, a in enumerate(primary_articles[:10], 1):
        date = a.get("date", "不明")
        lines.append(f"{i}. [{date}] {a['title']}")

    if social_posts:
        lines.append("")
        lines.append("## 二次情報（Reddit SNS投稿 — upvotes・コメント数付き）")
        for i, p in enumerate(social_posts[:15], 1):
            upvotes = p.get("score_upvotes", 0)
            comments = p.get("num_comments", 0)
            body = p.get("body", "").strip()[:200]
            header = f"{i}. [↑{upvotes} up / {comments} comments] {p['title']}"
            lines.append(header)
            if body:
                lines.append(f"   本文: {body}")

    lines += [
        "",
        "### 分析指示",
        "各記事・投稿を個別評価し、以下のJSONを返してください。",
        "- score: -1.0〜+1.0（株価への影響度）",
        "- label: positive(>0.1) / neutral(-0.1〜0.1) / negative(<-0.1)",
        "- source: 一次情報は'tdnet'、Reddit投稿は'reddit'",
        "- fundamental_score: 一次情報のみの加重平均スコア",
        "- social_score: Reddit投稿のupvote数を考慮した加重平均スコア",
        "- reliability_index: 情報の質と整合性 0.0〜1.0",
        "",
        "純粋なJSONのみ返してください（コードブロック不要）:",
        """{
  "articles": [
    {"title": "一次情報タイトル", "score": 0.5, "label": "positive", "explanation": "根拠（日本語）", "source": "tdnet"},
    {"title": "Reddit投稿タイトル", "score": 0.3, "label": "positive", "explanation": "根拠（日本語）", "source": "reddit"}
  ],
  "summary": "総合分析（日本語・3〜4文）",
  "fundamental_reason": "一次情報の主要要因（日本語・2文）",
  "social_insight": "SNSの反応（日本語・2文）",
  "risk_factor": "主要リスク（日本語・1〜2文）",
  "fundamental_score": 0.0,
  "social_score": 0.0,
  "final_score": 0.0,
  "reliability_index": 0.0,
  "judgment": "BUY"
}""",
    ]
    return "\n".join(lines)

def _parse_response(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)
    
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"Gemini parsing failed: {e}")
        return {
            "articles": [], "summary": "解析失敗（フォールバック）",
            "fundamental_reason": "エラー", "social_insight": "エラー", "risk_factor": "不明",
            "fundamental_score": 0.0, "social_score": 0.0, "final_score": 0.0,
            "reliability_index": 0.30, "judgment": "HOLD"
        }

async def analyze_sentiment(
    ticker: str,
    primary_articles: list[dict],
    social_posts: list[dict],
) -> dict[str, Any]:
    """Gemini SDKを使ってセンチメント分析"""
    if not primary_articles and not social_posts:
        return {
            "articles": [], "summary": "銘柄データ不足",
            "fundamental_reason": "なし", "social_insight": "なし", "risk_factor": "なし",
            "fundamental_score": 0.0, "social_score": 0.0, "final_score": 0.0,
            "confidence": 0.20, "predicted_change_pct": 0.0, "judgment": "HOLD",
            "predicted_direction": "neutral", "sentiment_label": "neutral",
        }

    prompt = _build_prompt(ticker, primary_articles, social_posts)
    model = _init_gemini()
    
    raw_text = ""
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 8192},
            ),
        )
        raw_text = response.text
        logger.info(f"Gemini SDK success for {ticker}: {len(raw_text)} chars")
    except Exception as e:
        logger.error(f"Gemini SDK error: {e}")

    parsed = _parse_response(raw_text)

    # Geminiが返した記事リスト
    analyzed = parsed.get("articles", [])

    # ---- Pythonサイドで upvote重み付き social_score を再計算 ----
    # social_postsのタイトルをキーにupvote/created_utcを引けるようにする
    _post_index = {p["title"][:60]: p for p in social_posts}

    weighted_sum = 0.0
    weight_total = 0.0
    for a in analyzed:
        if a.get("source") not in ("reddit",):
            continue
        score = float(a.get("score", 0.0))
        title_key = a.get("title", "")[:60]
        raw_post = _post_index.get(title_key)
        if raw_post:
            upvotes = raw_post.get("score_upvotes", 0)
            created_utc = raw_post.get("created_utc", 0.0)
            w = _upvote_weight(upvotes) * _recency_weight(created_utc)
        else:
            w = 1.0  # マッチしない場合はデフォルト重み
        weighted_sum += score * w
        weight_total += w

    # Geminiが返したsocial_scoreとPython計算の加重平均をブレンド
    gemini_s = float(parsed.get("social_score", 0.0))
    if weight_total > 0:
        python_s = weighted_sum / weight_total
        # Geminiの質的判断(60%) + Python重み付き計算(40%) でブレンド
        s_score = 0.60 * gemini_s + 0.40 * python_s
        logger.info(
            f"{ticker} social_score: gemini={gemini_s:.3f}, "
            f"python_weighted={python_s:.3f} (total_weight={weight_total:.1f}) → blend={s_score:.3f}"
        )
    else:
        s_score = gemini_s

    s_score = max(-1.0, min(1.0, s_score))

    # fundamental_score はGemini値をそのまま使用
    f_score = max(-1.0, min(1.0, float(parsed.get("fundamental_score", 0.0))))

    # final_score 再計算
    if social_posts:
        final_score = FUNDAMENTAL_WEIGHT * f_score + SOCIAL_WEIGHT * s_score
    else:
        final_score = f_score

    reliability = max(0.1, min(0.99, float(parsed.get("reliability_index", 0.50))))

    predicted_change_pct = round(final_score * 8.0 * reliability, 2)
    predicted_direction = "up" if final_score > 0.12 else "down" if final_score < -0.12 else "neutral"
    sentiment_label = "positive" if final_score > 0.12 else "negative" if final_score < -0.12 else "neutral"

    judgment = parsed.get("judgment", "HOLD")
    if judgment not in ("BUY", "HOLD", "WATCH"):
        judgment = "HOLD"

    return {
        "articles": analyzed,
        "summary": parsed.get("summary", ""),
        "fundamental_reason": parsed.get("fundamental_reason", ""),
        "social_insight": parsed.get("social_insight", ""),
        "risk_factor": parsed.get("risk_factor", ""),
        "fundamental_score": round(f_score, 4),
        "social_score": round(s_score, 4),
        "final_score": round(final_score, 4),
        "confidence": round(reliability, 3),
        "predicted_change_pct": predicted_change_pct,
        "judgment": judgment,
        "predicted_direction": predicted_direction,
        "sentiment_label": sentiment_label,
    }
