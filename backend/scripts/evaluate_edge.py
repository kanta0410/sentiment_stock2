import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

def generate_dummy_sentiment_data(tickers, start_date, end_date):
    """
    1. ダミーデータの生成:
    過去データがまだない状態を想定し、テスト用にダミーのDataFrameを生成。
    """
    np.random.seed(42)
    # 営業日のみのインデックスを生成
    dates = pd.date_range(start=start_date.date(), end=end_date.date(), freq='B')
    
    records = []
    for date in dates:
        for ticker in tickers:
            # -1.0 〜 1.0 のランダムなスコア
            score = np.random.uniform(-1.0, 1.0)
            records.append({'date': date, 'ticker': ticker, 'sentiment_score': score})
            
    df = pd.DataFrame(records)
    # yfinanceのインデックスとマージしやすくするため、タイムゾーンを削除
    df['date'] = df['date'].dt.tz_localize(None)
    return df

def fetch_and_calculate_returns(tickers, start_date, end_date):
    """
    2. 将来リターン（T+1）の計算:
    yfinanceを用いて株価データを取得し、翌日の終値から翌々日の終値の変化率を計算
    """
    # 将来のリターンを計算するため、エンドデートに少し余裕を持たせる
    extended_end = end_date + timedelta(days=10)
    
    print("株価データを取得中...")
    price_data = yf.download(tickers, start=start_date, end=extended_end, progress=False)
    
    # 複数銘柄の場合、MultiIndexになるため調整
    if isinstance(price_data.columns, pd.MultiIndex):
        close_prices = price_data['Close']
    else:
        close_prices = pd.DataFrame(price_data['Close'], columns=tickers)
        
    close_prices.index = close_prices.index.tz_localize(None)
    
    returns_df_list = []
    for ticker in tickers:
        ticker_close = close_prices[ticker].dropna()
        # 日次リターン: (翌日終値 - 当日終値) / 当日終値
        # shift(-1) / 現在値 - 1 が T+1(翌日)のリターン
        forward_return = ticker_close.shift(-1) / ticker_close - 1.0
        
        df = pd.DataFrame({
            'date': ticker_close.index,
            'ticker': ticker,
            'forward_return_1d': forward_return
        })
        returns_df_list.append(df)
        
    all_returns = pd.concat(returns_df_list, ignore_index=True)
    return all_returns

def calculate_ic(merged_df):
    """
    3. 情報係数 (Information Coefficient: IC) の計算:
    日次でスピアマンの順位相関係数を計算し、全期間の平均ICを算出
    """
    daily_ic = []
    
    # 日付ごとにグループ化
    for date, group in merged_df.groupby('date'):
        # 銘柄数が2以上ないと相関が計算できない
        if len(group['sentiment_score']) > 1:
            ic, _ = spearmanr(group['sentiment_score'], group['forward_return_1d'])
            if not np.isnan(ic):
                daily_ic.append({'date': date, 'ic': ic})
                
    ic_df = pd.DataFrame(daily_ic)
    if ic_df.empty or 'ic' not in ic_df:
        print("有効なICデータが計算されませんでした。銘柄数や対象期間を確認してください。")
        return pd.DataFrame()
        
    mean_ic = ic_df['ic'].mean()
    
    print("\n=== 情報係数 (IC) 分析 ===")
    print(f"Mean IC: {mean_ic:.4f}")
    if mean_ic > 0.05:
        print("評価: 非常に強い予測力 (エッジ) があります")
    elif mean_ic > 0.02:
        print("評価: 良好な予測力 (エッジ) があります")
    elif mean_ic > 0:
        print("評価: わずかな予測力があります")
    else:
        print("評価: 予測力が確認できません (ダミーデータの場合はランダムなため0付近になります)")
    print("-" * 30)
    
    return ic_df

def calculate_quintile_portfolios(merged_df):
    """
    4. クインタイル（5分位）分析:
    スコア順に5つのグループに分け、各グループの翌日平均リターンを計算
    """
    print("=== クインタイル（5分位）ポートフォリオのリターン ===")
    try:
        # ランダムなダミーモデルで銘柄数が少ない場合、日次での5等分は難しいため
        # 今回はパネル全体でのスコアを基準に分位を作成する
        merged_df['quintile'] = pd.qcut(
            merged_df['sentiment_score'], 5, 
            labels=['Q5(Lowest)', 'Q4', 'Q3', 'Q2', 'Q1(Highest)']
        )
        
        # クインタイルごとの平均翌日リターン
        quintile_returns = merged_df.groupby('quintile', observed=False)['forward_return_1d'].mean() * 10000 # bps表記
        
        print("各グループの翌日平均リターン (単位: bps, 1bps = 0.01%):")
        for q, ret in quintile_returns.items():
            print(f"{q}: {ret:.2f} bps")
            
        print("-" * 30)
        
        # 累積リターンの計算とプロット (オプション)
        # 各日のクインタイルごとの平均リターン（全体分位基準）
        daily_q_returns = merged_df.groupby(['date', 'quintile'], observed=False)['forward_return_1d'].mean().unstack()
        
        # 累積リターン (1 + r の累積積 - 1)
        cumulative_returns = (1 + daily_q_returns.fillna(0)).cumprod() - 1
        
        # プロット作成
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(10, 6))
        for col in cumulative_returns.columns:
            plt.plot(cumulative_returns.index, cumulative_returns[col] * 100, label=col)
            
        plt.title('Cumulative Returns by Sentiment Score Quintile (Dummy Data)')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return (%)')
        plt.legend(title='Quintile')
        plt.tight_layout()
        
        # 保存
        plot_path = "quintile_cumulative_returns.png"
        plt.savefig(plot_path)
        print(f"累積リターンのグラフをプロットし、保存しました: {plot_path}")
        
    except ValueError as e:
        print(f"分位分割エラー（銘柄数が少ないためかもしれません）: {e}")

def main():
    # パラメータ設定
    # 5分位クロスセクションのシミュレーションをしやすくするため、少し多めの10銘柄を設定
    tickers = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA", "NFLX", "INTC", "AMD"]
    end_date = datetime.today()
    start_date = end_date - timedelta(days=180) # 過去半年分(約126営業日)
    
    print(f"期間: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
    print(f"対象銘柄: {', '.join(tickers)}")
    print("ダミーデータの生成と処理を開始します...\n")
    
    # 1. ダミーデータの生成
    sentiment_df = generate_dummy_sentiment_data(tickers, start_date, end_date)
    
    # 2. 将来リターンの計算
    returns_df = fetch_and_calculate_returns(tickers, start_date, end_date)
    
    # データの結合
    merged_df = pd.merge(sentiment_df, returns_df, on=['date', 'ticker'], how='inner')
    merged_df = merged_df.dropna(subset=['forward_return_1d', 'sentiment_score'])
    
    print(f"\n結合済みデータ件数: {len(merged_df)} 件")
    print("-" * 30)
    
    # 3. 情報係数 (IC) の計算
    calculate_ic(merged_df)
    
    # 4. クインタイル分析と累積リターンのプロット
    calculate_quintile_portfolios(merged_df)
    
    print("\n※この結果はランダムなダミーセンチメントスコアに基づいているため、")
    print("ICは0付近となり、Q1〜Q5の間に優位なリターン差は出ないのが正常です。")

if __name__ == "__main__":
    main()
