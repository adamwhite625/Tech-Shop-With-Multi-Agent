"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserPlus, ArrowLeft } from "lucide-react";
import { webClient } from "@/lib/axios";

export default function RegisterPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirm_password) {
      setError("Mật khẩu xác nhận không khớp!");
      return;
    }

    setLoading(true);
    try {
      // Gọi API đăng ký tài khoản (Đảm bảo Backend của bạn có API POST /auth/register)
      await webClient.post("/auth/register", {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        password: formData.password,
      });

      alert("Đăng ký thành công! Vui lòng đăng nhập.");
      router.push("/login");
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Đăng ký thất bại. Email này có thể đã được sử dụng.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg border border-border">
        <div className="mb-6">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-text-muted hover:text-primary font-medium transition-colors text-sm"
          >
            <ArrowLeft size={16} /> Quay lại đăng nhập
          </Link>
        </div>

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-4">
            <UserPlus size={32} />
          </div>
          <h2 className="text-3xl font-bold text-text-main">Tạo Tài Khoản</h2>
          <p className="text-text-muted mt-2">
            Gia nhập cộng đồng PinkCapy Tech
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-danger p-3 rounded-md text-sm mb-6 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Họ
              </label>
              <input
                type="text"
                name="last_name"
                required
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                placeholder="Nguyễn Văn"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Tên
              </label>
              <input
                type="text"
                name="first_name"
                required
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                placeholder="A"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Mật khẩu
            </label>
            <input
              type="password"
              name="password"
              required
              minLength={6}
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Xác nhận mật khẩu
            </label>
            <input
              type="password"
              name="confirm_password"
              required
              minLength={6}
              value={formData.confirm_password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-hover text-white font-bold py-3 px-4 rounded-md transition-colors flex justify-center items-center mt-2"
          >
            {loading ? "ĐANG XỬ LÝ..." : "ĐĂNG KÝ NGAY"}
          </button>
        </form>
      </div>
    </div>
  );
}
