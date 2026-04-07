"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, ArrowLeft, ShoppingBag } from "lucide-react";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

// Định nghĩa kiểu dữ liệu cho Giỏ hàng
interface CartItem {
  cart_item_id: number;
  product_id: number;
  quantity: number;
  price: number;
  product?: {
    title: string;
    thumb: string;
    slug: string;
  };
}

const buildImageUrl = (thumb?: string) => {
  if (!thumb) return "";

  if (thumb.startsWith("http")) return thumb;

  const baseOrigin = "https://cellphones.com.vn/media/catalog/product";
  const cdnPrefix =
    "https://cdn2.cellphones.com.vn/insecure/rs:fill:300:300/q:90/plain/";

  return cdnPrefix + baseOrigin + thumb;
};

export default function CartPage() {
  const router = useRouter();
  const { user, setCartCount } = useStore();
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Nếu chưa đăng nhập, đá về trang login
    if (!localStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    fetchCart();
  }, [router]);

  const fetchCart = async () => {
    try {
      const res = await webClient.get("/cart/");
      const items = res.data?.items || [];
      setCartItems(items);
      setCartCount(items.length);
    } catch (error) {
      console.error("Lỗi khi tải giỏ hàng:", error);
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (cart_item_id: number) => {
    if (!confirm("Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?")) return;
    try {
      await webClient.delete(`/cart/items/${cart_item_id}`);
      fetchCart(); // Tải lại giỏ hàng sau khi xóa
    } catch (error) {
      console.error("Lỗi khi xóa sản phẩm:", error);
      alert("Không thể xóa sản phẩm lúc này.");
    }
  };

  // Tính tổng tiền
  const subtotal = cartItems.reduce(
    (acc, item) => acc + Number(item.price) * item.quantity,
    0,
  );

  if (loading) {
    return (
      <div className="text-center py-20 text-text-muted">
        Đang tải giỏ hàng...
      </div>
    );
  }

  return (
    <div className="container-custom py-10">
      <h1 className="text-3xl font-bold text-primary mb-8 flex items-center gap-3">
        <ShoppingBag size={32} /> Giỏ Hàng Của Bạn
      </h1>

      {cartItems.length === 0 ? (
        <div className="bg-white p-10 rounded-lg shadow-sm border border-border text-center">
          <p className="text-text-muted text-lg mb-6">
            Giỏ hàng của bạn đang trống.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white font-bold py-3 px-6 rounded-md transition-colors"
          >
            <ArrowLeft size={20} /> Tiếp tục mua sắm
          </Link>
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Cột danh sách sản phẩm */}
          <div className="lg:w-2/3 bg-white rounded-lg shadow-sm border border-border overflow-hidden">
            <div className="p-6">
              <div className="hidden md:grid grid-cols-12 gap-4 text-sm font-bold text-text-muted border-b border-border pb-4 mb-4">
                <div className="col-span-6">Sản phẩm</div>
                <div className="col-span-2 text-center">Đơn giá</div>
                <div className="col-span-2 text-center">Số lượng</div>
                <div className="col-span-2 text-right">Thao tác</div>
              </div>

              <div className="space-y-6">
                {cartItems.map((item) => (
                  <div
                    key={item.cart_item_id}
                    className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center border-b border-border pb-6 last:border-0 last:pb-0"
                  >
                    <div className="col-span-1 md:col-span-6 flex items-center gap-4">
                      <div className="w-20 h-20 shrink-0 border border-border rounded-md overflow-hidden bg-gray-50 flex items-center justify-center p-4">
                        {item.product?.thumb ? (
                          <img
                            src={buildImageUrl(item.product.thumb)}
                            alt={item.product.title}
                            className="max-w-full max-h-full object-contain"
                          />
                        ) : (
                          <ShoppingBag className="text-gray-300" size={24} />
                        )}
                      </div>
                      <div>
                        <h3 className="font-bold text-text-main line-clamp-2">
                          {item.product?.title ||
                            `Sản phẩm ID: ${item.product_id}`}
                        </h3>
                      </div>
                    </div>

                    <div className="col-span-1 md:col-span-2 text-primary font-bold md:text-center">
                      {Number(item.price).toLocaleString("vi-VN")} đ
                    </div>

                    <div className="col-span-1 md:col-span-2 flex justify-start md:justify-center items-center">
                      <span className="bg-gray-100 px-4 py-1.5 rounded-md font-medium text-text-main border border-border">
                        {item.quantity}
                      </span>
                    </div>

                    <div className="col-span-1 md:col-span-2 text-right">
                      <button
                        onClick={() => removeItem(item.cart_item_id)}
                        className="text-danger hover:text-red-700 bg-red-50 hover:bg-red-100 p-2 rounded-md transition-colors"
                        title="Xóa khỏi giỏ"
                      >
                        <Trash2 size={20} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cột Tóm tắt thanh toán */}
          <div className="lg:w-1/3">
            <div className="bg-white rounded-lg shadow-sm border border-border p-6 sticky top-6">
              <h2 className="text-xl font-bold text-text-main mb-6 border-b border-border pb-4">
                Tóm tắt đơn hàng
              </h2>

              <div className="space-y-4 text-text-main mb-6">
                <div className="flex justify-between">
                  <span>Tạm tính:</span>
                  <span className="font-medium">
                    {subtotal.toLocaleString("vi-VN")} đ
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Phí giao hàng:</span>
                  <span className="font-medium">30.000 đ</span>
                </div>
                <div className="border-t border-border pt-4 flex justify-between items-center">
                  <span className="font-bold">Tổng cộng:</span>
                  <span className="text-2xl font-bold text-primary">
                    {(subtotal + 30000).toLocaleString("vi-VN")} đ
                  </span>
                </div>
              </div>

              <Link
                href="/checkout"
                className="w-full bg-primary hover:bg-primary-hover text-white font-bold py-3 px-4 rounded-md transition-colors text-center block"
              >
                TIẾN HÀNH THANH TOÁN
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
