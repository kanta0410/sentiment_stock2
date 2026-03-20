"""
Reddit SNS スクレイパー
認証不要の公開JSONエンドポイントを使用してRedditからデータを取得
"""
import logging
import re
import httpx

logger = logging.getLogger(__name__)

REDDIT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

SUBREDDITS_JP = ["stocks", "StockMarket", "JapanFinance", "japanstocks"]
SUBREDDITS_US = ["stocks", "StockMarket", "investing", "SecurityAnalysis"]


def _build_search_query(ticker: str) -> str:
    """ティッカーから検索クエリを構築"""
    clean = ticker.replace(".T", "").replace(".", "").strip()
    return clean


async def _search_subreddit(
    client: httpx.AsyncClient, subreddit: str, query: str, limit: int = 5
) -> list[dict]:
    """特定サブレディットで検索"""
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={query}&sort=new&limit={limit}&restrict_sr=true&t=month"
    )
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        results = []
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "")
            selftext = p.get("selftext", "")[:500]
            score = p.get("score", 0)
            num_comments = p.get("num_comments", 0)
            if not title:
                continue
            results.append({
                "title": title,
                "body": selftext,
                "score_upvotes": score,
                "num_comments": num_comments,
                "subreddit": subreddit,
                "source": "reddit",
            })
        return results
    except Exception as e:
        logger.warning(f"Reddit search failed for r/{subreddit} q={query}: {e}")
        return []


FINANCE_SUBREDDITS = {
    "stocks", "StockMarket", "investing", "wallstreetbets", "SecurityAnalysis",
    "ValueInvesting", "dividends", "ETFs", "options", "JapanFinance", "japanstocks",
}


async def _search_global_reddit(
    client: httpx.AsyncClient, query: str, limit: int = 8
) -> list[dict]:
    """Reddit全体で検索（金融関連サブレディットのみ）"""
    url = (
        f"https://www.reddit.com/search.json"
        f"?q={query}+stock+OR+shares+OR+earnings&sort=new&limit={limit * 3}&t=month&include_over_18=false"
    )
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        results = []
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "")
            selftext = p.get("selftext", "")[:500]
            score = p.get("score", 0)
            subreddit = p.get("subreddit", "")
            # 金融関連サブレディットのみ残す
            if not title or subreddit not in FINANCE_SUBREDDITS:
                continue
            results.append({
                "title": title,
                "body": selftext,
                "score_upvotes": score,
                "num_comments": p.get("num_comments", 0),
                "subreddit": subreddit,
                "source": "reddit",
            })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        logger.warning(f"Reddit global search failed for {query}: {e}")
        return []


async def fetch_reddit_sentiment(ticker: str) -> list[dict]:
    """
    ティッカーに関連するReddit投稿を収集。
    日本株の場合、英語・日本語両方で検索。
    """
    is_japanese = ticker.upper().endswith(".T") or re.match(r"^\d{4}$", ticker)
    query = _build_search_query(ticker)
    subreddits = SUBREDDITS_JP if is_japanese else SUBREDDITS_US

    all_posts: list[dict] = []

    async with httpx.AsyncClient(headers=REDDIT_HEADERS, follow_redirects=True) as client:
        # サブレディット別検索
        for sub in subreddits:
            posts = await _search_subreddit(client, sub, query, limit=10)
            all_posts.extend(posts)
            if len(all_posts) >= 12:
                break

        # まだ少なければグローバル検索
        if len(all_posts) < 5:
            global_posts = await _search_global_reddit(client, query, limit=6)
            all_posts.extend(global_posts)

    # 重複除去（タイトルベース）
    seen_titles: set[str] = set()
    unique_posts = []
    for post in all_posts:
        key = post["title"][:50]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_posts.append(post)

    # アップボート数でソート（人気順）
    unique_posts.sort(key=lambda x: x.get("score_upvotes", 0), reverse=True)

    logger.info(f"Reddit scraped {len(unique_posts)} posts for {ticker}")
    return unique_posts[:10]
