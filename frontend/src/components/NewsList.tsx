"use client";

import React from "react";
import type { SentimentResult } from "@/types/api";

interface NewsListProps {
  articles: SentimentResult[];
}

const SOURCE_LABELS: Record<string, string> = {
  tdnet: "TDnet",
  kabutan: "株探",
  reddit: "Reddit",
  manual: "その他",
};

export default function NewsList({ articles }: NewsListProps) {
  if (!articles || articles.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)" }}>
        分析した記事がありません
      </div>
    );
  }

  return (
    <div className="glass-card animate-fade-in-up" style={{ padding: "24px" }}>
      <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "20px" }}>
        📰 ニュース＆投稿センチメント
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {articles.map((article, idx) => (
          <NewsItem key={idx} article={article} />
        ))}
      </div>
    </div>
  );
}

function NewsItem({ article }: { article: SentimentResult }) {
  const isPositive = article.label === "positive";
  const isNegative = article.label === "negative";

  const scoreColor = isPositive ? "#10b981" : isNegative ? "#ef4444" : "#f59e0b";
  const scoreWidth = `${Math.abs(article.score) * 100}%`;

  const badgeClass = isPositive ? "badge-positive" : isNegative ? "badge-negative" : "badge-neutral";
  const labelText = isPositive ? "強気" : isNegative ? "弱気" : "中立";

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "12px", padding: "14px 16px",
        transition: "border-color 0.2s, background 0.2s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(59,130,246,0.2)";
        (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.04)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-subtle)";
        (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.02)";
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "8px" }}>
        <p style={{ color: "var(--text-primary)", fontSize: "0.875rem", fontWeight: 500, lineHeight: 1.5, flex: 1 }}>
          {article.title}
        </p>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px", flexShrink: 0 }}>
          <span className={badgeClass}>{labelText}</span>
          <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
            {SOURCE_LABELS[article.source] ?? article.source}
          </span>
        </div>
      </div>

      <div style={{ marginBottom: "8px" }}>
        <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: "999px", height: "4px", overflow: "hidden" }}>
          <div
            style={{
              width: scoreWidth, height: "100%",
              background: scoreColor, borderRadius: "999px",
              boxShadow: `0 0 6px ${scoreColor}80`,
              marginLeft: article.score < 0 ? "auto" : undefined,
            }}
          />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "4px" }}>
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>スコア</span>
          <span style={{ fontSize: "0.72rem", color: scoreColor, fontWeight: 700 }}>
            {article.score >= 0 ? "+" : ""}{article.score.toFixed(3)}
          </span>
        </div>
      </div>

      <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", lineHeight: 1.6 }}>
        💬 {article.explanation}
      </p>
    </div>
  );
}
