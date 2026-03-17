"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserPlus, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";
import { webClient } from "@/lib/axios";

// Password strength checker
const checkPasswordStrength = (password: string) => {
  let strength = 0;
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
  };

  // Calculate strength score
  Object.values(checks).forEach((check) => {
    if (check) strength++;
  });

  let level = "Yếu";
  let color = "text-red-500";
  if (strength >= 4) {
    level = "Mạnh";
    color = "text-green-500";
  } else if (strength >= 3) {
    level = "Trung bình";
    color = "text-yellow-500";
  }

  return { checks, strength, level, color };
};

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
  const passwordStrength = checkPasswordStrength(formData.password);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const isPasswordValid = () => {
    const { length, uppercase, number } = passwordStrength.checks;
    return length && uppercase && number && formData.password.length >= 8;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate required fields
    if (!formData.first_name || !formData.last_name) {
      setError("Vui lòng nhập họ và tên!");
      return;
    }

    if (!formData.email) {
      setError("Vui lòng nhập email!");
      return;
    }

    // Validate password strength
    if (!isPasswordValid()) {
      setError("Mật khẩu phải có ít nhất 8 ký tự, chứa chữ hoa và số!");
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError("Mật khẩu xác nhận không khớp!");
      return;
    }

    setLoading(true);
    try {
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

  // Check if form is valid
  const isFormValid =
    formData.first_name &&
    formData.last_name &&
    formData.email &&
    isPasswordValid() &&
    formData.password === formData.confirm_password;

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
              minLength={8}
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
              placeholder="••••••••"
            />

            {/* Password strength indicator */}
            {formData.password && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-text-muted">
                    Độ mạnh mật khẩu
                  </span>
                  <span
                    className={`text-xs font-bold ${passwordStrength.color}`}
                  >
                    {passwordStrength.level}
                  </span>
                </div>

                {/* Strength bar */}
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      passwordStrength.strength <= 2
                        ? "bg-red-500 w-1/3"
                        : passwordStrength.strength <= 3
                          ? "bg-yellow-500 w-2/3"
                          : "bg-green-500 w-full"
                    }`}
                  />
                </div>

                {/* Requirements checklist */}
                <div className="space-y-1 text-xs">
                  <div
                    className={`flex items-center gap-2 ${
                      passwordStrength.checks.length
                        ? "text-green-600"
                        : "text-gray-400"
                    }`}
                  >
                    {passwordStrength.checks.length ? (
                      <CheckCircle size={14} />
                    ) : (
                      <AlertCircle size={14} />
                    )}
                    <span>Ít nhất 8 ký tự</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      passwordStrength.checks.uppercase
                        ? "text-green-600"
                        : "text-gray-400"
                    }`}
                  >
                    {passwordStrength.checks.uppercase ? (
                      <CheckCircle size={14} />
                    ) : (
                      <AlertCircle size={14} />
                    )}
                    <span>Chứa chữ hoa (A-Z)</span>
                  </div>
                  <div
                    className={`flex items-center gap-2 ${
                      passwordStrength.checks.number
                        ? "text-green-600"
                        : "text-gray-400"
                    }`}
                  >
                    {passwordStrength.checks.number ? (
                      <CheckCircle size={14} />
                    ) : (
                      <AlertCircle size={14} />
                    )}
                    <span>Chứa số (0-9)</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-text-main mb-1">
              Xác nhận mật khẩu
            </label>
            <input
              type="password"
              name="confirm_password"
              required
              minLength={8}
              value={formData.confirm_password}
              onChange={handleChange}
              className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-primary/50 outline-none ${
                formData.confirm_password &&
                formData.password === formData.confirm_password
                  ? "border-green-500 bg-green-50"
                  : formData.confirm_password &&
                      formData.password !== formData.confirm_password
                    ? "border-red-500 bg-red-50"
                    : "border-border"
              }`}
              placeholder="••••••••"
            />
            {formData.confirm_password && (
              <div
                className={`mt-1 text-xs font-medium ${
                  formData.password === formData.confirm_password
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {formData.password === formData.confirm_password
                  ? "✓ Mật khẩu khớp"
                  : "✗ Mật khẩu không khớp"}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !isFormValid}
            className="w-full bg-primary hover:bg-primary-hover disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-md transition-colors flex justify-center items-center mt-2"
          >
            {loading ? "ĐANG XỬ LÝ..." : "ĐĂNG KÝ NGAY"}
          </button>
        </form>
      </div>
    </div>
  );
}
