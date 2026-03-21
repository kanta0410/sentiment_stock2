import sys
import os
import asyncio

# プロジェクトルートをPYTHONPATHに追加してappモジュールをインポート可能にする
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from app.api.routes.predict import predict_quick

async def main():
    # コマンドライン引数があればそれを使用、なければ代表的な3銘柄
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["NVDA", "TSLA", "7203.T"]
    
    print("=========================================")
    print(f"リアルタイム予測エンジン (Live Prediction)")
    print(f"対象銘柄: {', '.join(tickers)}")
    print("=========================================\n")
    
    for ticker in tickers:
        print(f"🔄 [{ticker}] ニュース(TDNet等)、Reddit投稿、株価データを収集中...")
        try:
            # 実際にAPIのルート関数を直接呼び出して予測プロセスを実行
            result = await predict_quick(ticker=ticker, days=30, reddit_limit=30)
            
            print(f"\n✅ {ticker} - {result.company_name} の分析完了")
            print(f"  💰 現在値: {result.current_price}")
            print(f"  📈 AI判定: {result.judgment} (予想方向: {result.predicted_direction}, 予想変動幅: {result.predicted_change_pct}%)")
            print(f"  🤖 総合センチメントスコア: {result.sentiment_score} (公式/ニュース: {result.scores.fundamental}, SNS: {result.scores.social})")
            print(f"  📚 サマリー:\n     {result.sentiment_summary}")
            print("\n  🔍 詳細要因:")
            print(f"     - ファンダメンタル: {result.analysis.fundamental_reason}")
            print(f"     - ソーシャル(Reddit等): {result.analysis.social_insight}")
            print(f"     - リスク要因: {result.analysis.risk_factor}")
            
            print("\n  📰 参照した主要ニュース/SNS (上位3件):")
            for i, article in enumerate(result.news_articles[:3], 1):
                source_icon = "🔥" if article.source == "reddit" else "🗞️"
                print(f"     {i}. {source_icon} {article.source} | スコア: {article.score:.2f} ({article.label})")
                print(f"        「{article.title[:60]}...」")
            
            print("-" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ [{ticker}] エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            print("-" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
