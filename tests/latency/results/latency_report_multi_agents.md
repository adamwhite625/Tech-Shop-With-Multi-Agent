# Multi-Agent RAG Pipeline Latency Benchmark Report

Generated: 2026-07-14 14:36:09
Total queries: 10

## Pipeline Architecture

```
User -> Host Agent (GPT-4o-mini intent classification)
     -> Advisor Agent (RAG orchestrator)
          -> Search Agent (MiniLM embedding + Qdrant vector search)
          -> GPT-4o-mini (answer generation with product context)
     -> Response
```

## 1. End-to-End Latency Summary

| Metric | Value |
|--------|-------|
| MEAN | 4.4549s |
| MEDIAN | 4.4999s |
| MIN | 0.9870s |
| MAX | 9.1006s |
| STDEV | 3.0893s |
| P90 | 9.1006s |
| P95 | 9.1006s |

## 2. Per-Stage Latency Breakdown (seconds)

| Stage | Mean | Median | Min | Max | Stdev | Runs |
|-------|------|--------|-----|-----|-------|------|
| advisor_total | 4.7374 | 4.5284 | 2.3392 | 7.9197 | 2.0862 | 10 |
| e2e_via_host | 4.4549 | 4.4999 | 0.9870 | 9.1006 | 3.0893 | 10 |
| intent_classification_est | 1.1646 | 0.6054 | 0.0000 | 3.2776 | 1.3788 | 10 |
| llm_generation_est | 4.4919 | 4.3564 | 1.9976 | 7.8374 | 2.1000 | 10 |
| retrieval | 0.2455 | 0.3052 | 0.0410 | 0.3816 | 0.1343 | 10 |

**Slowest stage (avg):** `advisor_total` at 4.7374s

## 3. Retrieval Statistics

| Metric | Value |
|--------|-------|
| Mean docs retrieved | 3.0 |
| Min docs retrieved | 3 |
| Max docs retrieved | 3 |

## 4. Per-Query Detail

### 4.1. [Q01] ACTION_CAMERA

**Question:** Tìm camera hành trình GoPro Hero 13

**Answer (truncated):**

> Chúng tôi có hai sản phẩm camera hành trình GoPro Hero 13. Dưới đây là thông tin chi tiết:

1. **Camera hành trình GoPro Hero 13 Black**
   - Giá: 11.490.000 VND
   - [Xem chi tiết sản phẩm](https://pinkcapy.com/camera-hanh-trinh-gopro-hero-13-black)

2. **Camera hành trình GoPro Hero 13 Creator Edi...

**E2E Latency:** 1.4612s | Docs: 3 | Routed to: `search`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.0823 | 5.6% |
| advisor_total | 7.9197 | 542.0% |
| llm_generation_est | 7.8374 | 536.4% |
| e2e_via_host | 1.4612 | 100.0% |
| intent_classification_est | 0.0000 | 0.0% |

---

### 4.2. [Q02] IP_CAMERA

**Question:** Tư vấn mua camera IP WiFi Ezviz 360 độ trong nhà

**Answer (truncated):**

> Xin chào quý khách! Hiện tại, chúng tôi không có sản phẩm camera IP WiFi Ezviz 360 độ dành riêng cho trong nhà. Tuy nhiên, tôi có thể giới thiệu cho quý khách một số sản phẩm camera IP có khả năng quay quét 360 độ mà có thể phù hợp với nhu cầu của quý khách.

1. **Camera IP WiFi Ezviz C6N Pro 2K 3MP...

**E2E Latency:** 9.1006s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.3118 | 3.4% |
| advisor_total | 5.8230 | 64.0% |
| llm_generation_est | 5.5112 | 60.6% |
| e2e_via_host | 9.1006 | 100.0% |
| intent_classification_est | 3.2776 | 36.0% |

---

### 4.3. [Q03] GIMBAL

**Question:** Tay cầm chống rung Gimbal DJI OM 6 có tốt không?

**Answer (truncated):**

> Gimbal DJI OM 6 là một sản phẩm rất chất lượng và được nhiều người dùng đánh giá cao. Với thiết kế nhỏ gọn, dễ dàng mang theo, sản phẩm này giúp bạn ghi lại những khoảnh khắc một cách mượt mà và ổn định, ngay cả khi di chuyển.

Một số tính năng nổi bật của Gimbal DJI OM 6 bao gồm:
- Công nghệ chống ...

**E2E Latency:** 7.1554s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.3816 | 5.3% |
| advisor_total | 7.7332 | 108.1% |
| llm_generation_est | 7.3516 | 102.7% |
| e2e_via_host | 7.1554 | 100.0% |
| intent_classification_est | 0.0000 | 0.0% |

---

### 4.4. [Q04] CAR_ACCESSORY

**Question:** Bộ HUD kính lái VIETMAP hiển thị thông tin gì?

**Answer (truncated):**

> Bộ HUD kính lái VIETMAP thường hiển thị các thông tin quan trọng như tốc độ xe, chỉ dẫn đường, thông tin về tình trạng xe, và các cảnh báo an toàn. Điều này giúp người lái dễ dàng theo dõi các thông tin cần thiết mà không cần phải nhìn xuống bảng điều khiển, từ đó tăng cường sự an toàn khi lái xe. N...

**E2E Latency:** 6.2294s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.3128 | 5.0% |
| advisor_total | 3.3398 | 53.6% |
| llm_generation_est | 3.0270 | 48.6% |
| e2e_via_host | 6.2294 | 100.0% |
| intent_classification_est | 2.8896 | 46.4% |

---

### 4.5. [Q05] ACTION_CAMERA

**Question:** So sánh Insta360 X4 và GoPro

**Answer (truncated):**

> Xin chào quý khách! Hiện tại, chúng tôi không có thông tin cụ thể về sản phẩm Insta360 X4. Tuy nhiên, nếu quý khách đang quan tâm đến camera hành trình, chúng tôi có sản phẩm GoPro Hero 13 Black với giá 11.490.000 VND. 

GoPro Hero 13 Black nổi bật với khả năng quay video chất lượng cao, tính năng c...

**E2E Latency:** 5.4182s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.2985 | 5.5% |
| advisor_total | 3.9935 | 73.7% |
| llm_generation_est | 3.6950 | 68.2% |
| e2e_via_host | 5.4182 | 100.0% |
| intent_classification_est | 1.4247 | 26.3% |

---

### 4.6. [Q06] OUTDOOR_CAMERA

**Question:** Camera an ninh ngoài trời dùng năng lượng mặt trời

**Answer (truncated):**

> Chào bạn! Hiện tại, chúng tôi có hai mẫu camera an ninh ngoài trời sử dụng năng lượng mặt trời mà bạn có thể tham khảo:

1. **Camera năng lượng mặt trời ngoài trời 360 độ 4MP EZVIZ HB8 Lite Kit**
   - Giá: 2.790.000 VND
   - Đường dẫn: [Xem chi tiết](https://pinkcapy.com/camera-ezviz-nang-luong-mat-...

**E2E Latency:** 1.5040s | Docs: 3 | Routed to: `search`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.3178 | 21.1% |
| advisor_total | 5.9270 | 394.1% |
| llm_generation_est | 5.6092 | 373.0% |
| e2e_via_host | 1.5040 | 100.0% |
| intent_classification_est | 0.0000 | 0.0% |

---

### 4.7. [Q07] GIMBAL

**Question:** DJI Ronin RS4 mini dùng cho máy ảnh chịu tải bao nhiêu?

**Answer (truncated):**

> Xin lỗi, nhưng tôi không có thông tin cụ thể về khả năng chịu tải của tay cầm chống rung máy ảnh DJI Ronin RS4 mini. Tuy nhiên, bạn có thể tham khảo thông số kỹ thuật trên trang chính thức của sản phẩm hoặc tìm hiểu thêm từ các nguồn uy tín. Nếu bạn cần tư vấn về các sản phẩm khác của DJI hoặc có nh...

**E2E Latency:** 3.5815s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.3732 | 10.4% |
| advisor_total | 2.3708 | 66.2% |
| llm_generation_est | 1.9976 | 55.8% |
| e2e_via_host | 3.5815 | 100.0% |
| intent_classification_est | 1.2107 | 33.8% |

---

### 4.8. [Q08] TRIPOD

**Question:** Gậy chụp ảnh Tripod Wiwu loại nào giá rẻ?

**Answer (truncated):**

> Gậy chụp ảnh Tripod giá rẻ nhất mà chúng tôi đang cung cấp là gậy Tripod WIWU DETACHABLE SE001 với giá 250.000 VND. Bạn có thể tham khảo thêm thông tin chi tiết [tại đây]( /gay-chup-anh-tripod-wiwu-detachable-se001). Nếu bạn cần thêm thông tin hoặc có câu hỏi nào khác, hãy cho tôi biết!

**E2E Latency:** 1.2046s | Docs: 3 | Routed to: `search`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.2903 | 24.1% |
| advisor_total | 2.3392 | 194.2% |
| llm_generation_est | 2.0489 | 170.1% |
| e2e_via_host | 1.2046 | 100.0% |
| intent_classification_est | 0.0000 | 0.0% |

---

### 4.9. [Q09] CAR_ACCESSORY

**Question:** Android Box xe hơi VIETMAP cấu hình như thế nào?

**Answer (truncated):**

> Android Box xe hơi VIETMAP BS10 (6-128) có cấu hình mạnh mẽ với bộ nhớ RAM 6GB và bộ nhớ trong 128GB, giúp bạn dễ dàng chạy các ứng dụng và lưu trữ dữ liệu. Sản phẩm này được thiết kế để nâng cao trải nghiệm giải trí trên xe hơi, cho phép bạn truy cập internet, xem video, nghe nhạc và sử dụng các ứn...

**E2E Latency:** 0.9870s | Docs: 3 | Routed to: `search`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.0410 | 4.2% |
| advisor_total | 2.8643 | 290.2% |
| llm_generation_est | 2.8233 | 286.0% |
| e2e_via_host | 0.9870 | 100.0% |
| intent_classification_est | 0.0000 | 0.0% |

---

### 4.10. [Q10] GENERAL

**Question:** Gợi ý một số camera hành động chống nước để đi bơi

**Answer (truncated):**

> Chào bạn! Đối với nhu cầu sử dụng camera hành động chống nước để đi bơi, tôi xin gợi ý một số sản phẩm phù hợp:

1. **Camera hành động Akaso 4K EK7000 Pro**: Đây là một lựa chọn tốt với khả năng quay video 4K và thiết kế chống nước, rất thích hợp cho các hoạt động dưới nước. Giá của sản phẩm này là ...

**E2E Latency:** 7.9069s | Docs: 3 | Routed to: `advisor`

| Stage | Time (s) | % of E2E |
|-------|----------|----------|
| retrieval | 0.0456 | 0.6% |
| advisor_total | 5.0634 | 64.0% |
| llm_generation_est | 5.0178 | 63.5% |
| e2e_via_host | 7.9069 | 100.0% |
| intent_classification_est | 2.8435 | 36.0% |

---

## 5. Quick Comparison Table

| ID | Category | Retrieval (s) | Advisor (s) | E2E (s) | Docs | Agent | Question |
|----|----------|---------------|-------------|---------|------|-------|----------|
| Q01 | action_camera | 0.0823 | 7.9197 | 1.4612 | 3 | search | Tìm camera hành trình GoPro Hero 13 |
| Q02 | ip_camera | 0.3118 | 5.8230 | 9.1006 | 3 | advisor | Tư vấn mua camera IP WiFi Ezviz 360 độ trong ... |
| Q03 | gimbal | 0.3816 | 7.7332 | 7.1554 | 3 | advisor | Tay cầm chống rung Gimbal DJI OM 6 có tốt khô... |
| Q04 | car_accessory | 0.3128 | 3.3398 | 6.2294 | 3 | advisor | Bộ HUD kính lái VIETMAP hiển thị thông tin gì... |
| Q05 | action_camera | 0.2985 | 3.9935 | 5.4182 | 3 | advisor | So sánh Insta360 X4 và GoPro |
| Q06 | outdoor_camera | 0.3178 | 5.9270 | 1.5040 | 3 | search | Camera an ninh ngoài trời dùng năng lượng mặt... |
| Q07 | gimbal | 0.3732 | 2.3708 | 3.5815 | 3 | advisor | DJI Ronin RS4 mini dùng cho máy ảnh chịu tải ... |
| Q08 | tripod | 0.2903 | 2.3392 | 1.2046 | 3 | search | Gậy chụp ảnh Tripod Wiwu loại nào giá rẻ? |
| Q09 | car_accessory | 0.0410 | 2.8643 | 0.9870 | 3 | search | Android Box xe hơi VIETMAP cấu hình như thế n... |
| Q10 | general | 0.0456 | 5.0634 | 7.9069 | 3 | advisor | Gợi ý một số camera hành động chống nước để đ... |