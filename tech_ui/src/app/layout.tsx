import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Chatbot from "@/components/Chatbot";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "PinkCapy Tech Store",
  description: "Cửa hàng công nghệ đa tác vụ AI Multi-Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="antialiased flex flex-col min-h-screen">
        {/* Thanh Header luôn ở trên cùng */}
        <Header />

        {/* Nội dung thay đổi của từng trang sẽ nằm ở đây */}
        <main className="flex-grow bg-background">{children}</main>

        <Footer />
        <Chatbot />
      </body>
    </html>
  );
}
