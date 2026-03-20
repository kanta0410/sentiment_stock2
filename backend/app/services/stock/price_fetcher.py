"""
株価データフェッチャー
- 一次: pandas_datareader (stooq) - 安定、認証不要
- 二次: yfinance - フォールバック
"""
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _to_stooq_symbol(ticker: str) -> str:
    """ティッカーをstooq形式に変換
    7203.T -> 7203.JP
    AAPL   -> AAPL.US
    """
    t = ticker.upper()
    if t.endswith(".T"):
        return t.replace(".T", ".JP")
    if re.match(r"^\d{4}$", t):
        return f"{t}.JP"
    if "." not in t:
        return f"{t}.US"
    return t


def fetch_stock_info(ticker: str) -> dict:
    """銘柄の現在値・会社名を取得"""
    # stooq から最新価格を取得
    try:
        import pandas_datareader as pdr
        import datetime as dt

        sym = _to_stooq_symbol(ticker)
        end = dt.date.today()
        start = end - dt.timedelta(days=7)
        df = pdr.get_data_stooq(sym, start=start, end=end)

        if not df.empty:
            latest = df.sort_index(ascending=False).iloc[0]
            current_price = float(latest["Close"])

            # 会社名はyfinanceから試みる（失敗してもOK）
            company_name = _get_company_name(ticker)
            return {
                "ticker": ticker,
                "company_name": company_name,
                "current_price": current_price,
            }
    except Exception as e:
        logger.warning(f"stooq price fetch failed for {ticker}: {e}")

    # yfinanceフォールバック
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = getattr(info, "last_price", None) or getattr(info, "previous_close", None) or 0.0
        return {
            "ticker": ticker,
            "company_name": _get_company_name(ticker),
            "current_price": float(price),
        }
    except Exception as e:
        logger.warning(f"yfinance fallback failed for {ticker}: {e}")

    return {
        "ticker": ticker,
        "company_name": None,
        "current_price": 0.0,
    }


def _get_company_name(ticker: str) -> str | None:
    """会社名を取得（失敗時はNone）"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return (
            info.get("longName")
            or info.get("shortName")
            or None
        )
    except Exception:
        return None


def fetch_price_history(ticker: str, days: int = 30) -> list[dict]:
    """株価履歴を取得（stooq優先）"""
    try:
        import pandas_datareader as pdr
        import datetime as dt

        sym = _to_stooq_symbol(ticker)
        end = dt.date.today()
        start = end - dt.timedelta(days=days + 10)
        df = pdr.get_data_stooq(sym, start=start, end=end)

        if df.empty:
            raise ValueError("empty dataframe")

        df = df.sort_index(ascending=True)
        result = []
        for ts, row in df.iterrows():
            result.append({
                "date": ts.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })
        logger.info(f"stooq price history: {len(result)} rows for {ticker}")
        return result[-days:]

    except Exception as e:
        logger.warning(f"stooq history failed for {ticker}: {e}, trying yfinance")

    # yfinanceフォールバック
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        end = datetime.now()
        start = end - timedelta(days=days + 5)
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

        if hist.empty:
            return []

        result = []
        for ts, row in hist.iterrows():
            result.append({
                "date": ts.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })
        logger.info(f"yfinance price history: {len(result)} rows for {ticker}")
        return result[-days:]

    except Exception as e:
        logger.warning(f"yfinance history also failed for {ticker}: {e}")
        return []
