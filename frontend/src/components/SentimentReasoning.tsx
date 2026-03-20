"use client";

import React from "react";
import type { SentimentResult } from "@/types/api";

interface SentimentReasoningProps {
  articles: SentimentResult[];
  ticker: string;
}

const SOURCE_CONFIG: Record<string, { label: string; icon: string }> = {
  TDnet: { label: "TDnet 適時開示", icon: "📋" },
  tdnet: { label: "TDnet 適時開示", icon: "📋" },
  kabutan: { label: "株探", icon: "📋" },
  reddit: { label: "Reddit", icon: "💬" },
  manual: { label: "その他", icon: "📄" },
};

function getFactorConfig(label: "positive" | "neutral" | "negative") {
  if (label === "positive") {
    return {
      borderColor: "rgba(52, 211, 153, 0.35)",
      bgColor: "rgba(52, 211, 153, 0.06)",
      headerBg: "rgba(52, 211, 153, 0.12)",
      scoreColor: "#34d399",
      glow: "rgba(52, 211, 153, 0.2)",
      barColor: "#34d399",
      tagBg: "rgba(52, 211, 153, 0.15)",
      tagBorder: "rgba(52, 211, 153, 0.4)",
      tagColor: "#34d399",
      tagText: "▲ ポジティブ要因",
    };
  }
  if (label === "negative") {
    return {
      borderColor: "rgba(244, 63, 94, 0.35)",
      bgColor: "rgba(244, 63, 94, 0.06)",
      headerBg: "rgba(244, 63, 94, 0.1)",
      scoreColor: "#f43f5e",
      glow: "rgba(244, 63, 94, 0.2)",
      barColor: "#f43f5e",
      tagBg: "rgba(244, 63, 94, 0.15)",
      tagBorder: "rgba(244, 63, 94, 0.4)",
      tagColor: "#f43f5e",
      tagText: "▼ ネガティブ要因",
    };
  }
  return {
    borderColor: "rgba(251, 191, 36, 0.3)",
    bgColor: "rgba(251, 191, 36, 0.04)",
    headerBg: "rgba(251, 191, 36, 0.08)",
    scoreColor: "#fbbf24",
    glow: "rgba(251, 191, 36, 0.15)",
    barColor: "#fbbf24",
    tagBg: "rgba(251, 191, 36, 0.12)",
    tagBorder: "rgba(251, 191, 36, 0.35)",
    tagColor: "#fbbf24",
    tagText: "━ 中立要因",
  };
}

export default function SentimentReasoning({ articles, ticker }: SentimentReasoningProps) {
  if (!articles || articles.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
        分析データがありません
      </div>
    );
  }

  const sorted = [...articles].sort((a, b) => {
    const order = { positive: 0, negative: 1, neutral: 2 };
    return order[a.label] - order[b.label];
  });

  const positiveCount = articles.filter((a) => a.label === "positive").length;
  const negativeCount = articles.filter((a) => a.label === "negative").length;
  const neutralCount = articles.filter((a) => a.label === "neutral").length;

  return (
    <div className="glass-card animate-fade-in-up" style={{ padding: "24px 28px", position: "relative", overflow: "hidden" }}>
      <div style={{
        position: "absolute", top: "-60px", right: "-60px",
        width: "200px", height: "200px",
        background: "radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "36px", height: "36px", borderRadius: "9px",
            background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px",
          }}>
            📊
          </div>
          <div>
            <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "2px" }}>
              センチメント分析根拠
            </p>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 800, color: "var(--text-primary)" }}>
              {ticker} — スコア算出の要因分析
            </h3>
          </div>
        </div>

        <div style={{ display: "flex", gap: "6px" }}>
          <span style={{ background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.3)", color: "#34d399", borderRadius: "6px", padding: "3px 10px", fontSize: "0.72rem", fontWeight: 700 }}>
            ▲ ポジ {positiveCount}件
          </span>
          <span style={{ background: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.3)", color: "#f43f5e", borderRadius: "6px", padding: "3px 10px", fontSize: "0.72rem", fontWeight: 700 }}>
            ▼ ネガ {negativeCount}件
          </span>
          {neutralCount > 0 && (
            <span style={{ background: "rgba(251,191,36,0.1)", border: "1px solid rgba(251,191,36,0.25)", color: "#fbbf24", borderRadius: "6px", padding: "3px 10px", fontSize: "0.72rem", fontWeight: 700 }}>
              ━ 中立 {neutralCount}件
            </span>
          )}
        </div>
      </div>

      <div style={{ height: "1px", background: "linear-gradient(90deg, transparent, rgba(56,189,248,0.25), rgba(52,211,153,0.15), transparent)", marginBottom: "18px" }} />

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {sorted.map((article, idx) => (
          <FactorCard key={idx} article={article} index={idx} />
        ))}
      </div>
    </div>
  );
}

function FactorCard({ article, index }: { article: SentimentResult; index: number }) {
  const cfg = getFactorConfig(article.label);
  const src = SOURCE_CONFIG[article.source] ?? { label: article.source, icon: "📄" };
  const barWidth = `${Math.round(Math.abs(article.score) * 100)}%`;

  return (
    <div
      style={{
        background: cfg.bgColor,
        border: `1px solid ${cfg.borderColor}`,
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: `0 0 20px ${cfg.glow}`,
        animationDelay: `${index * 0.07}s`,
        animationFillMode: "both",
      }}
      className="animate-fade-in-up"
    >
      <div style={{ background: cfg.headerBg, padding: "10px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            background: cfg.tagBg, border: `1px solid ${cfg.tagBorder}`,
            color: cfg.tagColor, borderRadius: "4px", padding: "2px 9px",
            fontSize: "0.7rem", fontWeight: 800, letterSpacing: "0.04em",
            textShadow: `0 0 8px ${cfg.scoreColor}60`,
          }}>
            {cfg.tagText}
          </span>
          <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "3px" }}>
            {src.icon} {src.label}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "80px", height: "4px", background: "rgba(255,255,255,0.08)", borderRadius: "999px", overflow: "hidden" }}>
            <div style={{
              width: barWidth, height: "100%", background: cfg.barColor,
              borderRadius: "999px", boxShadow: `0 0 6px ${cfg.barColor}`,
              marginLeft: article.score < 0 ? "auto" : undefined,
            }} />
          </div>
          <span style={{
            fontSize: "0.82rem", fontWeight: 800, color: cfg.scoreColor,
            textShadow: `0 0 8px ${cfg.scoreColor}80`,
            minWidth: "48px", textAlign: "right",
            fontFamily: "'Inter', monospace",
          }}>
            {article.score >= 0 ? "+" : ""}{article.score.toFixed(3)}
          </span>
        </div>
      </div>

      <div style={{ padding: "12px 16px" }}>
        <p style={{ color: "var(--text-primary)", fontSize: "0.85rem", fontWeight: 600, lineHeight: 1.5, marginBottom: "8px" }}>
          {article.title}
        </p>
        <div style={{ borderLeft: `3px solid ${cfg.borderColor}`, paddingLeft: "12px", marginTop: "4px" }}>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", lineHeight: 1.7 }}>
            {article.explanation}
          </p>
        </div>
      </div>
    </div>
  );
}
