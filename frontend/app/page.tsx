"use client";

import React, { useState, useCallback } from "react";
import { fetchPrediction } from "@/lib/api";
import type { PredictionResponse } from "@/types/api";
import AIAnalysisEngine from "@/components/AIAnalysisEngine";
import PriceChart from "@/components/PriceChart";
import SentimentGauge from "@/components/SentimentGauge";
import SentimentReasoning from "@/components/SentimentReasoning";
import StockPriceCard from "@/components/StockPriceCard";
import NewsList from "@/components/NewsList";


/* ── 人気銘柄リスト ── */
const POPULAR_TICKERS = [
  { label: "トヨタ", value: "7203.T" },
  { label: "任天堂", value: "7974.T" },
  { label: "ソニー", value: "6758.T" },
  { label: "ソフトバンクG", value: "9984.T" },
  { label: "Apple", value: "AAPL" },
  { label: "NVIDIA", value: "NVDA" },
];

/* ── ヘッダー内サーチバー ── */
// page_ui.tsx の (ticker, days) シグネチャを維持しつつ、
// page.tsx の豊かなスタイル（フォーカスグロー・スピナーボタン）を採用
function HeaderSearchBar({
  onSearch,
  isLoading,
}: {
  onSearch: (ticker: string, days: number) => void;
  isLoading: boolean;
}) {
  const [ticker, setTicker] = useState("");
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) onSearch(ticker.trim().toUpperCase(), 30);
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, maxWidth: "600px" }}
    >
      <div style={{ position: "relative", flex: 1 }}>
        {/* スキャンラインアニメーション（ローディング中） */}
        {isLoading && (
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, height: "2px",
            background: "linear-gradient(90deg, transparent, #38bdf8, #34d399, transparent)",
            animation: "scan 1.8s linear infinite",
            borderRadius: "999px",
          }} />
        )}
        <input
          id="header-ticker-input"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="銘柄コードを入力 (例: 7203.T / AAPL)"
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: "100%",
            background: focused ? "rgba(56,189,248,0.06)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${focused ? "rgba(56,189,248,0.45)" : "rgba(255,255,255,0.04)"}`,
            borderRadius: "12px",
            padding: "10px 20px",
            color: "var(--text-primary)",
            fontSize: "0.95rem",
            fontWeight: 600,
            outline: "none",
            transition: "all 0.3s cubic-bezier(0.19, 1, 0.22, 1)",
            letterSpacing: "0.04em",
            boxShadow: focused ? "0 0 0 3px rgba(56,189,248,0.1)" : "none",
          }}
        />
      </div>
      {/* page.tsx のスタイリッシュなボタン＋スピナーを採用 */}
      <button
        id="header-predict-btn"
        type="submit"
        disabled={isLoading}
        style={{
          padding: "10px 24px",
          background: isLoading
            ? "rgba(100,100,120,0.4)"
            : "linear-gradient(135deg, #0284c7, #38bdf8)",
          border: "none",
          borderRadius: "12px",
          color: "white",
          fontWeight: 700,
          fontSize: "0.85rem",
          cursor: isLoading ? "not-allowed" : "pointer",
          transition: "all 0.2s",
          letterSpacing: "0.04em",
          whiteSpace: "nowrap",
          display: "flex",
          alignItems: "center",
          gap: "6px",
          flexShrink: 0,
          boxShadow: isLoading ? "none" : "0 0 16px rgba(56,189,248,0.3)",
        }}
      >
        {isLoading ? (
          <span
            style={{
              width: "14px", height: "14px",
              border: "2px solid rgba(255,255,255,0.2)",
              borderTopColor: "white", borderRadius: "50%",
              display: "inline-block",
            }}
            className="animate-spin-slow"
          />
        ) : (
          "🚀 ANALYZE"
        )}
      </button>
    </form>
  );
}

export default function DashboardPage() {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // (ticker, days) シグネチャを維持
  const handleSearch = useCallback(async (ticker: string, days: number = 30) => {
    setIsLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const data = await fetchPrediction(ticker, days);
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#06090c", position: "relative", color: "#f8fafc" }}>
      {/* 高級感のある背景装飾 */}
      <div
        style={{
          position: "fixed", inset: 0,
          backgroundImage:
            "radial-gradient(circle at 50% 0%, rgba(56,189,248,0.06) 0%, transparent 40%), radial-gradient(circle at 100% 100%, rgba(52,211,153,0.04) 0%, transparent 35%)",
          pointerEvents: "none", zIndex: 0,
        }}
      />
      {/* アンビエントグロー（page.tsx より） */}
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
      {/* サイバーグリッド背景 */}
      <div className="cyber-grid" style={{ position: "fixed", inset: 0, opacity: 0.15, pointerEvents: "none", zIndex: 0 }} />

      {/* ───── ヘッダー ───── */}
      <header style={{
        borderBottom: "1px solid rgba(255,255,255,0.03)",
        backdropFilter: "blur(40px)",
        background: "rgba(6,9,12,0.85)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{
          maxWidth: "1360px", margin: "0 auto",
          padding: "0 40px", height: "64px",
          display: "flex", alignItems: "center", gap: "20px",
        }}>
          {/* ロゴ */}
          <div style={{ display: "flex", alignItems: "center", gap: "14px", flexShrink: 0 }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "10px",
              background: "linear-gradient(135deg, #0e1116, #1a232e)",
              border: "1px solid rgba(56,189,248,0.25)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "18px", boxShadow: "0 0 20px rgba(56,189,248,0.1)",
            }}>
              📊
            </div>
            <div>
              <p style={{ fontSize: "0.9rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "0.02em", lineHeight: 1.2 }}>
                Sentiment Predictor
              </p>
              <p style={{ fontSize: "0.55rem", color: "var(--text-muted)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
                AI-POWERED MARKET ANALYSIS
              </p>
            </div>
          </div>

          <HeaderSearchBar onSearch={handleSearch} isLoading={isLoading} />

          {/* クイック選択ボタン（page.tsx より） */}
          <div style={{ display: "flex", gap: "5px", flexShrink: 0 }}>
            {POPULAR_TICKERS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => handleSearch(t.value, 30)}
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

          {/* 接続ステータスバッジ */}
          <div style={{ marginLeft: "auto", display: "flex", gap: "6px", alignItems: "center", flexShrink: 0 }}>
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

      {/* ───── メインコンテンツ ───── */}
      <main style={{
        maxWidth: "1360px",
        margin: "0 auto",
        padding: "40px",
        position: "relative",
        zIndex: 1,
      }}>
        <div style={{ minHeight: "600px" }}>
          {isLoading && <LoadingState />}
          {error && !isLoading && <ErrorState message={error} />}
          {!prediction && !isLoading && !error && <EmptyState />}

          {prediction && !isLoading && (
            <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
              {/* 株価カード */}
              <StockPriceCard data={prediction} />

              {/* チャート & センチメントゲージ (横並び) */}
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "340px 1fr", 
                gap: "28px", 
                alignItems: "stretch" 
              }}>
                {prediction.price_history && prediction.price_history.length > 0 ? (
                  <PriceChart prices={prediction.price_history} ticker={prediction.ticker} />
                ) : (
                  <div className="glass-card" style={{ padding: "40px", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
                    価格履歴データがありません
                  </div>
                )}
                
                <div className="glass-card" style={{ 
                  padding: "24px", 
                  display: "flex", 
                  justifyContent: "center", 
                  alignItems: "center", 
                  flexDirection: "column",
                  background: "rgba(56,189,248,0.03)",
                }}>
                  <SentimentGauge score={prediction.sentiment_score} label="総合センチメント" size={280} />
                </div>
              </div>

              {/* AI分析エンジン */}
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

              {/* センチメント根拠 */}
              {prediction.news_articles.length > 0 && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "28px" }}>
                  <SentimentReasoning articles={prediction.news_articles} ticker={prediction.ticker} />
                </div>
              )}

              {/* ニュース一覧 */}
              {prediction.news_articles.length > 0 && (
                <NewsList articles={prediction.news_articles} />
              )}
            </div>
          )}
        </div>
      </main>

      {/* フッター（page.tsx のより詳細な内容を採用） */}
      <footer style={{
        borderTop: "1px solid rgba(255,255,255,0.02)",
        padding: "24px 40px", textAlign: "center",
        color: "var(--text-muted)", fontSize: "0.65rem",
        position: "relative", zIndex: 1,
      }}>
        <p style={{ letterSpacing: "0.05em" }}>
          SENTIMENT STOCK PREDICTOR &copy; 2026 —{" "}
          <span className="neon-text-blue">POWERED BY GEMINI AI</span> ・ TDnet 適時開示 ・ Reddit
        </p>
        <p style={{ marginTop: "4px", opacity: 0.55 }}>
          本ツールは投資助言ではありません。投資判断は自己責任でお願いします。
        </p>
      </footer>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="glass-card" style={{ padding: "80px 40px", textAlign: "center", position: "relative", overflow: "hidden" }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "2px",
        background: "linear-gradient(90deg, transparent, #38bdf8, #34d399, transparent)",
        animation: "scan 2s linear infinite",
      }} />
      <div style={{
        width: "52px", height: "52px",
        border: "2px solid rgba(56,189,248,0.1)",
        borderTopColor: "#38bdf8", borderRightColor: "#34d399",
        borderRadius: "50%", margin: "0 auto 24px",
      }} className="animate-spin-slow" />
      <p style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: "8px" }}>銘柄をAIが詳細解析中</p>
      <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
        TDnet 適時開示・Reddit を収集し、Gemini AI がセンチメント分析を実行しています...
      </p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="glass-card" style={{ padding: "40px", textAlign: "center", borderColor: "rgba(244,63,94,0.2)" }}>
      <p style={{ fontSize: "2rem", marginBottom: "16px" }}>⚠️</p>
      <p style={{ color: "#f43f5e", fontWeight: 700, marginBottom: "8px" }}>解析に失敗しました</p>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>{message}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="glass-card" style={{ padding: "100px 40px", textAlign: "center" }}>
      <p style={{ fontSize: "3rem", marginBottom: "20px" }}>📈</p>
      <p style={{ fontWeight: 800, fontSize: "1.3rem", marginBottom: "12px", color: "var(--text-primary)" }}>
        銘柄レポートを生成します
      </p>
      <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", maxWidth: "400px", margin: "0 auto 24px" }}>
        最先端のAIが最新の適時開示情報と世論を統合し、即時にセンチメントを可視化します。
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