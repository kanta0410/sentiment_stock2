"""
株価データフェッチャー（httpx直接呼び出し版 - 外部ライブラリ不要）
Yahoo Finance の非公式 JSON API を使用
"""
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_stock_info(ticker: str) -> dict:
    """Yahoo Finance v8 APIから銘柄情報を取得"""
    sym = ticker.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d"

    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ValueError("No result")

        meta = result[0].get("meta", {})
        current_price = (
            meta.get("regularMarketPrice")
            or meta.get("previousClose")
            or 0.0
        )
        company_name = meta.get("longName") or meta.get("shortName") or None

        return {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": float(current_price),
        }
    except Exception as e:
        logger.warning(f"Yahoo Finance info failed for {ticker}: {e}")
        return {"ticker": ticker, "company_name": None, "current_price": 0.0}


def fetch_price_history(ticker: str, days: int = 30) -> list[dict]:
    """Yahoo Finance v8 APIから株価履歴を取得"""
    sym = ticker.upper()
    range_str = f"{min(days + 5, 90)}d"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={range_str}"

    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return []

        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {})
        quotes = indicators.get("quote", [{}])[0]

        opens = quotes.get("open", [])
        highs = quotes.get("high", [])
        lows = quotes.get("low", [])
        closes = quotes.get("close", [])
        volumes = quotes.get("volume", [])

        price_history = []
        for i, ts in enumerate(timestamps):
            if i >= len(closes) or closes[i] is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            price_history.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": round(float(opens[i] or closes[i]), 2),
                "high": round(float(highs[i] or closes[i]), 2),
                "low": round(float(lows[i] or closes[i]), 2),
                "close": round(float(closes[i]), 2),
                "volume": int(volumes[i] or 0) if i < len(volumes) else 0,
            })

        logger.info(f"Yahoo Finance history: {len(price_history)} rows for {ticker}")
        return price_history[-days:]

    except Exception as e:
        logger.warning(f"Yahoo Finance history failed for {ticker}: {e}")
        return []
