import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tech Shop Admin — Text2SQL Dashboard",
  description:
    "Admin dashboard for PinkCapy Tech Store. Query the database using natural language, powered by a fine-tuned Gemma 2 model.",
  keywords: ["text2sql", "admin", "tech shop", "natural language", "sql", "ai"],
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
