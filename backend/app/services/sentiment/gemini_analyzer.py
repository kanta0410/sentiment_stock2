"""
Gemini API センチメント分析エンジン

一次情報（TDnet/ニュース）と二次情報（Reddit/SNS）を統合し、
定量的センチメントスコアを算出する。

スコアリングアルゴリズム:
  final_score = 0.70 * fundamental_score + 0.30 * social_score

  confidence = f(n_articles, consistency, signal_strength)
  - consistency = 1 - std(scores)   (スコアの分散が小さいほど高信頼)
  - signal_strength = min(|final_score| * 2, 1.0)
  - n_factor = min(n_articles / 10, 1.0)
  - confidence = 0.40*consistency + 0.40*signal_strength + 0.20*n_factor
"""
import json
import logging
import re
from typing import Any

import google.generativeai as genai

from app.core.config import get_settings

logger = logging.getLogger(__name__)

FUNDAMENTAL_WEIGHT = 0.70
SOCIAL_WEIGHT = 0.30


def _init_gemini() -> genai.GenerativeModel:
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel("gemini-2.5-flash")  # gemini-2.0-flashはクォータ制限のため2.5-flashを使用


def _build_prompt(ticker: str, primary_articles: list[dict], social_posts: list[dict]) -> str:
    lines = [
        f"あなたはクオンツアナリストです。銘柄 {ticker} の以下のニュース・SNS投稿を分析してください。",
        "",
        "## 一次情報（公式ニュース・決算・適時開示）",
    ]
    for i, a in enumerate(primary_articles[:8], 1):  # 最大8件に絞る
        lines.append(f"{i}. {a['title']}")

    if social_posts:
        lines.append("")
        lines.append("## 二次情報（Reddit SNS投稿）")
        for i, p in enumerate(social_posts[:5], 1):  # 最大5件
            upvotes = p.get("score_upvotes", 0)
            lines.append(f"{i}. [r/{p.get('subreddit', 'reddit')} ↑{upvotes}] {p['title']}")

    lines += [
        "",
        "## 分析指示",
        "各情報ソースについて以下を評価し、最後にJSON形式で返してください。",
        "",
        "### 評価基準",
        "- score: -1.0（極めて悲観的）〜 +1.0（極めて楽観的）の実数値",
        "- label: 'positive'(score>0.1) / 'neutral'(-0.1≤score≤0.1) / 'negative'(score<-0.1)",
        "- explanation: 日本語で50-100字程度の根拠説明",
        "",
        "### 最終スコア計算（重み付け）",
        f"- fundamental_score: 一次情報の加重平均（重要度順）",
        f"- social_score: 二次情報の単純平均",
        f"- final_score: {FUNDAMENTAL_WEIGHT}×fundamental_score + {SOCIAL_WEIGHT}×social_score",
        "",
        "必ず以下のJSON形式のみ返してください（コードブロック不要、純粋なJSON）:",
        """
{
  "articles": [
    {"title": "記事タイトル", "score": 0.0, "label": "positive", "explanation": "根拠説明", "source": "tdnet"}
  ],
  "summary": "3〜4文の総合分析（日本語）。プラス要因とマイナス要因を明確に言及すること。",
  "fundamental_reason": "一次情報の主要ポジティブ・ネガティブ要因（日本語・2文程度）",
  "social_insight": "SNS世論の概要（日本語・1〜2文）",
  "risk_factor": "主要リスク要因（日本語・1〜2文）",
  "fundamental_score": 0.0,
  "social_score": 0.0,
  "final_score": 0.0
}""",
    ]
    return "\n".join(lines)


def _parse_gemini_response(raw: str, primary_articles: list[dict], social_posts: list[dict]) -> dict[str, Any]:
    """GeminiレスポンスのJSONをパース、失敗時はフォールバック"""
    # JSONブロックを抽出
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    # 先頭・末尾の余分なテキストを除去
    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        cleaned = json_match.group(0)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini JSON, using fallback")
        # フォールバック: 各記事にデフォルトスコア
        articles = []
        for a in primary_articles:
            articles.append({
                "title": a["title"],
                "score": 0.0,
                "label": "neutral",
                "explanation": "分析データを取得できませんでした",
                "source": a.get("source", "tdnet"),
            })
        for p in social_posts:
            articles.append({
                "title": p["title"],
                "score": 0.0,
                "label": "neutral",
                "explanation": "分析データを取得できませんでした",
                "source": "reddit",
            })
        return {
            "articles": articles,
            "summary": f"データ解析中にエラーが発生しました。取得した情報を基に再分析してください。",
            "fundamental_reason": "分析データ取得エラー",
            "social_insight": "分析データ取得エラー",
            "risk_factor": "データ不足によりリスク評価不能",
            "fundamental_score": 0.0,
            "social_score": 0.0,
            "final_score": 0.0,
        }


def _compute_confidence(scores: list[float]) -> float:
    """スコアの分布からconfidenceを計算"""
    import statistics
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


def _compute_predicted_change_pct(final_score: float, confidence: float) -> float:
    """最終スコアと信頼度から予測変動率(%)を算出"""
    # 最大変動幅 ±8% を想定
    MAX_CHANGE = 8.0
    return round(final_score * MAX_CHANGE * confidence, 2)


def _compute_judgment(final_score: float, confidence: float) -> str:
    if final_score >= 0.35 and confidence >= 0.55:
        return "BUY"
    elif final_score <= -0.35 and confidence >= 0.55:
        return "WATCH"
    else:
        return "HOLD"


async def analyze_sentiment(
    ticker: str,
    primary_articles: list[dict],
    social_posts: list[dict],
) -> dict[str, Any]:
    """
    Gemini APIを用いてセンチメント分析を実行

    Returns:
        {
          "articles": [SentimentResult],
          "summary": str,
          "fundamental_reason": str,
          "social_insight": str,
          "risk_factor": str,
          "fundamental_score": float,
          "social_score": float,
          "final_score": float,
          "confidence": float,
          "predicted_change_pct": float,
          "judgment": str,
          "predicted_direction": str,
          "sentiment_label": str,
        }
    """
    model = _init_gemini()

    # 記事がなければ空の結果を返す
    if not primary_articles and not social_posts:
        return {
            "articles": [],
            "summary": f"{ticker} の分析に必要なデータが取得できませんでした。",
            "fundamental_reason": "データなし",
            "social_insight": "データなし",
            "risk_factor": "データ不足",
            "fundamental_score": 0.0,
            "social_score": 0.0,
            "final_score": 0.0,
            "confidence": 0.20,
            "predicted_change_pct": 0.0,
            "judgment": "HOLD",
            "predicted_direction": "neutral",
            "sentiment_label": "neutral",
        }

    prompt = _build_prompt(ticker, primary_articles, social_posts)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
        raw = response.text
        logger.info(f"Gemini response received for {ticker} ({len(raw)} chars)")
    except Exception as e:
        logger.error(f"Gemini API error for {ticker}: {e}")
        raw = ""

    parsed = _parse_gemini_response(raw, primary_articles, social_posts)

    # スコアをソース別に集計
    analyzed_articles = parsed.get("articles", [])

    # Gemini が返した fundamental/social スコアを優先、
    # なければ article スコアから再計算
    fundamental_score = float(parsed.get("fundamental_score", 0.0))
    social_score = float(parsed.get("social_score", 0.0))
    final_score = float(parsed.get("final_score", 0.0))

    # 再計算（Gemini値が0のケース対応）
    if fundamental_score == 0.0 and social_score == 0.0 and analyzed_articles:
        fund_scores = [
            a["score"] for a in analyzed_articles if a.get("source") in ("tdnet", "kabutan")
        ]
        soc_scores = [
            a["score"] for a in analyzed_articles if a.get("source") == "reddit"
        ]
        if fund_scores:
            fundamental_score = sum(fund_scores) / len(fund_scores)
        if soc_scores:
            social_score = sum(soc_scores) / len(soc_scores)

        # どちらかのみある場合
        if fund_scores and not soc_scores:
            final_score = fundamental_score
        elif soc_scores and not fund_scores:
            final_score = social_score
        else:
            final_score = FUNDAMENTAL_WEIGHT * fundamental_score + SOCIAL_WEIGHT * social_score

    # スコアを -1.0 〜 +1.0 にクランプ
    fundamental_score = max(-1.0, min(1.0, fundamental_score))
    social_score = max(-1.0, min(1.0, social_score))
    final_score = max(-1.0, min(1.0, final_score))

    # Confidence 計算
    all_scores = [a["score"] for a in analyzed_articles if isinstance(a.get("score"), (int, float))]
    confidence = _compute_confidence(all_scores)

    # 方向・変動率・判定
    if final_score > 0.12:
        predicted_direction = "up"
    elif final_score < -0.12:
        predicted_direction = "down"
    else:
        predicted_direction = "neutral"

    if final_score > 0.12:
        sentiment_label = "positive"
    elif final_score < -0.12:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    predicted_change_pct = _compute_predicted_change_pct(final_score, confidence)
    judgment = _compute_judgment(final_score, confidence)

    # articleにsourceを確実に設定
    for a in analyzed_articles:
        if "source" not in a or not a["source"]:
            a["source"] = "tdnet"

    return {
        "articles": analyzed_articles,
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
