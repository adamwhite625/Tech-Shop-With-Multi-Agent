"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Mail,
  Shield,
  Save,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

export default function ProfilePage() {
  const router = useRouter();
  const { user, setUser } = useStore();

  // State cho form cập nhật thông tin
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
  });
  const [updatingInfo, setUpdatingInfo] = useState(false);
  const [infoMessage, setInfoMessage] = useState({ type: "", text: "" });

  // State cho form đổi mật khẩu
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [updatingPassword, setUpdatingPassword] = useState(false);
  const [passMessage, setPassMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    if (!sessionStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    fetchProfile();
  }, [router]);

  const fetchProfile = async () => {
    try {
      const res = await webClient.get("/auth/me");
      setUser(res.data);
      setFormData({
        first_name: res.data.first_name || "",
        last_name: res.data.last_name || "",
        email: res.data.email || "",
      });
    } catch (error) {
      console.error("Lỗi tải thông tin:", error);
    }
  };

  const handleUpdateInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdatingInfo(true);
    setInfoMessage({ type: "", text: "" });

    try {
      const res = await webClient.put("/auth/me", {
        first_name: formData.first_name,
        last_name: formData.last_name,
      });
      setUser(res.data);
      setInfoMessage({
        type: "success",
        text: "Cập nhật thông tin thành công!",
      });
    } catch (error: any) {
      setInfoMessage({
        type: "error",
        text: error.response?.data?.detail || "Cập nhật thất bại.",
      });
    } finally {
      setUpdatingInfo(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassMessage({ type: "", text: "" });

    if (passwords.new_password !== passwords.confirm_password) {
      setPassMessage({ type: "error", text: "Mật khẩu xác nhận không khớp!" });
      return;
    }

    setUpdatingPassword(true);
    try {
      await webClient.put("/auth/password", {
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      });
      setPassMessage({ type: "success", text: "Đổi mật khẩu thành công!" });
      setPasswords({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error: any) {
      setPassMessage({
        type: "error",
        text: error.response?.data?.detail || "Đổi mật khẩu thất bại.",
      });
    } finally {
      setUpdatingPassword(false);
    }
  };

  if (!user)
    return <div className="text-center py-20">Đang tải thông tin...</div>;

  return (
    <div className="container-custom py-10">
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-text-muted hover:text-primary font-medium transition-colors"
        >
          <ArrowLeft size={20} /> Quay lại trang chủ
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-primary mb-8 flex items-center gap-3">
        <User size={32} /> Quản Lý Tài Khoản
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* CỘT 1: THÔNG TIN CÁ NHÂN */}
        <div className="bg-white rounded-lg shadow-sm border border-border p-6 sm:p-8 h-fit">
          <h2 className="text-xl font-bold text-text-main mb-6 flex items-center gap-2 border-b border-border pb-4">
            <User className="text-primary" /> Thông tin cá nhân
          </h2>

          {infoMessage.text && (
            <div
              className={`p-3 rounded-md mb-6 text-sm flex items-center gap-2 ${infoMessage.type === "success" ? "bg-green-50 text-success border border-green-200" : "bg-red-50 text-danger border border-red-200"}`}
            >
              {infoMessage.type === "success" && <CheckCircle2 size={18} />}
              {infoMessage.text}
            </div>
          )}

          <form onSubmit={handleUpdateInfo} className="space-y-5">
            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-text-main mb-1">
                  Họ
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) =>
                    setFormData({ ...formData, last_name: e.target.value })
                  }
                  className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-main mb-1">
                  Tên
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) =>
                    setFormData({ ...formData, first_name: e.target.value })
                  }
                  className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Email (Không thể thay đổi)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail size={18} className="text-gray-400" />
                </div>
                <input
                  type="email"
                  value={formData.email}
                  disabled
                  className="w-full pl-10 px-4 py-2.5 border border-border rounded-md bg-gray-100 text-gray-500 cursor-not-allowed"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={updatingInfo}
              className="mt-4 bg-primary hover:bg-primary-hover text-white font-bold py-2.5 px-6 rounded-md transition-colors flex items-center gap-2 disabled:bg-gray-400"
            >
              <Save size={18} /> {updatingInfo ? "Đang lưu..." : "Lưu Thay Đổi"}
            </button>
          </form>
        </div>

        {/* CỘT 2: ĐỔI MẬT KHẨU */}
        <div className="bg-white rounded-lg shadow-sm border border-border p-6 sm:p-8 h-fit">
          <h2 className="text-xl font-bold text-text-main mb-6 flex items-center gap-2 border-b border-border pb-4">
            <Shield className="text-primary" /> Đổi mật khẩu
          </h2>

          {passMessage.text && (
            <div
              className={`p-3 rounded-md mb-6 text-sm flex items-center gap-2 ${passMessage.type === "success" ? "bg-green-50 text-success border border-green-200" : "bg-red-50 text-danger border border-red-200"}`}
            >
              {passMessage.type === "success" && <CheckCircle2 size={18} />}
              {passMessage.text}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Mật khẩu hiện tại
              </label>
              <input
                type="password"
                value={passwords.current_password}
                onChange={(e) =>
                  setPasswords({
                    ...passwords,
                    current_password: e.target.value,
                  })
                }
                className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Mật khẩu mới
              </label>
              <input
                type="password"
                value={passwords.new_password}
                onChange={(e) =>
                  setPasswords({ ...passwords, new_password: e.target.value })
                }
                className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                required
                minLength={6}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-main mb-1">
                Xác nhận mật khẩu mới
              </label>
              <input
                type="password"
                value={passwords.confirm_password}
                onChange={(e) =>
                  setPasswords({
                    ...passwords,
                    confirm_password: e.target.value,
                  })
                }
                className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                required
                minLength={6}
              />
            </div>

            <button
              type="submit"
              disabled={updatingPassword}
              className="mt-4 bg-text-main hover:bg-black text-white font-bold py-2.5 px-6 rounded-md transition-colors flex items-center gap-2 disabled:bg-gray-400"
            >
              <Shield size={18} />{" "}
              {updatingPassword ? "Đang xử lý..." : "Cập Nhật Mật Khẩu"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
