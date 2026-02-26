"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Package,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Bot,
} from "lucide-react";
import { webClient } from "@/lib/axios";
import { useStore } from "@/store/useStore";

// Định nghĩa kiểu dữ liệu Đơn hàng
interface Order {
  order_id: number;
  grand_total: number;
  status: number;
  created_at: string;
}

export default function OrdersPage() {
  const router = useRouter();
  const { user } = useStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionStorage.getItem("token")) {
      router.push("/login");
      return;
    }
    fetchOrders();
  }, [router]);

  const fetchOrders = async () => {
    try {
      // Gọi API lấy danh sách đơn hàng của user hiện tại
      // Lưu ý: Đảm bảo Backend của bạn có API GET /api/orders/me hoặc tương tự
      const res = await webClient.get("/orders/me");
      // Tùy cấu trúc API trả về, có thể là res.data hoặc res.data.data
      const ordersData = Array.isArray(res.data)
        ? res.data
        : res.data.data || [];

      // Sắp xếp đơn hàng mới nhất lên đầu
      const sortedOrders = ordersData.sort(
        (a: Order, b: Order) => b.order_id - a.order_id,
      );
      setOrders(sortedOrders);
    } catch (error) {
      console.error("Lỗi khi tải lịch sử đơn hàng:", error);
    } finally {
      setLoading(false);
    }
  };

  // Hàm helper để render Trạng thái đơn hàng cho đẹp
  const renderStatus = (status: number) => {
    switch (status) {
      case 1:
        return (
          <span className="flex items-center gap-1 text-warning bg-yellow-50 px-3 py-1 rounded-full font-medium text-sm border border-yellow-200">
            <Clock size={16} /> Chờ xử lý
          </span>
        );
      case 2:
        return (
          <span className="flex items-center gap-1 text-blue-btn bg-blue-50 px-3 py-1 rounded-full font-medium text-sm border border-blue-200">
            <Package size={16} /> Đã thanh toán
          </span>
        );
      case 3:
        return (
          <span className="flex items-center gap-1 text-success bg-green-50 px-3 py-1 rounded-full font-medium text-sm border border-green-200">
            <CheckCircle2 size={16} /> Hoàn thành
          </span>
        );
      case 8:
        return (
          <span className="flex items-center gap-1 text-danger bg-red-50 px-3 py-1 rounded-full font-medium text-sm border border-red-200">
            <XCircle size={16} /> Đã hủy
          </span>
        );
      default:
        return (
          <span className="text-gray-500 bg-gray-100 px-3 py-1 rounded-full text-sm">
            Không rõ
          </span>
        );
    }
  };

  if (loading)
    return (
      <div className="text-center py-20">Đang tải lịch sử đơn hàng...</div>
    );

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

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <h1 className="text-3xl font-bold text-primary flex items-center gap-3">
          <Package size={32} /> Đơn Hàng Của Tôi
        </h1>

        {/* Banner hướng dẫn dùng AI */}
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-100 p-4 rounded-lg flex items-start gap-3 max-w-md shadow-sm">
          <div className="bg-primary text-white p-2 rounded-full shrink-0 mt-0.5">
            <Bot size={20} />
          </div>
          <div>
            <h4 className="font-bold text-text-main text-sm">
              Trợ lý AI hỗ trợ 24/7
            </h4>
            <p className="text-xs text-text-muted mt-1 leading-relaxed">
              Bạn muốn hủy đơn hoặc kiểm tra chi tiết? Hãy mở Khung Chat góc
              phải và nhắn: <br />
              <strong className="text-primary">
                "Hủy giúp tôi đơn hàng số [Mã Đơn]"
              </strong>
            </p>
          </div>
        </div>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white p-12 rounded-lg shadow-sm border border-border text-center">
          <Package size={64} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-bold text-text-main mb-2">
            Bạn chưa có đơn hàng nào
          </h3>
          <p className="text-text-muted mb-6">
            Hãy lướt xem các sản phẩm công nghệ hot nhất và đặt hàng ngay nhé.
          </p>
          <Link
            href="/"
            className="inline-block bg-primary hover:bg-primary-hover text-white font-bold py-3 px-8 rounded-md transition-colors"
          >
            MUA SẮM NGAY
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-border overflow-hidden">
          <div className="hidden md:grid grid-cols-12 gap-4 p-4 bg-gray-50 border-b border-border font-bold text-text-muted text-sm">
            <div className="col-span-2">Mã Đơn</div>
            <div className="col-span-3">Ngày đặt</div>
            <div className="col-span-3 text-right">Tổng tiền</div>
            <div className="col-span-4 pl-8">Trạng thái</div>
          </div>

          <div className="divide-y divide-border">
            {orders.map((order) => (
              <div
                key={order.order_id}
                className="p-4 grid grid-cols-1 md:grid-cols-12 gap-4 items-center hover:bg-gray-50 transition-colors"
              >
                <div className="col-span-2">
                  <span className="md:hidden font-bold text-text-muted mr-2">
                    Mã đơn:
                  </span>
                  <span className="font-bold text-lg text-text-main">
                    #{order.order_id}
                  </span>
                </div>

                <div className="col-span-3 text-sm text-text-muted">
                  <span className="md:hidden font-bold mr-2">Ngày:</span>
                  {new Date(order.created_at).toLocaleString("vi-VN")}
                </div>

                <div className="col-span-3 md:text-right font-bold text-primary">
                  <span className="md:hidden font-bold text-text-muted mr-2 text-sm">
                    Tổng:
                  </span>
                  {Number(order.grand_total).toLocaleString("vi-VN")} đ
                </div>

                <div className="col-span-4 md:pl-8 flex justify-between items-center">
                  {renderStatus(order.status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
