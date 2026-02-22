"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 1. Gửi request Login tới FastAPI (/auth/login endpoint expects JSON)
      const loginRes = await webClient.post("/auth/login", {
        email: email,
        password: password,
      });

      // 2. Lưu Token vào Session Storage
      const token = loginRes.data.access_token;
      sessionStorage.setItem("token", token);

      // 3. Lưu User vào Zustand Store (từ response của login)
      setUser({
        user_id: loginRes.data.user.user_id,
        email: loginRes.data.user.email,
        first_name: loginRes.data.user.first_name,
        last_name: loginRes.data.user.last_name,
        is_admin: loginRes.data.user.is_admin,
      });

      // 4. Chuyển hướng về trang chủ
      router.push("/");
    } catch (err: any) {
      console.error("Chi tiết lỗi từ Backend:", err.response?.data);

      // Handle both string and object error details
      let errorMessage = "Đăng nhập thất bại. Kiểm tra lại thông tin.";
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === "string") {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          // Handle validation errors (array of objects)
          errorMessage = err.response.data.detail
            .map((e: any) => e.msg || JSON.stringify(e))
            .join(", ");
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md border border-border">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-primary">Đăng Nhập</h2>
          <p className="text-text-muted mt-2">
            Đăng nhập để mua sắm và quản lý đơn hàng
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-danger p-3 rounded-md text-sm mb-4 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Email đăng nhập
            </label>
            <input
              type="email"
              required
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@techshop.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Mật khẩu
            </label>
            <input
              type="password"
              required
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-hover text-white font-bold py-2.5 px-4 rounded-md transition-colors flex justify-center items-center"
          >
            {loading ? "Đang xử lý..." : "ĐĂNG NHẬP"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-text-muted">
          Chưa có tài khoản?{" "}
          <Link
            href="/register"
            className="text-blue-btn hover:underline font-medium"
          >
            Đăng ký ngay
          </Link>
        </div>
      </div>
    </div>
  );
}
