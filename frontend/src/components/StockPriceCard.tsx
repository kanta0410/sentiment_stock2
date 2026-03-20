"use client";

import React from "react";
import type { PredictionResponse } from "@/types/api";
import SentimentGauge from "./SentimentGauge";

interface StockPriceCardProps {
  data: PredictionResponse;
}

const DIRECTION_CONFIG = {
  up: {
    icon: "▲",
    label: "Bullish",
    color: "#34d399",
    borderColor: "rgba(52,211,153,0.3)",
    bgColor: "rgba(52,211,153,0.06)",
    glowClass: "glow-green",
  },
  down: {
    icon: "▼",
    label: "Bearish",
    color: "#f43f5e",
    borderColor: "rgba(244,63,94,0.3)",
    bgColor: "rgba(244,63,94,0.06)",
    glowClass: "glow-red",
  },
  neutral: {
    icon: "━",
    label: "Neutral",
    color: "#fbbf24",
    borderColor: "rgba(251,191,36,0.3)",
    bgColor: "rgba(251,191,36,0.05)",
    glowClass: "",
  },
};

export default function StockPriceCard({ data }: StockPriceCardProps) {
  const dir = DIRECTION_CONFIG[data.predicted_direction];

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "1fr 1fr 1fr",
      gap: "16px",
      alignItems: "stretch",
    }}>
      {/* 株価カード */}
      <div
        className={`glass-card animate-fade-in-up ${dir.glowClass}`}
        style={{ padding: "28px 24px", position: "relative", overflow: "hidden", borderColor: dir.borderColor }}
      >
        <div style={{
          position: "absolute", top: "-40px", right: "-40px",
          width: "150px", height: "150px",
          background: dir.bgColor,
          borderRadius: "50%", filter: "blur(30px)", pointerEvents: "none",
        }} />

        <p style={{
          fontSize: "0.65rem", color: "var(--text-muted)",
          letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "6px",
        }}>
          銘柄コード
        </p>
        <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "18px" }}>
          <h2 style={{ fontSize: "1.8rem", fontWeight: 900, color: "var(--text-primary)", letterSpacing: "0.03em" }}>
            {data.ticker}
          </h2>
          {data.company_name && (
            <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              {data.company_name}
            </span>
          )}
        </div>

        <div style={{ height: "1px", background: "var(--border-subtle)", marginBottom: "18px" }} />

        <p style={{
          fontSize: "0.65rem", color: "var(--text-muted)",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "6px",
        }}>
          現在値
        </p>
        <p
          className="gradient-text-green animate-neon-flicker"
          style={{ fontSize: "2.8rem", fontWeight: 900, letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "16px" }}
        >
          ¥{data.current_price?.toLocaleString("ja-JP") ?? "---"}
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{
            background: dir.bgColor,
            border: `1px solid ${dir.borderColor}`,
            color: dir.color,
            borderRadius: "999px",
            padding: "5px 14px",
            fontSize: "0.85rem", fontWeight: 800,
            display: "flex", alignItems: "center", gap: "5px",
            textShadow: `0 0 8px ${dir.color}70`,
          }}>
            {dir.icon}{" "}
            {data.predicted_change_pct !== undefined && data.predicted_change_pct !== null
              ? `${data.predicted_change_pct >= 0 ? "+" : ""}${data.predicted_change_pct.toFixed(2)}%`
              : "---"}
          </span>
          <span style={{ fontSize: "0.8rem", color: dir.color, fontWeight: 700 }}>
            {dir.label}
          </span>
        </div>
      </div>

      {/* 一次情報センチメントゲージ */}
      <div
        className="glass-card animate-fade-in-up"
        style={{
          padding: "24px 16px",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          gap: "8px", animationDelay: "0.1s",
          border: "1px solid rgba(255,255,255,0.03)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "0.6rem", color: "var(--text-muted)", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: "2px" }}>
            Primary Source
          </p>
          <p style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.02em" }}>
            決算・適時開示
          </p>
        </div>
        <SentimentGauge
          score={data.scores?.fundamental ?? data.sentiment_score}
          label="一次情報"
          size={140}
        />
      </div>

      {/* 二次情報センチメントゲージ */}
      <div
        className="glass-card animate-fade-in-up"
        style={{
          padding: "24px 16px",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          gap: "8px", animationDelay: "0.2s",
          border: "1px solid rgba(255,255,255,0.03)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "0.6rem", color: "var(--text-muted)", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: "2px" }}>
            Secondary Source
          </p>
          <p style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.02em" }}>
            SNS・世論
          </p>
        </div>
        <SentimentGauge
          score={data.scores?.social ?? data.sentiment_score}
          label="二次情報"
          size={140}
        />
      </div>
    </div>
  );
}
