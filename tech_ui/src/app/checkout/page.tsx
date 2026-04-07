"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, ArrowLeft, CreditCard, Truck } from "lucide-react";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

// Định nghĩa kiểu dữ liệu Giỏ hàng để hiển thị tóm tắt
interface CartItem {
  cart_item_id: number;
  quantity: number;
  price: number;
  product?: { title: string };
}

export default function CheckoutPage() {
  const router = useRouter();
  const { user, setCartCount } = useStore();
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // State lưu thông tin form
  const [formData, setFormData] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    phone: "",
    email: user?.email || "",
    line1: "",
    city: "",
    province: "",
    note: "",
  });

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    fetchCartSummary();
  }, [router, user]);

  const fetchCartSummary = async () => {
    try {
      const res = await webClient.get("/cart/");
      const items = res.data?.items || [];
      if (items.length === 0) {
        alert("Giỏ hàng của bạn đang trống!");
        router.push("/cart");
        return;
      }
      setCartItems(items);
    } catch (error) {
      console.error("Lỗi khi tải giỏ hàng:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Gọi API Đặt hàng (Có dấu / ở cuối theo cấu trúc Backend của bạn)
      const res = await webClient.post("/checkout/", {
        ...formData,
        payment_method: 1, // 1 là COD (Thanh toán khi nhận hàng)
      });

      // Nếu thành công:
      alert(
        "🎉 Đặt hàng thành công! Mã đơn hàng của bạn là: #" + res.data.order_id,
      );

      // Xóa số lượng giỏ hàng trên Header
      setCartCount(0);

      // Chuyển hướng về trang chủ (hoặc sau này bạn có thể làm trang /orders)
      router.push("/");
    } catch (error: any) {
      console.error("Lỗi đặt hàng:", error);
      alert(
        error.response?.data?.detail ||
          "Có lỗi xảy ra khi đặt hàng. Vui lòng kiểm tra lại.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const subtotal = cartItems.reduce(
    (acc, item) => acc + Number(item.price) * item.quantity,
    0,
  );
  const shippingFee = 30000;
  const grandTotal = subtotal + shippingFee;

  if (loading)
    return <div className="text-center py-20">Đang tải thông tin...</div>;

  return (
    <div className="container-custom py-10">
      <div className="mb-6">
        <Link
          href="/cart"
          className="inline-flex items-center gap-2 text-text-muted hover:text-primary font-medium transition-colors"
        >
          <ArrowLeft size={20} /> Quay lại giỏ hàng
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-primary mb-8 flex items-center gap-3">
        <CreditCard size={32} /> Thanh Toán Đơn Hàng
      </h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Cột Form điền thông tin */}
        <div className="lg:w-2/3">
          <div className="bg-white rounded-lg shadow-sm border border-border p-6 sm:p-8">
            <h2 className="text-xl font-bold text-text-main mb-6 flex items-center gap-2 border-b border-border pb-4">
              <Truck className="text-primary" /> Thông tin giao hàng
            </h2>

            <form
              id="checkout-form"
              onSubmit={handleCheckout}
              className="space-y-5"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Họ
                  </label>
                  <input
                    required
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="Nguyễn Văn"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Tên
                  </label>
                  <input
                    required
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="A"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Số điện thoại
                  </label>
                  <input
                    required
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="0901234567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Email
                  </label>
                  <input
                    required
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="email@example.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-main mb-1">
                  Địa chỉ cụ thể (Số nhà, đường)
                </label>
                <input
                  required
                  type="text"
                  name="line1"
                  value={formData.line1}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                  placeholder="123 Đường ABC..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Quận / Huyện
                  </label>
                  <input
                    required
                    type="text"
                    name="province"
                    value={formData.province}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="Quận 1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1">
                    Tỉnh / Thành phố
                  </label>
                  <input
                    required
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                    placeholder="TP. Hồ Chí Minh"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-main mb-1">
                  Ghi chú đơn hàng (Tùy chọn)
                </label>
                <textarea
                  name="note"
                  value={formData.note}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-2.5 border border-border rounded-md focus:ring-2 focus:ring-primary/50 outline-none"
                  placeholder="Giao giờ hành chính..."
                ></textarea>
              </div>
            </form>
          </div>
        </div>

        {/* Cột Tóm tắt Đơn hàng & Nút Submit */}
        <div className="lg:w-1/3">
          <div className="bg-white rounded-lg shadow-sm border border-border p-6 sticky top-6">
            <h2 className="text-xl font-bold text-text-main mb-6 border-b border-border pb-4">
              Đơn hàng của bạn
            </h2>

            <div className="space-y-4 mb-6 max-h-[300px] overflow-y-auto pr-2">
              {cartItems.map((item) => (
                <div
                  key={item.cart_item_id}
                  className="flex justify-between text-sm"
                >
                  <span className="text-text-muted line-clamp-1 pr-4">
                    {item.quantity} x {item.product?.title || "Sản phẩm"}
                  </span>
                  <span className="font-medium whitespace-nowrap">
                    {(Number(item.price) * item.quantity).toLocaleString(
                      "vi-VN",
                    )}{" "}
                    đ
                  </span>
                </div>
              ))}
            </div>

            <div className="space-y-4 text-text-main mb-6 border-t border-border pt-4">
              <div className="flex justify-between">
                <span>Tạm tính:</span>
                <span className="font-medium">
                  {subtotal.toLocaleString("vi-VN")} đ
                </span>
              </div>
              <div className="flex justify-between">
                <span>Phí giao hàng:</span>
                <span className="font-medium">
                  {shippingFee.toLocaleString("vi-VN")} đ
                </span>
              </div>
              <div className="flex justify-between text-success font-medium">
                <span>Phương thức:</span>
                <span>Thanh toán khi nhận hàng (COD)</span>
              </div>
              <div className="border-t border-border pt-4 flex justify-between items-center">
                <span className="font-bold text-lg">Tổng cộng:</span>
                <span className="text-2xl font-bold text-primary">
                  {grandTotal.toLocaleString("vi-VN")} đ
                </span>
              </div>
            </div>

            <button
              type="submit"
              form="checkout-form"
              disabled={submitting}
              className="w-full bg-primary hover:bg-primary-hover text-white font-bold py-3.5 px-4 rounded-md transition-colors text-center flex justify-center items-center gap-2 disabled:bg-gray-400"
            >
              {submitting ? (
                "ĐANG XỬ LÝ..."
              ) : (
                <>
                  <CheckCircle2 size={20} /> ĐẶT HÀNG NGAY
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
