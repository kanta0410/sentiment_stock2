"use client";

import React, { useEffect, useState } from "react";

interface SentimentGaugeProps {
  score: number; // -1.0 〜 +1.0
  label: string;
  size?: number;
  animated?: boolean;
}

function getColor(score: number): { stroke: string; glow: string; label: string } {
  if (score >= 0.5) return { stroke: "#34d399", glow: "rgba(52,211,153,0.6)", label: "Bullish" };
  if (score >= 0.2) return { stroke: "#6ee7b7", glow: "rgba(110,231,183,0.5)", label: "Slightly Bullish" };
  if (score >= -0.2) return { stroke: "#fbbf24", glow: "rgba(251,191,36,0.5)", label: "Neutral" };
  if (score >= -0.5) return { stroke: "#fb923c", glow: "rgba(251,146,60,0.4)", label: "Slightly Bearish" };
  return { stroke: "#f43f5e", glow: "rgba(244,63,94,0.6)", label: "Bearish" };
}

export default function SentimentGauge({
  score,
  label,
  size = 140,
  animated = true,
}: SentimentGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(animated ? 0 : score);

  useEffect(() => {
    if (!animated) { setAnimatedScore(score); return; }
    let start: number | null = null;
    const duration = 1200;
    const from = 0;
    const to = score;
    function step(ts: number) {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(from + (to - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }, [score, animated]);

  const { stroke, glow, label: statusLabel } = getColor(animatedScore);

  const cx = size / 2;
  const cy = size / 2;
  const r = (size / 2) * 0.72;
  const circumference = 2 * Math.PI * r;

  const arcAngle = 270;
  const arcLength = (arcAngle / 360) * circumference;
  const gap = circumference - arcLength;

  const normalized = (animatedScore + 1) / 2;
  const filled = normalized * arcLength;
  const dashOffset = arcLength - filled;

  const startAngle = 135;

  const labelColor =
    animatedScore >= 0.2
      ? "#34d399"
      : animatedScore >= -0.2
      ? "#fbbf24"
      : "#f43f5e";

  const filterId = `glow-${label.replace(/\s/g, "").replace(/[^a-zA-Z0-9]/g, "")}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size}>
          <defs>
            <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* トラック */}
          <circle
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={size * 0.065}
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${gap + 0.1}`}
            strokeDashoffset={0}
            transform={`rotate(${startAngle} ${cx} ${cy})`}
          />

          {/* フィル弧 */}
          <circle
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={stroke}
            strokeWidth={size * 0.065}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            strokeDashoffset={-dashOffset + (arcLength - filled)}
            transform={`rotate(${startAngle} ${cx} ${cy})`}
            filter={`url(#${filterId})`}
            style={{ transition: "stroke 0.5s ease" }}
          />

          {/* スコア値 */}
          <text
            x={cx} y={cy - size * 0.06}
            textAnchor="middle" dominantBaseline="middle"
            fill={stroke}
            fontSize={size * 0.22}
            fontWeight="800"
            fontFamily="'Inter', sans-serif"
            style={{ filter: `drop-shadow(0 0 6px ${glow})` }}
          >
            {animatedScore >= 0 ? "+" : ""}
            {animatedScore.toFixed(2)}
          </text>
          <text
            x={cx} y={cy + size * 0.14}
            textAnchor="middle" dominantBaseline="middle"
            fill={labelColor}
            fontSize={size * 0.1}
            fontWeight="600"
            fontFamily="'Inter', sans-serif"
          >
            {statusLabel}
          </text>
        </svg>

        <span style={{
          position: "absolute",
          bottom: size * 0.08,
          left: size * 0.0,
          fontSize: size * 0.085,
          color: "rgba(244,63,94,0.7)",
          fontWeight: 700,
          fontFamily: "'Inter', sans-serif",
        }}>
          -1
        </span>
        <span style={{
          position: "absolute",
          bottom: size * 0.08,
          right: size * 0.0,
          fontSize: size * 0.085,
          color: "rgba(52,211,153,0.7)",
          fontWeight: 700,
          fontFamily: "'Inter', sans-serif",
        }}>
          +1
        </span>
      </div>

      <div style={{ textAlign: "center" }}>
        <p style={{
          fontSize: "0.72rem",
          fontWeight: 700,
          color: "var(--text-secondary)",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}>
          {label}
        </p>
      </div>
    </div>
  );
}
