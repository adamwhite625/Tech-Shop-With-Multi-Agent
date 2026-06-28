import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Text2SQL — Natural Language Database Queries",
  description:
    "Query your CSV data using natural language. Powered by a fine-tuned Gemma 2 model running locally.",
  keywords: ["text2sql", "natural language", "sql", "csv", "ai", "llm"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
