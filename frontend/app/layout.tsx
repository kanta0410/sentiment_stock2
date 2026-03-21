import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent S",
  description:
    "Gemini AIとニュース・SNS分析で日本株・米国株の株価方向性を予測するダッシュボード。TDnet・Redditのデータをリアルタイムに分析します。",
  keywords: ["株価予測", "センチメント分析", "AI", "Gemini", "投資", "日本株"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+JP:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
