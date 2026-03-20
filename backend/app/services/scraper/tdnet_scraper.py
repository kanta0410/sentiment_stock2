"""
ニューススクレイパー
- 日本株: Yahoo Finance Japan から株別ニュースを取得
- 米国株: Yahoo Finance から最新ニュースを取得
"""
import re
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def fetch_yahoo_jp_news(ticker: str) -> list[dict]:
    """Yahoo Finance Japan から銘柄別ニュースを取得"""
    url = f"https://finance.yahoo.co.jp/quote/{ticker}/news"
    articles = []

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.content.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Yahoo JP news fetch failed for {ticker}: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")

    for link in soup.select("a[href*='/news/']"):
        title = link.get_text(strip=True)
        if not title or len(title) < 8:
            continue
        # ナビゲーションリンクを除外
        if title in ("ニュース", "企業情報", "株価", "チャート"):
            continue
        href = link.get("href", "")
        articles.append({
            "title": title,
            "body": "",
            "date": "",
            "source": "tdnet",
            "url": href if href.startswith("http") else f"https://finance.yahoo.co.jp{href}",
        })
        if len(articles) >= 12:
            break

    logger.info(f"Yahoo JP scraped {len(articles)} articles for {ticker}")
    return articles


async def fetch_yahoo_us_news(ticker: str) -> list[dict]:
    """Yahoo Finance から US株ニュースを取得（JSON API）"""
    url = (
        f"https://query1.finance.yahoo.com/v1/finance/search"
        f"?q={ticker}&newsCount=10&quotesCount=0"
    )
    articles = []

    try:
        async with httpx.AsyncClient(
            headers={**HEADERS, "Accept": "application/json"},
            timeout=15,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"Yahoo Finance search failed for {ticker}: {e}")
        return []

    for item in data.get("news", []):
        title = item.get("title", "")
        if not title:
            continue
        articles.append({
            "title": title,
            "body": item.get("summary", ""),
            "date": "",
            "source": "tdnet",
        })

    logger.info(f"Yahoo US news got {len(articles)} articles for {ticker}")
    return articles


async def fetch_primary_news(ticker: str) -> list[dict]:
    """銘柄に応じた一次情報ニュースを取得"""
    is_japanese = ticker.upper().endswith(".T") or re.match(r"^\d{4}$", ticker)

    if is_japanese:
        articles = await fetch_yahoo_jp_news(ticker)
        return articles[:12]
    else:
        return await fetch_yahoo_us_news(ticker)
