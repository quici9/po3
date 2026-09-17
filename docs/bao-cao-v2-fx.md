# Cơ Chế Power of 3 và Phân Bổ Thời Gian Trên Nến H1 — Phiên bản 2 (FX, đã xác thực bằng dữ liệu)

**Phạm vi:** cặp tiền chính. **Dữ liệu:** nến M1 của EURUSD, GBPUSD, USDJPY từ 01/2023 đến 11/09/2026 (histdata.com, quy về UTC), đối chiếu bằng Dukascopy cho EURUSD và GBPUSD; nến H1 Dukascopy 2021–2026 cho thống kê tuần. **Tổng mẫu:** 66.552 nến H1, trong đó 28.973 nến định hướng; 295 tuần cho EURUSD và GBPUSD, 193 tuần cho USDJPY.

**Thay đổi so với phiên bản 1:** toàn bộ số liệu định lượng của bản 1 (71,3%, 46,8%, ma trận AMD, tỷ lệ profile theo phiên, 97,75% trên 3.245 nến) không có nguồn kiểm chứng được và đã bị bác bỏ khi đo trực tiếp. Bản 2 giữ khung khái niệm PO3, thay số liệu bằng số đo thật kèm cỡ mẫu và khoảng tin cậy 95%, và sửa ba lỗi khái niệm: True Open xx:15, ICT Macro mỗi giờ, và quy đổi múi giờ. Chi tiết đối chiếu ở Phụ lục A.

---

## 1. Tóm tắt điều hành

Mô hình Power of 3 (Tích lũy – Thao túng – Phân phối) mô tả nến H1 có hướng như một chuỗi: giá dao động quanh mở cửa, tạo râu ngược hướng, rồi mở rộng thân nến. Trên dữ liệu FX, hình thái này tồn tại nhưng **thời điểm** của nó khác hẳn mô tả phổ biến:

- Cực trị ngược hướng (đáy của nến tăng, đỉnh của nến giảm) hình thành trong **10 phút đầu** ở 69% trường hợp và trong 25 phút đầu ở 89%. Trung vị là phút thứ 4. Không có "đỉnh thao túng" ở phút 11–25.
- Khoảng 21% nến định hướng có râu thao túng in cực trị **ngay phút 0**, gấp gần ba lần mức 7,8% của bước ngẫu nhiên. Đây là quán tính xuyên biên giờ, không phải bẫy giá.
- Một cực trị ngược hướng mới sau phút 35 chỉ xảy ra ở 4,6% nến định hướng. Đây là ngưỡng phủ định luận điểm nến có hướng đáng tin cậy hơn mọi mốc "quý" nào.
- Giờ động lượng cao nhất trong ngày là **09:00 New York**, kế đến 10:00, 11:00, 08:00, rồi 04:00 và 03:00 NY. Giờ 17:00–18:00 NY gần như không có mở rộng.
- Ở cấp tuần, "Thứ Hai là ngày thao túng" (≈50%) trùng với mức bước ngẫu nhiên (55,9%) nên không mang thông tin. Tín hiệu duy nhất vượt nền là **Thứ Tư và Thứ Năm** là ngày có thân thuận hướng lớn nhất (25% mỗi ngày so với nền 20%).

Hệ quả thực hành: cửa sổ chờ thao túng là 10 phút đầu giờ, không phải 15–25. Sau phút 25, xác suất còn cực trị mới chỉ khoảng 11%, và sau phút 35 là dưới 5%.

---

## 2. Nguyên lý Time and Price và tính phân dạng

Khung khái niệm giữ nguyên từ bản 1 và nhất quán với tài liệu ICT: nến H1 tăng tuân theo chuỗi Mở – Đáy – Đỉnh – Đóng (OLHC), nến giảm theo Mở – Đỉnh – Đáy – Đóng (OHLC); giá trên mở cửa là Premium, dưới mở cửa là Discount trong phạm vi giờ đó.

Hai điểm cần hiểu đúng:

1. **Chuỗi OLHC/OHLC hợp lệ ở 97–98% nến định hướng, nhưng đây là điều hiển nhiên**, không phải bằng chứng cho PO3. Một nến đóng cửa trên mở cửa với thân chiếm trên nửa biên độ gần như bắt buộc phải tạo đáy trước đỉnh.
2. **Râu ngược hướng không phải "tất yếu cơ học".** 29% nến định hướng không có râu phía mở cửa đáng kể (dưới 5% biên độ): giá mở cửa và đi thẳng. Đây là profile Trend Runaway, phổ biến hơn bản 1 mô tả.

---

## 3. Cấu trúc thời gian nội vi 60 phút

### 3.1. Sửa hai khái niệm của bản 1

- **"True H1 Open tại xx:15"** không có trong Quarterly Theory. Cả hai nguồn được trích (quartersequence.com, oracleinsights.io) định nghĩa chu kỳ nội ngày là 90 phút với True Open tại phút thứ 22,5, và không định nghĩa True Open cho chu kỳ 60 phút. Khi kiểm định trực tiếp, kịch bản "cực trị hình thành sau phút 15 và vượt qua giá mở xx:15" chỉ xảy ra ở 16,5% nến tăng và 19,2% nến giảm. Mốc neo đúng cho H1 là giá mở cửa xx:00.
- **"ICT Macro xx:50–xx:10 mỗi giờ"** là khái quát sai. Các macro ICT là những cửa sổ cụ thể (08:50–09:10, 09:50–10:10, 10:50–11:10, 11:50–12:10, 13:10–13:40, 15:15–15:45 giờ NY; London 02:33–03:00 và 04:03–04:30). Macro London không nằm ở biên giờ.

### 3.2. Phân bố phút tạo cực trị thao túng (số đo)

Định nghĩa: nến định hướng là nến có thân ≥ 50% biên độ. Cực trị thao túng là đáy của nến tăng hoặc đỉnh của nến giảm. Phút tạo cực trị là phút M1 đầu tiên chạm mức đó. Chỉ tính nến có râu phía mở cửa ≥ 5% biên độ.

| Tập (n) | 00–10 | 11–25 | 26–40 | 41–59 | ≤ 25 phút [CI 95%] | Trung vị | Phút 0 |
|---|---|---|---|---|---|---|---|
| Bản 1 (không nguồn) | 24,5% | 46,8% | 18,2% | 10,5% | 71,3% | — | — |
| EURUSD (6.787) | 68,2% | 20,6% | 8,7% | 2,4% | 88,8% [88,1–89,6] | 5 | 20,8% |
| GBPUSD (6.828) | 69,1% | 19,7% | 8,5% | 2,7% | 88,8% [88,0–89,5] | 4 | 20,3% |
| USDJPY (6.896) | 68,9% | 19,6% | 8,6% | 3,0% | 88,5% [87,7–89,2] | 4 | 21,6% |
| **FX gộp (20.511)** | **68,8%** | **19,9%** | **8,6%** | **2,7%** | **88,7% [88,3–89,1]** | **4** | **20,9%** |
| Bước ngẫu nhiên, cùng bộ lọc | 56,6% | 28,3% | 11,7% | 3,4% | 84,9% | 8 | 7,8% |

Với ngưỡng râu nghiêm hơn (≥ 15% biên độ, loại các râu nhỏ do nhiễu): FX gộp 57,4 / 26,8 / 12,1 / 3,7%, trung vị phút 8; bước ngẫu nhiên 44,4 / 35,6 / 15,7 / 4,3%, trung vị 12. Kết luận không đổi.

Kết quả ổn định theo năm (cột 00–10 dao động 68,1–68,9% qua 2023, 2024, 2025, 2026), theo nguồn dữ liệu (histdata và Dukascopy lệch nhau dưới 0,1 điểm), và không thay đổi khi bỏ hai giờ chứa tin NY (08:00 và 10:00).

### 3.3. Đường tích lũy theo phiên: công cụ dùng trong phiên

Đến phút m, bao nhiêu phần trăm nến định hướng đã in xong cực trị thao túng (FX gộp, râu ≥ 5%):

| Phiên (giờ NY) | ≤ 5 | ≤ 10 | ≤ 15 | ≤ 20 | ≤ 25 | ≤ 30 | ≤ 40 | ≤ 50 |
|---|---|---|---|---|---|---|---|---|
| Tất cả | 55% | 69% | 78% | 84% | 89% | 93% | 97% | 100% |
| Á (19–23) | 59% | 72% | 80% | 86% | 90% | 94% | 98% | 100% |
| London (02–04) | 53% | 67% | 77% | 83% | 88% | 92% | 98% | 100% |
| NY AM (08–10) | 49% | 63% | 73% | 80% | 85% | 92% | 97% | 100% |
| NY PM (13–15) | 56% | 71% | 79% | 86% | 91% | 93% | 98% | 100% |

Cùng bảng với râu ≥ 15%: Tất cả 40 / 57 / 69 / 78 / 84 / 90 / 96 / 99%; NY AM chậm nhất với 34 / 51 / 63 / 73 / 79 / 89 / 96 / 100%.

Cách đọc: nếu đang ở phút 25 của một giờ London và luận điểm là nến tăng, thì 88% khả năng đáy đã in. Một đáy mới sau đó là sự kiện 12%. NY AM là phiên duy nhất cực trị đến muộn hơn rõ rệt, do tin 08:30 và 10:00.

### 3.4. Thời điểm hoàn tất phân phối

Cực trị thuận hướng (đỉnh của nến tăng) có trung vị ở phút 53. 70% nến in cực trị thuận hướng trong 15 phút cuối, 45% trong 5 phút cuối, và 18% đúng phút 59. Râu phía đóng cửa trung bình 16% biên độ, lớn hơn râu thao túng trung bình 14%. Nói cách khác, "pha hồi quy chốt lời cuối giờ" của bản 1 tồn tại nhưng nhỏ: phần lớn nến định hướng đóng cửa gần cực trị.

### 3.5. Mô tả lại chu kỳ 60 phút theo số đo

| Cửa sổ | Điều xảy ra trên dữ liệu FX |
|---|---|
| Phút 0–10 | Cửa sổ thao túng thật sự: 69% cực trị ngược hướng đã in. 21% in ngay phút 0 (quán tính từ giờ trước). |
| Phút 11–25 | Đuôi của pha thao túng: thêm 20% cực trị. Sau phút 25 còn 11%. |
| Phút 26–45 | Mở rộng thân nến. Cực trị ngược hướng mới hiếm (8,6%); sau phút 35 chỉ 4,6%. |
| Phút 46–59 | Hoàn tất: 70% cực trị thuận hướng in trong cửa sổ này. |

Bản 1 dùng ba cách chia giờ khác nhau (theo quý 15 phút, theo ma trận 10/25/45, theo profile 15/25/50). Bản 2 bỏ các mốc cố định và dùng đường tích lũy ở mục 3.3.

---

## 4. Năm profile nến H1

### 4.1. Định nghĩa vận hành (loại trừ lẫn nhau, xét theo thứ tự)

ATR là trung bình biên độ 24 nến H1 trước đó. r là tỷ lệ thân trên biên độ.

1. **News/Outlier:** biên độ ≥ 2,5 ATR.
2. **Trend Runaway:** r ≥ 0,75 và râu phía mở cửa < 5%.
3. **Classic Expansion:** biên độ ≥ 0,8 ATR, r ≥ 0,65, râu phía mở cửa 5–30%, râu phía đóng cửa ≤ 15%, chuỗi OLHC/OHLC hợp lệ.
4. **Consolidation Reversal:** r < 0,4 và một râu ≥ 50% biên độ.
5. **Seek & Destroy:** r < 0,3 và cả hai râu ≥ 25%.
6. **Khác:** phần còn lại.

### 4.2. Tỷ lệ đo được theo phiên (FX gộp)

| Phiên (n) | Classic Expansion | Consolidation Reversal | News/Outlier | Seek & Destroy | Trend Runaway | Khác |
|---|---|---|---|---|---|---|
| Á (14.102) | 5,7% | 30,3% | 1,2% | 6,4% | 7,6% | 48,7% |
| London (8.623) | 9,9% | 29,4% | 3,4% | 6,5% | 6,6% | 44,3% |
| NY AM (8.098) | 9,5% | 28,0% | 11,5% | 6,5% | 5,6% | 38,8% |
| NY PM (8.098) | 7,5% | 30,2% | 2,1% | 6,4% | 7,0% | 46,9% |

Bản 1 nêu Á 60% Seek & Destroy, London 50% Classic Expansion, NY 40% Classic Expansion. Số đo cho thấy hình dạng nến gần như giống nhau giữa các phiên: Classic Expansion theo định nghĩa chặt chỉ 6–10%, Seek & Destroy 6–7% ở mọi phiên. Khác biệt thật giữa các phiên nằm ở **độ lớn** nến và ở tỷ lệ nến tin, không ở hình dạng.

---

## 5. Biến thiên theo phiên giao dịch

### 5.1. Khung giờ (sửa quy đổi múi giờ)

Giờ ICT tính theo múi America/New_York, có DST. Quy đổi sang Việt Nam phải dùng hai bảng; bản 1 chỉ đúng mùa đông.

| Phiên | Giờ New York | Giờ VN mùa đông (tháng 11 – tháng 3) | Giờ VN mùa hè (tháng 3 – tháng 11) |
|---|---|---|---|
| Á | 19:00 – 00:00 | 07:00 – 12:00 | 06:00 – 11:00 |
| London Killzone | 02:00 – 05:00 | 14:00 – 17:00 | 13:00 – 16:00 |
| NY AM | 08:00 – 11:00 | 20:00 – 23:00 | 19:00 – 22:00 |
| NY PM | 13:00 – 16:00 | 01:00 – 04:00 | 00:00 – 03:00 |

### 5.2. Đặc trưng đo được (FX gộp)

| Tiêu chí | Á | London | NY AM | NY PM |
|---|---|---|---|---|
| Thân nến / ATR (trung bình) | 0,39 | 0,60 | 0,80 | 0,45 |
| Biên độ / ATR | 0,81 | 1,20 | 1,61 | 0,91 |
| P(mở rộng: r ≥ 0,65 và biên độ ≥ 0,8 ATR) | 13,5% | 23,2% | 25,5% | 17,2% |
| Tỷ lệ thân trung bình r | 0,45 | 0,45 | 0,46 | 0,45 |
| Trung vị phút tạo cực trị thao túng | 4 | 5 | 6 | 4 |
| Cực trị thao túng ≤ 10 phút | 72% | 67% | 63% | 71% |
| Tỷ lệ nến tin (biên độ ≥ 2,5 ATR) | 1,2% | 3,4% | 11,5% | 2,1% |

Tỷ lệ thân trung bình giống nhau ở mọi phiên (0,45–0,46). Bản 1 nói thân nến Á "dưới 45% biên độ" còn London "65–85%": không đúng. Phiên chỉ thay đổi độ lớn tuyệt đối của nến, không thay đổi hình dạng.

### 5.3. Giờ động lượng trong ngày (FX gộp, giờ NY)

| Giờ NY | Thân / ATR | Biên độ / ATR | P(mở rộng) | Tỷ lệ nến tin |
|---|---|---|---|---|
| 02:00 | 0,47 | 0,96 | 18,8% | 1,6% |
| 03:00 | 0,64 | 1,29 | 24,6% | 3,9% |
| 04:00 | 0,68 | 1,36 | 26,2% | 4,6% |
| 05:00 | 0,56 | 1,17 | 21,9% | 2,5% |
| 08:00 | 0,70 | 1,39 | 24,7% | 8,4% |
| **09:00** | **0,90** | **1,77** | **26,4%** | 14,2% |
| 10:00 | 0,81 | 1,67 | 25,4% | 11,9% |
| 11:00 | 0,78 | 1,59 | 26,5% | 10,2% |
| 12:00 | 0,57 | 1,17 | 23,2% | 2,6% |
| 13:00 | 0,47 | 0,96 | 19,6% | 1,3% |
| 14:00 | 0,47 | 0,93 | 17,6% | 2,5% |
| 15:00 | 0,42 | 0,83 | 14,5% | 2,6% |
| 17:00 | 0,27 | 0,61 | 5,6% | 0,6% |
| 18:00 | 0,30 | 0,71 | 6,9% | 1,2% |
| 21:00 | 0,46 | 0,92 | 17,4% | 1,7% |

Xếp hạng theo thân / ATR: 09:00, 10:00, 11:00, 08:00, 04:00, 03:00 NY. Giờ 09:00 NY có một phần đóng góp từ tin 08:30 kéo dài và mở cửa chứng khoán 09:30; ngay cả khi loại giờ 08:00 và 10:00, thứ hạng không đổi. Silver Bullet 10:00–11:00 của bản 1 là giờ tốt nhưng không phải cao nhất trên FX; 09:00 mạnh hơn. Trong London, 04:00 NY mạnh hơn 02:00 và 03:00.

Phút tạo cực trị thao túng theo giờ không khác nhau nhiều: trung vị 4–7 phút ở mọi giờ London và NY; chậm nhất là 08:00 NY (trung vị 7, 60% trong 10 phút đầu) và nhanh nhất 11:00, 13:00, 14:00 NY (trung vị 4, 72–73% trong 10 phút đầu).

---

## 6. Ngày trong tuần: thao túng và phân phối ở cấp tuần

Tuần tính từ mở cửa Chủ nhật 18:00 NY đến đóng cửa Thứ Sáu; hướng tuần là đóng cửa so với mở cửa tuần. Ba chỉ số: ngày tạo cực trị ngược hướng tuần (ngày thao túng), ngày tạo cực trị thuận hướng (ngày kết thúc phân phối), ngày có thân thuận hướng lớn nhất (ngày phân phối chính). Mốc so sánh là bước ngẫu nhiên 5 ngày cùng cách đo.

| Thứ | Ngày thao túng EUR / GBP / JPY | Ngày kết thúc phân phối EUR / GBP / JPY | Ngày phân phối chính EUR / GBP / JPY | Bước ngẫu nhiên: thao túng / kết thúc / chính | Biên độ ngày / TB |
|---|---|---|---|---|---|
| Thứ Hai | 54 / 50 / 47% | 4 / 2 / 3% | 15 / 17 / 16% | 56 / 4 / 20% | 0,91 |
| Thứ Ba | 19 / 22 / 26% | 9 / 11 / 9% | 20 / 19 / 23% | 20 / 9 / 20% | 0,98 |
| Thứ Tư | 14 / 15 / 15% | 18 / 14 / 18% | **25 / 20 / 23%** | 13 / 13 / 20% | 1,06 |
| Thứ Năm | 9 / 9 / 9% | 25 / 25 / 25% | **25 / 25 / 21%** | 8 / 20 / 20% | 1,08 |
| Thứ Sáu | 5 / 5 / 3% | 44 / 48 / 45% | 16 / 19 / 18% | 4 / 55 / 20% | 0,97 |

EURUSD và GBPUSD: 295 tuần (2021–2026); USDJPY: 193 tuần (2023–2026).

Đọc bảng này cần mốc bước ngẫu nhiên. Trong một tuần đóng cửa có hướng, cực trị ngược hướng tất yếu nghiêng về đầu tuần và cực trị thuận hướng nghiêng về cuối tuần, kể cả khi giá hoàn toàn ngẫu nhiên. Vì vậy:

- "Thứ Hai là ngày thao túng" (47–54%) **không mang thông tin**: bước ngẫu nhiên cho 56%.
- "Thứ Sáu kết thúc phân phối" (44–48%) thực ra **thấp hơn** ngẫu nhiên (55%): Thứ Sáu hồi quy nhiều hơn kỳ vọng ngẫu nhiên.
- Tín hiệu thật duy nhất là **Thứ Tư và Thứ Năm** là ngày phân phối chính, 20–25% so với nền 20%, với khoảng tin cậy của EURUSD (20,5–30,3%) vừa vượt nền. Thứ Hai thấp hơn nền (15–17%, khoảng tin cậy 11–22%). Biên độ ngày cũng lớn nhất vào Thứ Năm và nhỏ nhất Thứ Hai.

Kết luận thực hành: kỳ vọng phân phối tuần vào Thứ Tư và Thứ Năm là có cơ sở nhưng biên lợi thế nhỏ (khoảng 5 điểm phần trăm trên nền 20%). Kỳ vọng "Thứ Hai tạo đáy tuần" không phải lợi thế vì bước ngẫu nhiên cũng cho kết quả đó.

---

## 7. Giao thức thực thi theo nến H1 (điều chỉnh theo số đo)

### 7.1. Bối cảnh khung lớn (D1/H4)

Giữ nguyên từ bản 1: xác định mục tiêu rút thanh khoản (DOL) và thiên kiến trước khi xét nến H1. Chỉ tìm lệnh mua khi giá dưới mở cửa giờ nếu thiên kiến tăng.

### 7.2. Đồng hồ nội vi (thay đổi lớn so với bản 1)

- **Mốc neo duy nhất là giá mở cửa xx:00.** Bỏ mốc True Open xx:15.
- **Phút 0–10 là cửa sổ thao túng.** Đây là lúc râu ngược hướng hình thành ở 69% trường hợp. Bản 1 khuyên "không hành động trong 10 phút đầu"; số đo nói ngược lại: 10 phút đầu là nơi cần theo dõi sát nhất trên M1.
- **Phút 11–25 là đuôi thao túng** với thêm 20%. Vào lệnh sau khi có xác nhận dịch chuyển cấu trúc trên M1/M5 trong cửa sổ này vẫn bắt được 89% cực trị đã in.
- **Sau phút 25**, nếu giá vẫn chưa tạo râu ngược hướng và đi ngang, nến có nhiều khả năng là Consolidation Reversal hoặc Khác chứ không phải Classic Expansion đến muộn.

### 7.3. Xác nhận trên M1/M5

Giữ ba yếu tố của bản 1 (quét thanh khoản, phân kỳ SMT, dịch chuyển cấu trúc / CISD). Đây là các điều kiện định tính chưa được đo trong nghiên cứu này; chúng không bị bác bỏ nhưng cũng chưa được xác nhận.

### 7.4. Quản trị vị thế

- **Dừng lỗ** dưới đáy râu thao túng, như bản 1.
- **Ngưỡng phủ định luận điểm:** một cực trị ngược hướng mới sau phút 35 chỉ xảy ra ở 4,6% nến định hướng có râu. Bản 1 dùng mốc này đúng, nhưng lý do là số đo trên chứ không phải "lý thuyết quý".
- **Chốt lời:** 70% nến định hướng in cực trị thuận hướng trong 15 phút cuối, 45% trong 5 phút cuối. Chốt sớm ở phút 48–55 như bản 1 khuyên sẽ bỏ lỡ phần cuối của phân phối trong gần một nửa trường hợp. Chốt phần còn lại tại phút 57–59 hoặc theo mục tiêu giá hợp lý hơn.

---

## 8. Kết luận

Nến H1 trên FX có cấu trúc thời gian đo được: cực trị ngược hướng dồn vào 10 phút đầu, thân nến mở rộng từ phút 25 đến 55, cực trị thuận hướng in trong 15 phút cuối. Cấu trúc này nhất quán qua ba cặp tiền, bốn năm, hai nguồn dữ liệu và hai ngưỡng lọc. Phần "thông tin" vượt trên bước ngẫu nhiên là ở đầu giờ: cực trị in sớm hơn và ngay phút 0 nhiều hơn ngẫu nhiên, phản ánh quán tính xuyên biên giờ.

Điều không tồn tại trên dữ liệu: đỉnh thao túng ở phút 11–25, True Open xx:15, macro mỗi giờ, khác biệt hình dạng nến giữa các phiên, và "Thứ Hai là ngày thao túng" như một lợi thế. Giờ động lượng cao nhất là 09:00 NY, kế đến 10:00 và 11:00; ngày phân phối tuần nghiêng nhẹ về Thứ Tư và Thứ Năm.

---

## Phụ lục A. Đối chiếu từng luận điểm của bản 1

| Luận điểm bản 1 | Nguồn gắn | Kết quả kiểm tra | Xử lý trong bản 2 |
|---|---|---|---|
| 97,75% trong 3.245 nến có râu ngược chiều | Video YouTube tiếng Pháp (04/2026) | Không phải khảo sát; con số gần như hiển nhiên | Bỏ. Thay bằng "29% nến định hướng không có râu phía mở cửa". |
| 24,5 / 46,8 / 18,2 / 10,5%; 71,3% trong 25 phút | Bài Reddit "MACRO" | Không có dữ liệu trong nguồn; đo được 68,8 / 19,9 / 8,6 / 2,7%; 88,7% | Thay bằng số đo, mục 3.2. |
| Ma trận xác suất AMD theo 4 cửa sổ | Bài tổng quan PO3 | Không nguồn; không có định nghĩa đo | Thay bằng đường tích lũy, mục 3.3. |
| Tỷ lệ profile theo phiên (60/25/15, 50/35/15, 40/40/20) | Scribd PDF | Không nguồn; đo được khác hoàn toàn | Thay bằng số đo, mục 4.2. |
| Z-Swing: 50% tại Fib 1.0, 82% trong 1.0–2.0 | Bài Reddit | Không truy cập được; trích dẫn hỏng "([])" | Bỏ khỏi phần định lượng. |
| True H1 Open = mở cửa M15 thứ hai (xx:15) | quartersequence.com, oracleinsights.io | Sai: hai nguồn chỉ định nghĩa chu kỳ 90 phút | Bỏ; kiểm định trực tiếp cho 16–19%. |
| ICT Macro xx:50–xx:10 mỗi giờ | LuxAlgo | Sai: nguồn liệt kê cửa sổ cụ thể | Sửa, mục 3.1. |
| Quy đổi EST sang GMT+7 | — | Sai 1 giờ mùa DST | Sửa, mục 5.1. |
| Nghiên cứu "Quarter-Hour Effect" xác nhận bùng nổ biên giờ | arXiv 2607.09426 | Bài có thật nhưng về crypto perpetual trên Binance | Không dùng cho FX. |
| OLHC / OHLC; Premium/Discount so với mở cửa; London KZ 02–05; Silver Bullet 10–11 NY | Tài liệu ICT | Đúng | Giữ, có ghi chú số đo. |

## Phụ lục B. Phương pháp

- **Dựng nến H1 từ M1** để biên nến khớp với dữ liệu phút; loại giờ có dưới 30 nến M1.
- **Múi giờ:** timestamp UTC; phiên và giờ trong ngày gán theo America/New_York bằng tz database.
- **Nến định hướng:** thân ≥ 50% biên độ. **Có râu thao túng:** râu phía mở cửa ≥ 5% (kiểm tra lại với 15%).
- **Phút tạo cực trị:** phút M1 đầu tiên chạm đáy (nến tăng) hoặc đỉnh (nến giảm).
- **Mốc bước ngẫu nhiên:** 200.000 nến giả lập gồm 60 bước Gaussian, áp cùng bộ lọc rồi đo cùng chỉ số. Với tuần: 200.000 tuần giả lập gồm 5 ngày × 24 bước.
- **Khoảng tin cậy:** Wilson 95%.
- **Nguồn dữ liệu:** histdata.com (M1, EST cố định, đã quy về UTC) cho EURUSD, GBPUSD, USDJPY 2023-01 → 2026-09-11; Dukascopy (M1 2023-09 → 2026-09 và H1 2021-01 → 2026-08) cho EURUSD, GBPUSD làm đối chiếu và thống kê tuần.
- **Mã và báo cáo chi tiết:** `po3_stats.py`, `po3_fx_verify.py`, thư mục `reports/`.

## Phụ lục C. Nguồn còn được sử dụng

1. quartersequence.com, "Reading True Opens" (định nghĩa True Open theo chu kỳ 90 phút).
2. oracleinsights.io, "True Opens — The Levels That Actually Matter".
3. LuxAlgo Library, "ICT Macros" (danh sách cửa sổ macro).
4. Kim & Hansen, "The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures", arXiv 2607.09426 (chỉ để tham chiếu về chu kỳ theo đồng hồ trên crypto).
5. Tài liệu ICT tổng quan về Power of 3 và Killzone (khái niệm, không dùng số liệu).
