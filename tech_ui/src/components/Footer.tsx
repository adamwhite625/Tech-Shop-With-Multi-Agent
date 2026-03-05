import Link from "next/link";
import { Mail, Phone, MapPin } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-[#1e293b] text-gray-300 pt-12 pb-8 mt-auto">
      <div className="container-custom grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8 border-b border-gray-700 pb-8">
        {/* Cột 1: Thông tin công ty */}
        <div>
          <h3 className="text-white text-xl font-bold mb-4 flex items-center gap-2">
            <span className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm">
              P
            </span>
            PinkCapy Tech
          </h3>
          <p className="text-sm mb-4 leading-relaxed">
            Hệ thống cửa hàng phân phối sản phẩm công nghệ chính hãng, tích hợp
            Trợ lý AI tư vấn chuyên sâu 24/7.
          </p>
          <div className="space-y-2 text-sm">
            <p className="flex items-center gap-2">
              <MapPin size={16} className="text-primary" /> 123 Đường Công Nghệ,
              Quận 1, TP.HCM
            </p>
            <p className="flex items-center gap-2">
              <Phone size={16} className="text-primary" /> 1800.6969 (Miễn phí)
            </p>
            <p className="flex items-center gap-2">
              <Mail size={16} className="text-primary" /> support@techstore.com
            </p>
          </div>
        </div>

        {/* Cột 2: Hỗ trợ khách hàng */}
        <div>
          <h4 className="text-white font-bold mb-4">Hỗ trợ khách hàng</h4>
          <ul className="space-y-2 text-sm">
            <li>
              <Link href="#" className="hover:text-primary transition-colors">
                Hướng dẫn mua hàng
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors">
                Chính sách bảo hành
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors">
                Chính sách đổi trả
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors">
                Giao hàng & Thanh toán
              </Link>
            </li>
          </ul>
        </div>

        {/* Cột 3: Danh mục nổi bật */}
        <div>
          <h4 className="text-white font-bold mb-4">Danh mục nổi bật</h4>
          <ul className="space-y-2 text-sm">
            <li>
              <Link
                href="/products?category=camera"
                className="hover:text-primary transition-colors"
              >
                Camera An Ninh
              </Link>
            </li>
            <li>
              <Link
                href="/products?category=smartwatch"
                className="hover:text-primary transition-colors"
              >
                Đồng hồ thông minh
              </Link>
            </li>
            <li>
              <Link
                href="/products?category=accessories"
                className="hover:text-primary transition-colors"
              >
                Phụ kiện công nghệ
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors">
                Thiết bị mạng
              </Link>
            </li>
          </ul>
        </div>

        {/* Cột 4: Đăng ký nhận tin */}
        <div>
          <h4 className="text-white font-bold mb-4">Đăng ký nhận khuyến mãi</h4>
          <p className="text-sm mb-4">
            Nhận ngay mã giảm giá 10% cho đơn hàng đầu tiên của bạn.
          </p>
          <form className="flex">
            <input
              type="email"
              placeholder="Nhập email của bạn..."
              className="w-full px-4 py-2 rounded-l-md text-gray-900 focus:outline-none"
            />
            <button
              type="button"
              className="bg-primary hover:bg-primary-hover px-4 py-2 rounded-r-md text-white font-medium transition-colors"
            >
              Gửi
            </button>
          </form>
        </div>
      </div>

      <div className="container-custom text-center text-sm text-gray-500">
        <p>
          &copy; {new Date().getFullYear()} Tech Store. Bảo lưu mọi quyền. Đồ án
          xây dựng bởi bạn.
        </p>
      </div>
    </footer>
  );
}
