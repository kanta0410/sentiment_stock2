import asyncio
import sys
import os
from datetime import datetime
import json

# backend フォルダをパスに追加
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.scraper.tdnet_scraper import fetch_primary_news
from app.services.scraper.reddit_scraper import fetch_reddit_sentiment
from app.services.sentiment.gemini_analyzer import analyze_sentiment

async def debug_flow(ticker: str):
    print(f"--- Debugging Flow for {ticker} ---")
    
    # 1. 一次情報取得 (TDnet/株探)
    print("\n[1] Fetching primary news...")
    primary = await fetch_primary_news(ticker)
    if primary:
        print(f"Found {len(primary)} articles.")
        for a in primary[:3]:
            print(f" - [{a.get('date', 'N/A')}] {a['title']}")
    else:
        print("No news found.")

    # 2. 二次情報取得 (Reddit)
    print("\n[2] Fetching social posts (Reddit)...")
    social = await fetch_reddit_sentiment(ticker)
    if social:
        print(f"Found {len(social)} posts.")
        for p in social[:3]:
            print(f" - [↑{p.get('score_upvotes', 0)}] {p['title']}")
    else:
        print("No social posts found.")

    # 3. Gemini による統合分析とスコアリング
    print("\n[3] Running Gemini AI analysis...")
    if not primary and not social:
        print("Error: No data to analyze.")
        return

    result = await analyze_sentiment(ticker, primary, social)
    
    print("\n--- Analysis Result ---")
    print(f"Final Score   : {result.get('final_score')}")
    print(f"Confidence    : {result.get('confidence')} (Reliability)")
    print(f"Judgment      : {result.get('judgment')}")
    print(f"Direction     : {result.get('predicted_direction')}")
    print(f"Change Pct    : {result.get('predicted_change_pct')}%")
    print(f"Summary       : {result.get('summary')}")
    print("\nFundamental Reason: ", result.get('fundamental_reason'))
    print("Social Insight    : ", result.get('social_insight'))
    print("Risk Factor       : ", result.get('risk_factor'))

if __name__ == "__main__":
    asyncio.run(debug_flow("7203.T")) # トヨタ
