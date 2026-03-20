import asyncio
import sys
sys.path.append("backend")
from app.services.scraper.tdnet_scraper import fetch_primary_news

async def test():
    articles = await fetch_primary_news("7203.T")
    print(f"ARTICLES: {len(articles)}")
    for a in articles[:3]:
        print(f" - {a['title']}")

asyncio.run(test())
