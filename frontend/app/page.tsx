"use client";

import React, { useState, useCallback } from "react";
import { fetchPrediction } from "@/lib/api";
import type { PredictionResponse } from "@/types/api";
import StockPriceCard from "@/components/StockPriceCard";
import AIAnalysisEngine from "@/components/AIAnalysisEngine";
import NewsList from "@/components/NewsList";
import SentimentReasoning from "@/components/SentimentReasoning";
import PriceChart from "@/components/PriceChart";

const POPULAR_TICKERS = [
  { label: "トヨタ", value: "7203.T" },
  { label: "任天堂", value: "7974.T" },
  { label: "ソニー", value: "6758.T" },
  { label: "ソフトバンクG", value: "9984.T" },
  { label: "Apple", value: "AAPL" },
  { label: "NVIDIA", value: "NVDA" },
];

function HeaderSearchBar({
  onSearch,
  isLoading,
}: {
  onSearch: (ticker: string) => void;
  isLoading: boolean;
}) {
  const [ticker, setTicker] = useState("7203.T");
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) onSearch(ticker.trim().toUpperCase());
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, maxWidth: "600px" }}
    >
      <div style={{ position: "relative", flex: 1 }}>
        {isLoading && (
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, height: "2px",
            background: "linear-gradient(90deg, transparent, #38bdf8, #34d399, transparent)",
            animation: "scan 1.8s linear infinite",
            borderRadius: "999px",
          }} />
        )}
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="銘柄コードを入力 (例: 7203.T / AAPL)"
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: "100%",
            background: focused ? "rgba(56,189,248,0.06)" : "rgba(255,255,255,0.04)",
            border: `1px solid ${focused ? "rgba(56,189,248,0.45)" : "rgba(255,255,255,0.08)"}`,
            borderRadius: "12px", padding: "10px 20px",
            color: "var(--text-primary)", fontSize: "0.95rem", fontWeight: 600,
            outline: "none", transition: "all 0.3s cubic-bezier(0.19, 1, 0.22, 1)",
            letterSpacing: "0.04em",
            boxShadow: focused ? "0 0 0 3px rgba(56,189,248,0.1)" : "none",
          }}
        />
      </div>
      <button
        type="submit"
        disabled={isLoading}
        style={{
          padding: "10px 20px",
          background: isLoading ? "rgba(100,100,120,0.4)" : "linear-gradient(135deg, #0284c7, #38bdf8)",
          border: "none", borderRadius: "10px",
          color: "white", fontWeight: 700, fontSize: "0.9rem",
          cursor: isLoading ? "not-allowed" : "pointer",
          transition: "all 0.2s",
          letterSpacing: "0.04em",
          display: "flex", alignItems: "center", gap: "6px",
          flexShrink: 0,
          boxShadow: isLoading ? "none" : "0 4px 16px rgba(56,189,248,0.3)",
        }}
      >
        {isLoading ? (
          <span style={{
            width: "14px", height: "14px",
            border: "2px solid rgba(255,255,255,0.2)",
            borderTopColor: "white", borderRadius: "50%",
            display: "inline-block",
          }} className="animate-spin-slow" />
        ) : (
          "🚀 分析"
        )}
      </button>
    </form>
  );
}

export default function DashboardPage() {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async (ticker: string) => {
    setIsLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const data = await fetchPrediction(ticker, 30);
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#05080A", position: "relative", color: "#f8fafc" }}>
      {/* サイバーグリッド背景 */}
      <div
        className="cyber-grid"
        style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, opacity: 0.35 }}
      />
      {/* アンビエントグロー */}
      <div style={{
        position: "fixed", top: "15%", left: "5%",
        width: "500px", height: "400px",
        background: "radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%)",
        pointerEvents: "none", zIndex: 0,
      }} />
      <div style={{
        position: "fixed", bottom: "10%", right: "8%",
        width: "400px", height: "300px",
        background: "radial-gradient(circle, rgba(52,211,153,0.04) 0%, transparent 70%)",
        pointerEvents: "none", zIndex: 0,
      }} />

      {/* ヘッダー */}
      <header style={{
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        backdropFilter: "blur(24px)",
        background: "rgba(5,8,10,0.92)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{
          maxWidth: "1400px", margin: "0 auto",
          padding: "0 28px", height: "58px",
          display: "flex", alignItems: "center", gap: "20px",
        }}>
          {/* ロゴ */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
            <div style={{
              width: "32px", height: "32px", borderRadius: "8px",
              background: "linear-gradient(135deg, #0f3460, #38bdf8)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "15px", boxShadow: "0 0 16px rgba(56,189,248,0.3)",
            }}>
              📊
            </div>
            <div>
              <p style={{ fontSize: "0.88rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "0.01em", lineHeight: 1.2 }}>
                Sentiment Stock Predictor
              </p>
              <p style={{ fontSize: "0.58rem", color: "var(--text-muted)", letterSpacing: "0.08em" }}>
                AI-POWERED MARKET ANALYSIS
              </p>
            </div>
          </div>

          <HeaderSearchBar onSearch={handleSearch} isLoading={isLoading} />

          {/* クイック選択 */}
          <div style={{ display: "flex", gap: "5px", flexShrink: 0 }}>
            {POPULAR_TICKERS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => handleSearch(t.value)}
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderRadius: "6px", padding: "4px 10px",
                  color: "var(--text-secondary)", fontSize: "0.7rem", fontWeight: 600,
                  cursor: "pointer", transition: "all 0.15s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "rgba(56,189,248,0.12)";
                  (e.currentTarget as HTMLButtonElement).style.color = "#38bdf8";
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(56,189,248,0.3)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.04)";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255,255,255,0.07)";
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", gap: "6px", flexShrink: 0 }}>
            <span style={{
              background: "rgba(52,211,153,0.08)", border: "1px solid rgba(52,211,153,0.22)",
              color: "#34d399", borderRadius: "6px", padding: "3px 10px",
              fontSize: "0.65rem", fontWeight: 700, letterSpacing: "0.05em",
              display: "flex", alignItems: "center", gap: "4px",
            }}>
              <span style={{
                width: "5px", height: "5px", background: "#34d399",
                borderRadius: "50%", display: "inline-block", boxShadow: "0 0 6px #34d399",
              }} className="animate-pulse-glow" />
              GEMINI AI
            </span>
          </div>
        </div>
      </header>

      <main style={{
        maxWidth: "1400px", margin: "0 auto",
        padding: "24px 28px 60px",
        position: "relative", zIndex: 1,
      }}>
        {isLoading && <LoadingState />}
        {error && !isLoading && <ErrorState message={error} />}
        {!prediction && !isLoading && !error && <EmptyState />}

        {prediction && !isLoading && (
          <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
            <StockPriceCard data={prediction} />
            <AIAnalysisEngine
              summary={prediction.sentiment_summary}
              ticker={prediction.ticker}
              direction={prediction.predicted_direction}
              confidence={prediction.confidence}
              sentimentScore={prediction.sentiment_score}
              analysis={prediction.analysis}
              scores={prediction.scores}
              judgment={prediction.judgment}
            />
            {prediction.news_articles.length > 0 && (
              <SentimentReasoning articles={prediction.news_articles} ticker={prediction.ticker} />
            )}
            {prediction.news_articles.length > 0 && (
              <NewsList articles={prediction.news_articles} />
            )}
            {prediction.price_history.length > 0 && (
              <PriceChart prices={prediction.price_history} ticker={prediction.ticker} />
            )}
          </div>
        )}
      </main>

      <footer style={{
        borderTop: "1px solid rgba(255,255,255,0.04)",
        padding: "16px 28px", textAlign: "center",
        color: "var(--text-muted)", fontSize: "0.7rem",
        position: "relative", zIndex: 1,
      }}>
        <p>
          Sentiment Stock Predictor &copy; 2026 —{" "}
          <span className="neon-text-blue">Gemini AI</span> ・ TDnet 適時開示 ・ Reddit
        </p>
        <p style={{ marginTop: "3px", opacity: 0.55 }}>
          本ツールは投資助言ではありません。投資判断は自己責任でお願いします。
        </p>
      </footer>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="glass-card" style={{ padding: "56px 32px", textAlign: "center", position: "relative", overflow: "hidden" }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "2px",
        background: "linear-gradient(90deg, transparent, #38bdf8, #34d399, transparent)",
        animation: "scan 2s linear infinite",
      }} />
      <div style={{
        width: "52px", height: "52px",
        border: "2px solid rgba(56,189,248,0.15)",
        borderTopColor: "#38bdf8", borderRightColor: "#34d399",
        borderRadius: "50%", margin: "0 auto 18px",
      }} className="animate-spin-slow" />
      <p style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: "1rem", marginBottom: "6px" }}>
        解析中...
      </p>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
        TDnet 適時開示・Reddit を収集し、Gemini AI がセンチメント分析を実行しています
      </p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="glass-card glow-red" style={{ padding: "32px", textAlign: "center", borderColor: "rgba(244,63,94,0.3)" }}>
      <p style={{ fontSize: "2rem", marginBottom: "10px" }}>⚠️</p>
      <p style={{ color: "#f43f5e", fontWeight: 700, marginBottom: "8px" }}>エラーが発生しました</p>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{message}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="glass-card" style={{ padding: "80px 32px", textAlign: "center" }}>
      <p style={{ fontSize: "3rem", marginBottom: "16px" }}>📈</p>
      <p style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: "1.1rem", marginBottom: "8px" }}>
        銘柄を入力して分析を開始
      </p>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "24px" }}>
        上部の検索バーにティッカーシンボルを入力してください
      </p>
      <div style={{ display: "flex", justifyContent: "center", gap: "12px", flexWrap: "wrap" }}>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>例：</span>
        {["7203.T（トヨタ）", "AAPL（Apple）", "NVDA（NVIDIA）", "9984.T（ソフトバンク）"].map((ex) => (
          <span key={ex} style={{
            background: "rgba(56,189,248,0.06)", border: "1px solid rgba(56,189,248,0.15)",
            color: "#38bdf8", borderRadius: "6px", padding: "3px 10px", fontSize: "0.78rem",
          }}>
            {ex}
          </span>
        ))}
      </div>
    </div>
  );
}
