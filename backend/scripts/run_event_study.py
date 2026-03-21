import os
import sys
import asyncio
import time
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 環境変数（Gemini APIキーなど）を読むためにdotenvをロード
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from app.services.scraper.reddit_scraper import fetch_reddit_sentiment
from app.services.scraper.tdnet_scraper import fetch_primary_news
from app.services.sentiment.gemini_analyzer import analyze_sentiment

# 検証したいイベント（急騰/急落の前日などを指定）
EVENTS = [
    {"ticker": "TSLA", "target_date": "2026-03-18"},
    {"ticker": "7203.T", "target_date": "2026-03-15"},
    {"ticker": "NVDA", "target_date": "2026-02-20"}
]

RESULTS_DIR = os.path.join(project_root, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

async def run_event_study():
    print("=== イベント・ドリブン評価 (タイムマシン検証) 開始 ===")
    
    for idx, event in enumerate(EVENTS):
        ticker = event["ticker"]
        target_date = event["target_date"]
        
        print(f"\n[{idx+1}/{len(EVENTS)}] 銘柄: {ticker}, 評価基準日: {target_date}")
        print(" -> 過去データ(評価基準日以前のニュース/SNS)を取得中...")
        
        try:
            # 1. タイムマシン機能を使って過去データのみ取得
            primary_task = fetch_primary_news(ticker, target_date=target_date)
            social_task = fetch_reddit_sentiment(ticker, limit=30, target_date=target_date)
            
            primary_articles, social_posts = await asyncio.gather(primary_task, social_task)
            
            print(f" -> 取得完了: ニュース {len(primary_articles)} 件, Reddit {len(social_posts)} 件")
            
            # 2. AIによる予測 (指定した過去時点での感情分析)
            print(" -> AIによる分析（予測シグナル生成）を実行中...")
            analysis_result = await analyze_sentiment(ticker, primary_articles, social_posts)
            
            # 3. 結果をMarkdownで保存
            save_filename = f"event_study_{ticker}_{target_date}.md"
            save_path = os.path.join(RESULTS_DIR, save_filename)
            
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(f"# Event Study Result: {ticker}\n\n")
                f.write(f"- **Target Date (評価基準日):** {target_date}\n")
                f.write(f"- **Generated At:** {datetime.now().isoformat()}\n\n")
                
                f.write("## 1. AI Sentiment Analysis (シグナル評価)\n")
                f.write(f"- **Judgment (推奨):** {analysis_result.get('judgment', '不明')}\n")
                f.write(f"- **Predicted Direction:** {analysis_result.get('predicted_direction')}\n")
                f.write(f"- **Sentiment Score:** {analysis_result.get('final_score')}\n")
                f.write(f"- **Confidence:** {analysis_result.get('confidence')}\n\n")
                
                f.write("## 2. Summary (総合サマリー)\n")
                f.write(f"{analysis_result.get('summary', '')}\n\n")
                
                f.write("## 3. Detailed Factors (詳細要因)\n")
                f.write(f"### Fundamental\n{analysis_result.get('fundamental_reason', '')}\n\n")
                f.write(f"### Social Insight\n{analysis_result.get('social_insight', '')}\n\n")
                f.write(f"### Risk Factor\n{analysis_result.get('risk_factor', '')}\n\n")
                
            print(f" ✅ 結果ファイルを作成しました: {save_path}")
            
        except Exception as e:
            print(f" ❌ エラーが発生しました: {e}")
        
        # API制限回避
        if idx < len(EVENTS) - 1:
            wait_sec = 15
            print(f" -> APIレート制限回避のため {wait_sec}秒 待機します...")
            time.sleep(wait_sec)
            
    print("\n=== 全ての検証処理が完了しました ===")

if __name__ == "__main__":
    asyncio.run(run_event_study())
