"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShoppingCart,
  ArrowLeft,
  ShieldCheck,
  Truck,
  RotateCcw,
} from "lucide-react";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

// Định nghĩa kiểu dữ liệu Sản phẩm
interface ProductMeta {
  meta_id: number;
  product_id: number;
  key: string;
  content?: string;
}

interface ProductDetail {
  product_id: number;
  title: string;
  price: number;
  discount: number;
  thumb: string;
  slug: string;
  desc?: string;
  summary?: string;
  sku?: string;
  type?: string;
  quantity: number;
  metas?: ProductMeta[];
}

const buildImageUrl = (thumb: string) => {
  if (!thumb) return "";

  if (thumb.startsWith("http")) return thumb;

  const baseOrigin = "https://cellphones.com.vn/media/catalog/product";
  const cdnPrefix =
    "https://cdn2.cellphones.com.vn/insecure/rs:fill:300:300/q:90/plain/";

  return cdnPrefix + baseOrigin + thumb;
};

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug; // Lấy slug từ URL

  const { setCartCount } = useStore();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [buyQuantity, setBuyQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);

  useEffect(() => {
    if (slug) fetchProductDetail();
  }, [slug]);

  const fetchProductDetail = async () => {
    try {
      // Gọi API lấy chi tiết sản phẩm theo slug
      const res = await webClient.get(`/products/${slug}`);
      setProduct(res.data);
    } catch (error) {
      console.error("Lỗi khi tải chi tiết sản phẩm:", error);
      // Nếu không tìm thấy, có thể API của bạn thiết kế theo dạng ID, ta sẽ xử lý sau.
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;
    setAddingToCart(true);
    try {
      const res = await webClient.post("/cart/items", {
        product_id: product.product_id,
        quantity: buyQuantity,
      });
      if (res.data && res.data.items) {
        setCartCount(res.data.items.length);
      }
      alert("Đã thêm vào giỏ hàng thành công!");
    } catch (error: any) {
      if (error.response?.status === 401) {
        alert("Vui lòng đăng nhập để mua hàng!");
        router.push("/login");
      } else {
        alert("Có lỗi xảy ra khi thêm vào giỏ.");
      }
    } finally {
      setAddingToCart(false);
    }
  };

  if (loading)
    return (
      <div className="text-center py-20">Đang tải thông tin sản phẩm...</div>
    );

  if (!product)
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-text-main mb-4">
          Không tìm thấy sản phẩm
        </h2>
        <Link href="/" className="text-primary hover:underline">
          Quay về trang chủ
        </Link>
      </div>
    );

  return (
    <div className="container-custom py-10">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-text-muted hover:text-primary font-medium transition-colors mb-6"
      >
        <ArrowLeft size={20} /> Tiếp tục mua sắm
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
        <div className="flex flex-col md:flex-row">
          {/* Cột Hình ảnh */}
          <div className="md:w-1/2 p-8 bg-gray-50 flex items-center justify-center border-r border-border min-h-[400px]">
            {product.thumb ? (
              <img
                src={buildImageUrl(product.thumb)}
                alt={product.title}
                className="max-w-full max-h-[400px] object-contain hover:scale-105 transition-transform duration-300"
              />
            ) : (
              <div className="text-gray-400 font-medium">Chưa có hình ảnh</div>
            )}
          </div>

          {/* Cột Thông tin chi tiết */}
          <div className="md:w-1/2 p-8">
            <h1 className="text-2xl md:text-3xl font-bold text-text-main mb-4 leading-tight">
              {product.title}
            </h1>

            <div className="flex items-end gap-4 mb-6 pb-6 border-b border-border">
              <span className="text-4xl font-bold text-primary">
                {Number(product.price).toLocaleString("vi-VN")} đ
              </span>
              {product.discount > 0 && (
                <span className="text-lg text-text-muted line-through mb-1">
                  {(
                    Number(product.price) + Number(product.discount)
                  ).toLocaleString("vi-VN")}{" "}
                  đ
                </span>
              )}
            </div>

            <div className="mb-6 space-y-3 text-sm text-text-main">
              <p className="flex items-center gap-2">
                <ShieldCheck size={18} className="text-success" /> Bảo hành
                chính hãng 12 tháng
              </p>
              <p className="flex items-center gap-2">
                <Truck size={18} className="text-blue-btn" /> Giao hàng toàn
                quốc siêu tốc
              </p>
              <p className="flex items-center gap-2">
                <RotateCcw size={18} className="text-warning" /> Đổi trả miễn
                phí trong 7 ngày nếu có lỗi
              </p>
            </div>

            {/* Chọn số lượng */}
            <div className="mb-8 flex items-center gap-4">
              <span className="font-medium text-text-main">Số lượng:</span>
              <div className="flex items-center border border-border rounded-md">
                <button
                  onClick={() => setBuyQuantity((q) => Math.max(1, q - 1))}
                  className="px-4 py-2 text-text-main hover:bg-gray-100 transition-colors"
                >
                  -
                </button>
                <span className="px-4 py-2 font-medium border-x border-border min-w-[3rem] text-center">
                  {buyQuantity}
                </span>
                <button
                  onClick={() =>
                    setBuyQuantity((q) => Math.min(product.quantity, q + 1))
                  }
                  className="px-4 py-2 text-text-main hover:bg-gray-100 transition-colors"
                >
                  +
                </button>
              </div>
              <span className="text-sm text-text-muted">
                ({product.quantity} sản phẩm có sẵn)
              </span>
            </div>

            {/* Nút Hành động */}
            <div className="flex gap-4">
              <button
                onClick={handleAddToCart}
                disabled={addingToCart || product.quantity === 0}
                className="flex-1 bg-primary hover:bg-primary-hover text-white font-bold py-3.5 px-6 rounded-md transition-colors flex justify-center items-center gap-2 disabled:bg-gray-400"
              >
                <ShoppingCart size={20} />
                {addingToCart ? "ĐANG THÊM..." : "THÊM VÀO GIỎ"}
              </button>
            </div>

            {product.quantity === 0 && (
              <p className="text-danger mt-3 text-sm font-medium">
                Sản phẩm này hiện đang tạm hết hàng.
              </p>
            )}
          </div>
        </div>

        {/* Phần Thông tin chi tiết (Metas) */}
        {product.metas && product.metas.length > 0 && (
          <div className="p-8 border-t border-border">
            <h2 className="text-2xl font-bold text-text-main mb-6">
              Thông tin chi tiết sản phẩm
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {product.metas.map((meta) => (
                <div
                  key={meta.meta_id}
                  className="p-4 bg-gray-50 rounded-lg border border-border"
                >
                  <h3 className="font-semibold text-text-main mb-2 capitalize">
                    {meta.key.replace(/_/g, " ")}
                  </h3>
                  <div
                    className="text-text-muted text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{
                      __html: meta.content || "",
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Phần Mô tả (Description) */}
        {product.desc && (
          <div className="p-8 border-t border-border">
            <h2 className="text-2xl font-bold text-text-main mb-4">Mô tả</h2>
            <div
              className="text-text-muted leading-relaxed"
              dangerouslySetInnerHTML={{ __html: product.desc }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
