# Agent S
> **Quant-Style Sentiment Analysis Powered by Google Gemini 2.0-Flash**

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)

企業の**公式発表（TDnet/株探）**と、大衆の**SNS世論（Reddit）**をAIがリアルタイムに統合・時系列評価。  
単なるキーワード抽出ではない、**「情報の鮮度」と「信頼性」**を考慮した次世代の株価センチメント予測エンジンです。

---

## 🚀 Key Features | 主な機能

### 🔍 1. Hybrid Multi-Source Scraping
- **Primary Data (一次情報)**: TDnetおよび株探から適時開示・ニュースを高速スクレイピング。
- **Social Pulse (二次情報)**: Reddit API (PRAW) から銘柄に関連する各国の個人投資家のリアルタイムな反応を収集。

### 🧠 2. Advanced Quant-Logic Analysis
- **Recency Weighting (時系列重み付け)**:  
  情報の経過時間に基づき、スコアをダイナミックに減衰。分析基準日から24時間以内の情報を「最重要（1.2x）」と定義し、時間の経過とともに「既に市場に織り込まれた情報（0.6x〜）」として自動調整。
- **Influence Score (SNS影響度)**:  
  Upvotes数やコメント数を対数スケールで正規化し、爆発的に拡散している情報の「熱量」をセンチメントに反映。

### 📊 3. Reliability Index (信頼度インデックス)
AIが自身の判断根拠を「ソースの質 × 全体的な文脈の一致度（整合性）」の観点から 0.0〜1.0 で算出。不確かな情報に惑わされないための「判断の盤石さ」を提示します。

---

## 🎨 Professional UI Architecture | アーキテクチャ

````mermaid
graph LR
    subgraph Frontend [Next.js App]
        UI[Interactive Dashboard]
        Chart[Recharts Logic]
    end
    
    subgraph Backend [FastAPI Engine]
        API[REST & Prediction API]
        Scraper[Hybrid Scraper]
        Gemini[Gemini 2.0-Flash]
    end
    
    UI --> API
    API --> Scraper
    Scraper --> Gemini
````

---

## 🛠 Setup & Launch | セットアップ

### **環境変数設定 (.env)**
`backend/.env` に以下のキーを設定してください。
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
REDDIT_CLIENT_ID=YOUR_CLIENT_ID
REDDIT_CLIENT_SECRET=YOUR_CLIENT_SECRET
REDDIT_USER_AGENT=sentiment_stock_aggregator
```

### **1. サーバーの準備**
```bash
# Backend (FastAPI)
cd backend
pip install -r requirements.txt
python main.py

# Frontend (Next.js)
cd frontend
npm install
npm run dev
```

---

## 🧪 Documentation & Testing
今回のロジック検証のために作成されたスクリプトを利用して、一気通貫のデバッグが可能です。
```bash
python debug_analysis.py # トヨタ(7203.T)を例に、取得からスコアリングまでをテスト
```

---

## 🎯 Project Vision | 今後の展望
- **Global Sentiment Expansion**: X (Twitter) 等の多言語ソースの更なる統合。
- **Correlation Engine**: 過去のセンチメント推移と実際の株価変動の相関係数を算出し、予測精度を継続的に最適化。

---
Created as part of [Hakkason 2026/03]