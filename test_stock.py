
import os
import sys
sys.path.append("backend")
from app.services.stock.price_fetcher import fetch_stock_info

info = fetch_stock_info("7203.T")
print(f"INFO: {info}")
