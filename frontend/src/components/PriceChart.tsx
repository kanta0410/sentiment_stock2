"use client";

import React from "react";
import type { StockPricePoint } from "@/types/api";

interface PriceChartProps {
  prices: StockPricePoint[];
  ticker: string;
}

export default function PriceChart({ prices, ticker }: PriceChartProps) {
  if (!prices || prices.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)" }}>
        株価データがありません
      </div>
    );
  }

  const closes = prices.map((p) => p.close);
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const range = maxClose - minClose || 1;

  const W = 600;
  const H = 200;
  const PAD = { top: 20, right: 20, bottom: 40, left: 60 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const toX = (i: number) => PAD.left + (i / (prices.length - 1)) * innerW;
  const toY = (v: number) => PAD.top + innerH - ((v - minClose) / range) * innerH;

  const linePath = prices
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toX(i).toFixed(1)} ${toY(p.close).toFixed(1)}`)
    .join(" ");

  const areaPath =
    linePath +
    ` L ${toX(prices.length - 1).toFixed(1)} ${(PAD.top + innerH).toFixed(1)}` +
    ` L ${toX(0).toFixed(1)} ${(PAD.top + innerH).toFixed(1)} Z`;

  const isUp = prices.length >= 2 && closes[closes.length - 1] >= closes[0];
  const lineColor = isUp ? "#10b981" : "#ef4444";
  const gradId = `grad-${ticker.replace(/[^a-zA-Z0-9]/g, "_")}`;

  const xLabels = [0, Math.floor(prices.length / 2), prices.length - 1];
  const yTicks = Array.from({ length: 5 }, (_, i) => minClose + (range * i) / 4);

  return (
    <div className="glass-card animate-fade-in-up" style={{ padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
          📈 株価チャート
        </h3>
        <div style={{ display: "flex", gap: "12px", fontSize: "0.8rem" }}>
          <span style={{ color: "var(--text-secondary)" }}>
            高値: <span style={{ color: "#10b981", fontWeight: 600 }}>¥{maxClose.toLocaleString("ja-JP")}</span>
          </span>
          <span style={{ color: "var(--text-secondary)" }}>
            安値: <span style={{ color: "#ef4444", fontWeight: 600 }}>¥{minClose.toLocaleString("ja-JP")}</span>
          </span>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          style={{ width: "100%", minWidth: "300px", height: "auto", display: "block" }}
          aria-label={`${ticker}の株価チャート`}
        >
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
              <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
            </linearGradient>
          </defs>

          {yTicks.map((v, i) => (
            <line key={i} x1={PAD.left} y1={toY(v)} x2={W - PAD.right} y2={toY(v)}
              stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
          ))}

          <path d={areaPath} fill={`url(#${gradId})`} />
          <path d={linePath} fill="none" stroke={lineColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {yTicks.map((v, i) => (
            <text key={i} x={PAD.left - 6} y={toY(v) + 4} textAnchor="end" fontSize="10" fill="rgba(139,154,184,0.7)">
              {v >= 1000 ? v.toFixed(0) : v.toFixed(2)}
            </text>
          ))}

          {xLabels.map((idx) => (
            <text key={idx} x={toX(idx)} y={H - 8} textAnchor="middle" fontSize="10" fill="rgba(139,154,184,0.7)">
              {prices[idx]?.date
                ? new Date(prices[idx].date).toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" })
                : ""}
            </text>
          ))}

          <circle cx={toX(prices.length - 1)} cy={toY(closes[closes.length - 1])}
            r="5" fill={lineColor} stroke="var(--bg-primary)" strokeWidth="2" />
        </svg>
      </div>
    </div>
  );
}
