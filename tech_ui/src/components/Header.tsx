"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, ShoppingCart, User, LogOut, Menu, Phone } from "lucide-react";
import { useStore } from "@/store/useStore"; // Import Zustand store

export default function Header() {
  const router = useRouter();
  const { user, cartCount, logout } = useStore();
  const [searchQuery, setSearchQuery] = useState("");

  // Xử lý hydration mismatch (Lỗi render giữa server và client trong Next.js)
  const [isMounted, setIsMounted] = useState(false);
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/products?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  if (!isMounted) return null; // Tránh lỗi giao diện nhấp nháy

  return (
    <header className="w-full relative z-50">
      {/* --- TOP BAR (Màu Đỏ Gradient giống Laravel cũ) --- */}
      <div className="header-gradient text-white py-3 shadow-md">
        <div className="container-custom flex flex-wrap md:flex-nowrap items-center justify-between gap-4">
          {/* 1. LOGO */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-primary font-bold text-xl">
              P
            </div>
            <span className="font-bold text-2xl tracking-tight hidden sm:block">
              PinkCapy
            </span>
          </Link>

          {/* 2. THANH TÌM KIẾM */}
          <form
            onSubmit={handleSearch}
            className="flex-1 w-full md:w-auto order-3 md:order-none max-w-2xl flex"
          >
            <input
              type="text"
              placeholder="Bạn đang tìm sản phẩm công nghệ gì..."
              className="w-full px-4 py-2.5 rounded-l-md text-text-main focus:outline-none"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              type="submit"
              className="bg-secondary hover:bg-yellow-400 text-text-main px-6 py-2.5 rounded-r-md font-medium transition-colors flex items-center justify-center"
            >
              <Search size={20} />
            </button>
          </form>

          {/* 3. NHÓM ACTION (Giỏ hàng, Tài khoản) */}
          <div className="flex items-center gap-6 shrink-0">
            {/* Hotline (Ẩn trên mobile) */}
            <div className="hidden lg:flex items-center gap-2">
              <Phone size={24} className="text-secondary" />
              <div className="flex flex-col">
                <span className="text-xs text-gray-200">Hotline 24/7</span>
                <span className="font-bold text-sm">1800.6969</span>
              </div>
            </div>

            {/* Giỏ hàng */}
            <Link
              href="/cart"
              className="flex items-center gap-2 relative group"
            >
              <div className="relative">
                <ShoppingCart size={28} />
                <span className="absolute -top-2 -right-2 bg-secondary text-text-main text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center border-2 border-primary">
                  {cartCount}
                </span>
              </div>
              <span className="hidden sm:block text-sm font-medium group-hover:text-secondary transition-colors">
                Giỏ hàng
              </span>
            </Link>

            {/* Tài khoản */}
            {user ? (
              <div className="group relative flex items-center gap-2 cursor-pointer">
                <div className="bg-white/20 p-1.5 rounded-full">
                  <User size={20} />
                </div>
                <div className="hidden sm:flex flex-col">
                  <span className="text-xs text-gray-200">Xin chào,</span>
                  <span className="font-bold text-sm truncate max-w-[100px]">
                    {user.first_name}
                  </span>
                </div>

                {/* Dropdown Menu */}
                <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-2 hidden group-hover:block border border-border">
                  <Link
                    href="/profile"
                    className="block px-4 py-2 text-text-main hover:bg-background hover:text-primary transition-colors text-sm"
                  >
                    Tài khoản của tôi
                  </Link>
                  <Link
                    href="/orders"
                    className="block px-4 py-2 text-text-main hover:bg-background hover:text-primary transition-colors text-sm"
                  >
                    Đơn mua
                  </Link>
                  <hr className="my-1 border-border" />
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-danger hover:bg-background transition-colors text-sm flex items-center gap-2"
                  >
                    <LogOut size={16} /> Đăng xuất
                  </button>
                </div>
              </div>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-2 hover:text-secondary transition-colors"
              >
                <User size={24} />
                <div className="hidden sm:flex flex-col">
                  <span className="text-xs text-gray-200">Đăng nhập</span>
                  <span className="font-bold text-sm">Tài khoản</span>
                </div>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* --- BOTTOM BAR (Danh mục - Dùng nền trắng giống IS207) --- */}
      <div className="bg-white border-b border-border hidden md:block shadow-sm">
        <div className="container-custom flex items-center">
          <div className="flex items-center gap-2 bg-primary text-white px-4 py-3 font-bold cursor-pointer hover:bg-primary-hover transition-colors">
            <Menu size={20} />
            <span>DANH MỤC SẢN PHẨM</span>
          </div>

          <nav className="flex items-center gap-6 ml-8 font-medium text-text-main text-sm">
            <Link href="/" className="hover:text-primary transition-colors">
              Trang chủ
            </Link>
            <Link
              href="/products?category=camera"
              className="hover:text-primary transition-colors"
            >
              Camera
            </Link>
            <Link
              href="/products?category=smartwatch"
              className="hover:text-primary transition-colors"
            >
              Đồng hồ thông minh
            </Link>
            <Link
              href="/products?category=accessories"
              className="hover:text-primary transition-colors"
            >
              Phụ kiện
            </Link>
            <Link
              href="/about"
              className="hover:text-primary transition-colors"
            >
              Giới thiệu
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
