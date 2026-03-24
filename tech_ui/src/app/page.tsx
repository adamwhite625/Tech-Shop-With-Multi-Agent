"use client";

import { useEffect, useState } from "react";
import Image from "next/link"; // Dùng Link tạm thay cho Image component phức tạp
import Link from "next/link";
import { ShoppingCart, Flame } from "lucide-react";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

// Định nghĩa kiểu dữ liệu Sản phẩm
interface Product {
  product_id: number;
  title: string;
  price: number;
  thumb: string;
  slug: string;
}

// Định nghĩa kiểu dữ liệu Danh mục
interface Category {
  category_id: number;
  title: string;
  slug: string;
}

// Kiểu dữ liệu danh mục kèm sản phẩm
interface CategoryWithProducts {
  category: Category;
  products: Product[];
}

export default function Home() {
  const [categorizedProducts, setCategorizedProducts] = useState<
    CategoryWithProducts[]
  >([]);
  const [loading, setLoading] = useState(true);
  const { setCartCount } = useStore();

  useEffect(() => {
    fetchCategoriesAndProducts();
  }, []);

  const fetchCategoriesAndProducts = async () => {
    try {
      // 1. Lấy danh sách danh mục
      const categoriesRes = await webClient.get("/categories/");
      let categories: Category[] = categoriesRes.data || [];

      console.log("Danh mục nhận được:", categories);

      // Lọc bỏ danh mục "Root" hoặc danh mục không có sluzg hoặc tên là "Root"
      categories = categories.filter(
        (cat) => cat.title?.toLowerCase() !== "root" && cat.slug !== "root",
      );

      // 2. Lấy sản phẩm của từng danh mục
      const categorizedData: CategoryWithProducts[] = [];

      for (const category of categories) {
        try {
          const productsRes = await webClient.get(`/products/`, {
            params: {
              category_id: category.category_id,
              size: 10, // Hiển thị 10 sản phẩm per danh mục
            },
          });

          if (productsRes.data?.data && Array.isArray(productsRes.data.data)) {
            // Chỉ thêm vào nếu có sản phẩm
            if (productsRes.data.data.length > 0) {
              categorizedData.push({
                category,
                products: productsRes.data.data,
              });
            }
          }
        } catch (err) {
          console.warn(`Lỗi tải sản phẩm danh mục ${category.title}:`, err);
        }
      }

      setCategorizedProducts(categorizedData);
    } catch (error) {
      console.error("Lỗi khi tải danh mục:", error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product_id: number) => {
    try {
      const res = await webClient.post("/cart/items", {
        product_id: product_id,
        quantity: 1,
      });
      // Cập nhật lại số lượng trên Header
      if (res.data && res.data.items) {
        setCartCount(res.data.items.length);
      }
      alert("Đã thêm sản phẩm vào giỏ hàng!");
    } catch (error: any) {
      if (error.response?.status === 401) {
        alert("Vui lòng đăng nhập để mua hàng!");
      } else {
        alert("Có lỗi xảy ra khi thêm vào giỏ.");
      }
    }
  };

  const buildImageUrl = (thumb: string) => {
    if (!thumb) return "";

    const baseOrigin = "https://cellphones.com.vn/media/catalog/product";
    const cdnPrefix =
      "https://cdn2.cellphones.com.vn/insecure/rs:fill:300:300/q:90/plain/";

    return cdnPrefix + baseOrigin + thumb;
  };

  return (
    <div className="pb-12">
      {/* --- HERO BANNER --- */}
      <div className="bg-primary text-white py-12 mb-8">
        <div className="container-custom flex flex-col md:flex-row items-center justify-between">
          <div className="md:w-1/2 space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold leading-tight">
              Đại Tiệc Công Nghệ <br />
              <span className="text-secondary">Giảm Khủng Đến 50%</span>
            </h1>
            <p className="text-lg text-red-100">
              Sắm ngay Camera, Đồng hồ thông minh và Phụ kiện với giá rẻ vô
              địch. Tích hợp AI tư vấn chuyên sâu 24/7!
            </p>
            <button className="bg-secondary text-text-main font-bold px-8 py-3 rounded-md hover:bg-yellow-400 transition-colors">
              MUA NGAY
            </button>
          </div>

          <div className="md:w-1/2 mt-8 md:mt-0 flex justify-end">
            <img
              src="/images/banner.webp"
              alt="Đại Tiệc Công Nghệ"
              className="w-full max-w-md h-64 object-cover rounded-2xl shadow-lg"
            />
          </div>
        </div>
      </div>

      {/* --- DANH SÁCH SẢN PHẨM THEO DANH MỤC --- */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-12">
          {categorizedProducts.map((categoryData) => (
            <div
              key={categoryData.category.category_id}
              className="container-custom"
            >
              {/* Tiêu đề danh mục */}
              <div className="flex items-center gap-2 mb-6 border-b-2 border-primary pb-2 inline-flex">
                <Flame size={28} className="text-primary" />
                <h2 className="text-2xl font-bold uppercase text-text-main">
                  {categoryData.category.title}
                </h2>
              </div>

              {/* Danh sách sản phẩm của danh mục */}
              {categoryData.products.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {categoryData.products.map((product) => (
                    <div
                      key={product.product_id}
                      className="bg-white rounded-lg border border-border overflow-hidden hover:shadow-lg transition-all group flex flex-col"
                    >
                      {/* Ảnh sản phẩm */}
                      <Link
                        href={`/products/${product.slug}`}
                        className="block relative aspect-square p-4 bg-gray-50 flex items-center justify-center"
                      >
                        {product.thumb ? (
                          <img
                            src={buildImageUrl(product.thumb)}
                            alt={product.title}
                            className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform"
                          />
                        ) : (
                          <div className="text-gray-300">No Image</div>
                        )}
                      </Link>

                      {/* Thông tin */}
                      <div className="p-3 flex flex-col flex-grow">
                        <Link
                          href={`/products/${product.slug}`}
                          className="text-sm text-text-main font-medium line-clamp-2 hover:text-primary mb-2 flex-grow"
                        >
                          {product.title}
                        </Link>

                        <div className="font-bold text-primary text-lg mb-3">
                          {Number(product.price).toLocaleString("vi-VN")} đ
                        </div>

                        <button
                          onClick={() => addToCart(product.product_id)}
                          className="w-full bg-blue-btn hover:bg-blue-600 text-white font-medium py-2 rounded-md flex justify-center items-center gap-2 transition-colors mt-auto text-sm"
                        >
                          <ShoppingCart size={16} /> Thêm vào giỏ
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-text-muted">
                  Chưa có sản phẩm trong danh mục này
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
