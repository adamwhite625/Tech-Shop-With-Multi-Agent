"use client";

import { useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  X,
  Send,
  Bot,
  User,
  Loader2,
  Upload,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { aiClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  imageUrl?: string;
};

export default function Chatbot() {
  const { user } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "ai",
      content:
        "Xin chào! Tôi là Trợ lý AI của Tech Store. Tôi có thể giúp bạn tìm kiếm sản phẩm, tư vấn cấu hình, hoặc tra cứu/hủy đơn hàng. Bạn cần giúp gì nào?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tạo Session ID độc nhất cho mỗi người dùng/phiên chat
  const [sessionId] = useState(
    () => `session_${Math.random().toString(36).substring(2, 9)}`,
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Tự động cuộn xuống tin nhắn mới nhất
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");

    // Thêm tin nhắn của User vào giao diện
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: userMsg },
    ]);
    setIsLoading(true);

    try {
      // Gọi lên Host Agent (Cổng 8000)
      const res = await aiClient.post("/orchestrate", {
        message: userMsg,
        session_id: user ? `user_${user.user_id}` : sessionId, // Nếu có user thì dùng ID user để AI nhớ
      });

      // Bóc tách kết quả từ Multi-Agent
      let aiResponseContent = "";
      const agentType = res.data.agent;
      const responseData = res.data.data;

      if (agentType === "search") {
        // Xử lý nếu trả về từ Search Agent
        aiResponseContent = `Tôi tìm thấy ${responseData.total_found} sản phẩm phù hợp:\n`;
        responseData.results.forEach((item: any) => {
          aiResponseContent += `- **${item.title}** (Giá: ${item.price?.toLocaleString()}đ)\n`;
        });
        if (responseData.total_found === 0)
          aiResponseContent =
            "Xin lỗi, tôi không tìm thấy sản phẩm nào phù hợp.";
      } else {
        // Xử lý nếu trả về từ Advisor hoặc Order Agent
        aiResponseContent = responseData.content;
      }

      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "ai", content: aiResponseContent },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "ai",
          content:
            "Xin lỗi, hệ thống AI đang quá tải hoặc mất kết nối. Vui lòng thử lại sau.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Thêm preview hình ảnh vào chat
    const imageUrl = URL.createObjectURL(file);
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content: "Đã gửi hình ảnh",
        imageUrl: imageUrl, // Lưu URL ảnh
      },
    ]);

    setIsLoading(true);

    try {
      // Gửi ảnh tới Search Agent
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8001/api/search/image", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();

      // Xử lý kết quả tìm kiếm ảnh
      let aiResponseContent = "Dựa trên hình ảnh bạn gửi, tôi tìm thấy:\n";
      if (data.results && data.results.length > 0) {
        data.results.forEach((item: any) => {
          const matchScore = item.match_score || item.score || 0;
          aiResponseContent += `- **${item.title}** - Độ tương đồng: ${(matchScore * 100).toFixed(1)}%\n`;
        });
      } else {
        aiResponseContent =
          "Xin lỗi, tôi không tìm thấy sản phẩm nào tương tự với hình ảnh này.";
      }

      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "ai", content: aiResponseContent },
      ]);
    } catch (error) {
      console.error("Image search error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "ai",
          content:
            "Xin lỗi, có lỗi khi xử lý hình ảnh. Vui lòng thử lại sau.\n\nGợi ý: Kiểm tra xem Search Agent có chạy ở port 8001 không.",
        },
      ]);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <>
      {/* Nút bấm mở Chat lơ lửng */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 bg-primary text-white rounded-full shadow-lg hover:bg-primary-hover hover:scale-110 transition-all z-50 ${isOpen ? "hidden" : "flex"}`}
      >
        <MessageSquare size={28} />
      </button>

      {/* Khung Chat */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[350px] sm:w-[400px] h-[550px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden border border-border">
          {/* Header của Chatbot */}
          <div className="bg-primary text-white p-4 flex justify-between items-center shadow-md">
            <div className="flex items-center gap-2">
              <Bot size={24} />
              <div>
                <h3 className="font-bold">Trợ lý AI</h3>
                <p className="text-xs text-red-100">Đang hoạt động</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-primary-hover p-1 rounded-md transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Vùng hiển thị tin nhắn */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-4 text-sm">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "ai" && (
                  <div className="w-8 h-8 rounded-full bg-primary flex flex-shrink-0 items-center justify-center text-white">
                    <Bot size={16} />
                  </div>
                )}

                <div
                  className={`p-3 rounded-2xl max-w-[80%] ${msg.role === "user" ? "bg-blue-btn text-white rounded-tr-none" : "bg-white text-text-main border border-border rounded-tl-none shadow-sm prose prose-sm prose-p:leading-relaxed prose-pre:bg-gray-100"}`}
                >
                  {msg.imageUrl ? (
                    // Hiển thị hình ảnh nếu có imageUrl
                    <div className="flex flex-col gap-2">
                      <img
                        src={msg.imageUrl}
                        alt="Uploaded"
                        className="max-w-full h-auto rounded-lg max-h-64 object-cover"
                      />
                      {msg.content && <p className="text-sm">{msg.content}</p>}
                    </div>
                  ) : (
                    // Hiển thị text markdown nếu không có ảnh
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-2 justify-start items-center text-text-muted">
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  <Bot size={16} />
                </div>
                <div className="bg-white p-3 rounded-2xl rounded-tl-none border border-border shadow-sm flex items-center gap-2">
                  <Loader2 className="animate-spin" size={16} /> AI đang suy
                  nghĩ...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Khung nhập liệu */}
          <form
            onSubmit={handleSendMessage}
            className="p-3 bg-white border-t border-border flex items-center gap-2"
          >
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />

            {/* Image upload button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="p-2.5 bg-gray-100 text-text-muted hover:bg-gray-200 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-full transition-colors"
              title="Upload hình ảnh"
            >
              <Upload size={18} />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập tin nhắn..."
              className="flex-1 py-2 px-4 bg-gray-100 border-transparent rounded-full focus:outline-none focus:ring-2 focus:ring-primary/50 text-text-main"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-2.5 bg-primary text-white rounded-full hover:bg-primary-hover disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
