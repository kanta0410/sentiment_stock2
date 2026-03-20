"use client";

import React, { useEffect, useState, useRef } from "react";

interface AIAnalysisEngineProps {
  summary: string;
  ticker: string;
  direction: "up" | "down" | "neutral";
  confidence: number;
  sentimentScore: number;
  analysis?: {
    fundamental_reason: string;
    social_insight: string;
    risk_factor: string;
  };
  scores?: {
    fundamental: number;
    social: number;
    gap: number;
  };
  judgment?: "BUY" | "HOLD" | "WATCH";
}

const BULLISH_KEYWORDS = [
  "増益", "最高益", "上昇", "買い", "強気", "好調", "増収", "回復",
  "Bullish", "上方修正", "好業績", "利益増加", "成長", "ブレイクアウト",
  "強い", "堅調",
];
const BEARISH_KEYWORDS = [
  "減益", "下落", "売り", "弱気", "不調", "懸念", "リスク", "警戒",
  "Bearish", "下方修正", "赤字", "損失", "不安", "低迷",
];
const NEUTRAL_KEYWORDS = ["横ばい", "様子見", "中立", "Neutral", "安定", "維持"];

function highlightText(text: string): React.ReactNode[] {
  const allKeywords = [
    ...BULLISH_KEYWORDS.map((k) => ({ word: k, type: "bullish" })),
    ...BEARISH_KEYWORDS.map((k) => ({ word: k, type: "bearish" })),
    ...NEUTRAL_KEYWORDS.map((k) => ({ word: k, type: "neutral" })),
  ];

  const pattern = new RegExp(
    `(${allKeywords.map((k) => k.word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
    "g"
  );

  const parts = text.split(pattern);
  return parts.map((part, i) => {
    const kw = allKeywords.find((k) => k.word === part);
    if (!kw) return <span key={i}>{part}</span>;
    if (kw.type === "bullish")
      return <span key={i} className="neon-badge" style={{ margin: "0 2px" }}>{part}</span>;
    if (kw.type === "bearish")
      return <span key={i} className="neon-badge-red" style={{ margin: "0 2px" }}>{part}</span>;
    return (
      <span key={i} style={{ color: "#fbbf24", fontWeight: 700, textShadow: "0 0 8px rgba(251,191,36,0.4)" }}>
        {part}
      </span>
    );
  });
}

function useTypingEffect(text: string, speed = 16) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    let idx = 0;
    function tick() {
      idx++;
      setDisplayed(text.slice(0, idx));
      if (idx < text.length) {
        timerRef.current = setTimeout(tick, speed);
      } else {
        setDone(true);
      }
    }
    timerRef.current = setTimeout(tick, 300);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [text, speed]);

  return { displayed, done };
}

const DIRECTION_LABELS = {
  up: { label: "上昇予測", color: "#34d399", icon: "▲", badgeClass: "neon-badge" },
  down: { label: "下落予測", color: "#f43f5e", icon: "▼", badgeClass: "neon-badge-red" },
  neutral: { label: "横ばい予測", color: "#fbbf24", icon: "━", badgeClass: "" },
};

export default function AIAnalysisEngine({
  summary,
  ticker,
  direction,
  confidence,
  sentimentScore,
  analysis,
  scores,
  judgment,
}: AIAnalysisEngineProps) {
  const { displayed, done } = useTypingEffect(summary, 16);
  const dir = DIRECTION_LABELS[direction];
  const confidencePct = Math.round(confidence * 100);

  return (
    <div className="glass-card animate-fade-in-up" style={{ padding: "28px 32px", position: "relative", overflow: "hidden" }}>
      {/* 背景グロー */}
      <div style={{
        position: "absolute", top: "-80px", right: "-80px",
        width: "300px", height: "300px",
        background: "radial-gradient(circle, rgba(56,189,248,0.05) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", bottom: "-60px", left: "20%",
        width: "200px", height: "200px",
        background: "radial-gradient(circle, rgba(52,211,153,0.04) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      {/* ヘッダー */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "40px", height: "40px", borderRadius: "10px",
            background: "rgba(56,189,248,0.1)",
            border: "1px solid rgba(56,189,248,0.3)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "20px",
          }}>
            🤖
          </div>
          <div>
            <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "2px" }}>
              Gemini AI アナリストエンジン
            </p>
            <h3 style={{ fontSize: "1rem", fontWeight: 800, color: "var(--text-primary)" }}>
              {ticker} 総合分析レポート
            </h3>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <span className={dir.badgeClass || "badge-neutral"} style={{ fontSize: "0.78rem" }}>
            {dir.icon} {dir.label}
          </span>
          <span style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px", padding: "3px 10px",
            fontSize: "0.72rem", color: "var(--text-secondary)", fontWeight: 600,
          }}>
            信頼度 {confidencePct}%
          </span>
          <span style={{
            background: "rgba(255,255,255,0.05)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px", padding: "3px 10px",
            fontSize: "0.72rem",
            color: sentimentScore >= 0 ? "var(--accent-emerald)" : "var(--accent-red)",
            fontWeight: 700,
          }}>
            スコア {sentimentScore >= 0 ? "+" : ""}{sentimentScore.toFixed(3)}
          </span>
          {judgment && (() => {
            const jStyle =
              judgment === "BUY"
                ? { bg: "rgba(52,211,153,0.15)", border: "#34d399", color: "#34d399", cls: "neon-badge" }
                : judgment === "WATCH"
                ? { bg: "rgba(244,63,94,0.15)", border: "#f43f5e", color: "#f43f5e", cls: "neon-badge-red" }
                : { bg: "rgba(255,255,255,0.06)", border: "rgba(255,255,255,0.15)", color: "var(--text-secondary)", cls: "" };
            return (
              <span className={jStyle.cls} style={{
                fontSize: "0.78rem",
                background: jStyle.bg,
                borderColor: jStyle.border,
                color: jStyle.color,
                border: `1px solid ${jStyle.border}`,
                borderRadius: "6px",
                padding: "3px 10px",
                fontWeight: 700,
              }}>
                JUDGMENT: {judgment}
              </span>
            );
          })()}
        </div>
      </div>

      {/* セパレーター */}
      <div style={{
        height: "1px",
        background: "linear-gradient(90deg, transparent, rgba(56,189,248,0.3), rgba(52,211,153,0.2), transparent)",
        marginBottom: "20px",
      }} />

      {/* 分析テキスト */}
      <div style={{
        background: "rgba(0,0,0,0.2)",
        border: "1px solid rgba(255,255,255,0.05)",
        borderRadius: "12px", padding: "20px 24px",
        position: "relative", minHeight: "100px",
      }}>
        {/* ターミナル風ヘッダー */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "14px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f43f5e" }} />
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#fbbf24" }} />
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#34d399" }} />
          <span style={{
            marginLeft: "8px", fontSize: "0.68rem",
            color: "var(--text-muted)",
            fontFamily: "'Courier New', monospace",
            letterSpacing: "0.05em",
          }}>
            gemini-2.5-flash :: {ticker} :: 分析完了
          </span>
        </div>

        <p style={{ color: "var(--text-primary)", fontSize: "0.9rem", lineHeight: 1.85, fontFamily: "'Inter', 'Noto Sans JP', sans-serif" }}>
          {done ? highlightText(displayed) : displayed}
          {!done && (
            <span style={{
              display: "inline-block", width: "2px", height: "1em",
              background: "var(--accent-blue)", marginLeft: "2px",
              verticalAlign: "middle",
              animation: "typing-cursor 0.7s ease-in-out infinite",
            }} />
          )}
        </p>

        {done && analysis && (
          <div style={{ marginTop: "24px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div className="glass-card" style={{ padding: "16px", background: "rgba(255,255,255,0.02)" }}>
              <p style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: 800, marginBottom: "8px" }}>■ FUNDAMENTAL</p>
              <p style={{ fontSize: "0.82rem", lineHeight: 1.6, color: "var(--text-primary)" }}>{analysis.fundamental_reason}</p>
            </div>
            <div className="glass-card" style={{ padding: "16px", background: "rgba(255,255,255,0.02)" }}>
              <p style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: 800, marginBottom: "8px" }}>■ SOCIAL INSIGHT</p>
              <p style={{ fontSize: "0.82rem", lineHeight: 1.6, color: "var(--text-primary)" }}>{analysis.social_insight}</p>
            </div>
          </div>
        )}

        {done && analysis?.risk_factor && (
          <div style={{ marginTop: "12px" }}>
            <div className="glass-card" style={{ padding: "16px", background: "rgba(244,63,94,0.03)", borderColor: "rgba(244,63,94,0.15)" }}>
              <p style={{ fontSize: "0.75rem", color: "#f43f5e", fontWeight: 800, marginBottom: "8px" }}>■ RISK FACTOR</p>
              <p style={{ fontSize: "0.82rem", lineHeight: 1.6, color: "var(--text-primary)" }}>{analysis.risk_factor}</p>
            </div>
          </div>
        )}
      </div>

      {/* フッター */}
      <div style={{
        marginTop: "16px", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexWrap: "wrap", gap: "8px",
      }}>
        <div style={{ display: "flex", gap: "8px" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: "6px", height: "6px", background: "#34d399", borderRadius: "50%", display: "inline-block" }} className="animate-pulse-glow" />
            TDnet 適時開示データ
          </span>
          <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>•</span>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: "6px", height: "6px", background: "#38bdf8", borderRadius: "50%", display: "inline-block" }} className="animate-pulse-glow" />
            パブリックセンチメント解析
          </span>
          {scores && (
            <>
              <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>•</span>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                Gap: {scores.gap >= 0 ? "+" : ""}{scores.gap.toFixed(3)}
              </span>
            </>
          )}
        </div>
        <p style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>
          ※ 投資判断は自己責任でお願いします
        </p>
      </div>
    </div>
  );
}
