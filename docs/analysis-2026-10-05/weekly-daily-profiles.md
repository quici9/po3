# Weekly profile và daily profile — thống kê, xếp loại, chọn lọc, phân bổ

Sinh bởi `po3_profiles.py` ngày 2026-10-05. Dữ liệu M1 histdata UTC, EURUSD, GBPUSD; ngày 2023-01-02 → 2026-09-11. Mẫu: **1915 ngày** (957 ngày mỗi cặp) và **386 tuần**. Cột *Ngẫu nhiên* là cùng pipeline chạy trên bước đi ngẫu nhiên Gauss không trôi, biến động hằng số, 1939 ngày: đó là tỷ lệ mà **mọi** chuỗi giá sinh ra do số học, không mang thông tin. Dấu `*` ở cột lệch nghĩa là khoảng tin cậy 95% của hiệu không chứa 0.

Định nghĩa đóng băng cùng file (xem docstring đầu `po3_profiles.py`): ngày = nến D 17:00→17:00 New York (giống nến D của OANDA trên TradingView, nên tối Chủ nhật thuộc về thứ Hai); tuần = thứ Hai→thứ Sáu cùng tuần ISO; ba khối trong ngày là **Á** 17:00–02:00, **Luân Đôn** 02:00–07:00, **New York** 07:00–17:00 — cắt như vậy để mỗi giờ quyết định của quy trình (03:00 và 09:00) nằm trong một khối; ba pha trong tuần là **đầu tuần** (thứ 2–3), **giữa tuần** (thứ 4), **cuối tuần** (thứ 5–6).

> Cảnh báo đọc số: nhãn profile chỉ xác định được **sau khi** chu kỳ đóng. Bảng tần suất ở mục 1 và 3 là mô tả, không phải tín hiệu. Phần dùng được trong lúc giao dịch nằm ở mục 2, 3, 5, 6 và 7: xác suất có điều kiện tính từ thông tin đã biết tại 03:00 hoặc 09:00 New York.


## 1. Daily profile — cực trị ngày rơi vào khối nào

Ô = tỷ lệ số ngày có đáy ngày ở khối hàng và đỉnh ngày ở khối cột (trong ngoặc là số ngày).

|  | Á | Luân Đôn | New York | Tổng |
|---|---|---|---|---|
| Á | 0.3% (5) | 2.7% (52) | 22.2% (426) | 25.2% |
| Luân Đôn | 2.9% (56) | 1.0% (19) | 15.1% (290) | 19.1% |
| New York | 20.5% (392) | 16.6% (317) | 18.7% (358) | 55.7% |
| Tổng | 23.7% | 20.3% | 56.1% | 100% |

Cùng ma trận trên bước đi ngẫu nhiên (để so):

|  | Á | Luân Đôn | New York | Tổng |
|---|---|---|---|---|
| Á | 4.1% (80) | 5.5% (106) | 33.5% (649) | 43.1% |
| Luân Đôn | 6.9% (134) | 0.2% (4) | 7.9% (153) | 15.0% |
| New York | 29.8% (577) | 7.2% (140) | 5.0% (96) | 41.9% |
| Tổng | 40.8% | 12.9% | 46.3% | 100% |

Xếp loại 9 ô theo tần suất, kèm tính chất của từng loại:

| profile | n | Tỷ lệ | Ngẫu nhiên | Lệch so với ngẫu nhiên (điểm %) | Biên độ ngày (pip, trung vị) | Đóng cửa trong biên (%, trung vị) | P(đáy trước đỉnh) | Ngày rộng (> 1,3 ATR20) |
|---|---|---|---|---|---|---|---|---|
| đáy Á / đỉnh Á | 5 | 0.3% [0.1–0.6] | 4.1% | -3.9 [-4.8; -3.0] * | 71 | 44 | 60% | 0% |
| đáy Á / đỉnh Luân Đôn | 52 | 2.7% [2.1–3.5] | 5.5% | -2.8 [-4.0; -1.5] * | 61 | 51 | 100% | 10% |
| đáy Á / đỉnh New York | 426 | 22.2% [20.4–24.2] | 33.5% | -11.2 [-14.0; -8.4] * | 78 | 77 | 100% | 26% |
| đáy Luân Đôn / đỉnh Á | 56 | 2.9% [2.3–3.8] | 6.9% | -4.0 [-5.3; -2.6] * | 58 | 46 | 0% | 11% |
| đáy Luân Đôn / đỉnh Luân Đôn | 19 | 1.0% [0.6–1.5] | 0.2% | +0.8 [+0.3; +1.3] * | 69 | 46 | 58% | 16% |
| đáy Luân Đôn / đỉnh New York | 290 | 15.1% [13.6–16.8] | 7.9% | +7.3 [+5.2; +9.3] * | 74 | 77 | 100% | 19% |
| đáy New York / đỉnh Á | 392 | 20.5% [18.7–22.3] | 29.8% | -9.3 [-12.0; -6.6] * | 75 | 25 | 0% | 21% |
| đáy New York / đỉnh Luân Đôn | 317 | 16.6% [15.0–18.3] | 7.2% | +9.3 [+7.3; +11.4] * | 72 | 25 | 0% | 15% |
| đáy New York / đỉnh New York | 358 | 18.7% [17.0–20.5] | 5.0% | +13.7 [+11.7; +15.7] * | 66 | 45 | 49% | 15% |

Theo ngày trong tuần (tỷ lệ các ngày của cột đó):

| Ngày | n | đáy ở Á | đáy ở Luân Đôn | đáy ở New York | đỉnh ở Á | đỉnh ở Luân Đôn | đỉnh ở New York | Biên độ (pip, trung vị) | P(đóng cửa trên mở 00:00) |
|---|---|---|---|---|---|---|---|---|---|
| Thứ 2 | 381 | 36% | 19% | 44% | 23% | 23% | 55% | 67 | 55% |
| Thứ 3 | 386 | 20% | 19% | 61% | 26% | 20% | 54% | 69 | 49% |
| Thứ 4 | 382 | 23% | 22% | 56% | 25% | 19% | 56% | 76 | 50% |
| Thứ 5 | 382 | 24% | 17% | 59% | 25% | 21% | 54% | 79 | 47% |
| Thứ 6 | 384 | 23% | 18% | 59% | 20% | 19% | 61% | 73 | 51% |

Phiên đặt cực trị, chi tiết hơn (6 phiên, % số ngày):

| Phiên | Đặt đáy ngày | Đặt đỉnh ngày | Đặt đáy (ngẫu nhiên) | Biên độ phiên (pip, trung vị) |
|---|---|---|---|---|
| Á 20–00 | 8.2% | 12.7% | 12.9% | 18 |
| 00–02 | 2.6% | 2.8% | 6.5% | 11 |
| Luân Đôn 02–05 | 13.6% | 13.8% | 9.6% | 27 |
| 05–07 | 5.5% | 6.4% | 5.4% | 21 |
| NY sáng 07–11 | 23.8% | 22.9% | 11.4% | 38 |
| NY chiều 11–16 | 25.7% | 26.8% | 18.6% | 34 |
| ngoài phiên | 20.7% | 14.6% | 35.5% |  |

## 2. Tại 03:00 và 09:00 New York thì cực trị ngày đã in chưa

Đây là bảng dùng được trong ngày: nó nói phần biên độ còn lại sau giờ quyết định.

| Mốc | Ngày | n | P(đỉnh ngày đã in) | P(đáy ngày đã in) | P(cả hai đã in) | Biên độ còn lại sau mốc (pip): Q1 / trung vị / Q3 |
|---|---|---|---|---|---|---|
| 03:00 | Thứ 2 | 381 | 26.2% [22.1–30.9] | 36.7% [32.1–41.7] | 1% | 41 / 57 / 79 |
| 03:00 | Thứ 3 | 386 | 29.5% [25.2–34.3] | 23.6% [19.6–28.1] | 0% | 47 / 64 / 84 |
| 03:00 | Thứ 4 | 382 | 28.8% [24.5–33.5] | 25.7% [21.5–30.3] | 0% | 52 / 69 / 92 |
| 03:00 | Thứ 5 | 382 | 28.5% [24.2–33.3] | 25.4% [21.3–30.0] | 0% | 55 / 71 / 91 |
| 03:00 | Thứ 6 | 384 | 22.1% [18.3–26.6] | 26.8% [22.6–31.5] | 1% | 48 / 67 / 88 |
| 05:00 | Thứ 2 | 381 | 36.7% [32.1–41.7] | 48.0% [43.1–53.0] | 4% | 37 / 53 / 72 |
| 05:00 | Thứ 3 | 386 | 40.7% [35.9–45.6] | 36.0% [31.4–40.9] | 2% | 42 / 57 / 74 |
| 05:00 | Thứ 4 | 382 | 37.7% [33.0–42.7] | 37.4% [32.7–42.4] | 3% | 47 / 63 / 86 |
| 05:00 | Thứ 5 | 382 | 39.8% [35.0–44.8] | 36.4% [31.7–41.3] | 3% | 51 / 66 / 86 |
| 05:00 | Thứ 6 | 384 | 32.6% [28.1–37.4] | 36.2% [31.5–41.1] | 3% | 44 / 60 / 82 |
| 09:00 | Thứ 2 | 381 | 55.4% [50.4–60.3] | 62.2% [57.2–66.9] | 22% | 30 / 39 / 56 |
| 09:00 | Thứ 3 | 386 | 54.7% [49.7–59.6] | 46.9% [42.0–51.9] | 14% | 34 / 47 / 60 |
| 09:00 | Thứ 4 | 382 | 50.8% [45.8–55.8] | 51.0% [46.0–56.0] | 15% | 40 / 54 / 73 |
| 09:00 | Thứ 5 | 382 | 51.3% [46.3–56.3] | 47.6% [42.7–52.7] | 10% | 40 / 54 / 71 |
| 09:00 | Thứ 6 | 384 | 47.4% [42.5–52.4] | 51.0% [46.1–56.0] | 13% | 37 / 49 / 70 |

## 3. Mức thanh khoản ngày trước và tuần trước (DOL) có bị quét không

Bảng này nối trực tiếp với panel DOL của indicator v7: PDH/PDL là đỉnh/đáy nến D hôm trước, PWH/PWL là đỉnh/đáy nến W tuần trước. *Quét* = giá chạm vượt mức đó, không cần đóng cửa ngoài.

| Ngày | n | P(quét PDH) | P(quét PDL) | P(quét cả hai) | P(không quét mức nào) | P(PDH bị quét trước 03:00) | P(PDL bị quét trước 03:00) | P(PDH bị quét trước 09:00) | P(PDL bị quét trước 09:00) |
|---|---|---|---|---|---|---|---|---|---|
| Thứ 2 | 381 | 53.5% [48.5–58.5] | 41.5% [36.6–46.5] | 13% | 18% | 25% | 23% | 41% | 32% |
| Thứ 3 | 386 | 50.3% [45.3–55.2] | 47.7% [42.7–52.6] | 10% | 12% | 27% | 20% | 40% | 36% |
| Thứ 4 | 382 | 50.0% [45.0–55.0] | 49.0% [44.0–54.0] | 11% | 12% | 23% | 20% | 36% | 37% |
| Thứ 5 | 382 | 47.1% [42.2–52.1] | 53.1% [48.1–58.1] | 12% | 12% | 23% | 21% | 35% | 37% |
| Thứ 6 | 384 | 47.1% [42.2–52.1] | 46.6% [41.7–51.6] | 10% | 17% | 21% | 22% | 33% | 35% |
| Mọi ngày | 1913 | 49.7% [47.4–51.9] | 47.6% [45.4–49.9] | 11% | 14% | 24% | 21% | 37% | 36% |
| Ngẫu nhiên | 1938 | 50.8% | 49.5% | 9% | 9% |  |  |  |  |

Mức tuần trước, tính theo ngày nào trong tuần thực hiện việc quét:

| Ngày | n | P(quét PWH trong ngày này) | P(quét PWL trong ngày này) |
|---|---|---|---|
| Thứ 2 | 379 | 26.6% [22.4–31.3] | 19.3% [15.6–23.5] |
| Thứ 3 | 384 | 29.9% [25.6–34.7] | 24.2% [20.2–28.7] |
| Thứ 4 | 380 | 33.2% [28.6–38.0] | 30.0% [25.6–34.8] |
| Thứ 5 | 380 | 35.3% [30.6–40.2] | 34.5% [29.9–39.4] |
| Thứ 6 | 382 | 34.6% [30.0–39.5] | 36.1% [31.5–41.1] |
| Cả tuần | 384 | 51.8% [46.8–56.8] | 47.4% [42.5–52.4] |

Trong 384 tuần có mức tuần trước: quét cả PWH và PWL **12%**, chỉ một phía **76%**, không quét mức nào **12%**.


## 4. Weekly profile — cực trị tuần rơi vào ngày nào

Ma trận thô: ngày đặt đáy tuần (hàng) × ngày đặt đỉnh tuần (cột), % số tuần.

|  | Thứ 2 | Thứ 3 | Thứ 4 | Thứ 5 | Thứ 6 | Tổng |
|---|---|---|---|---|---|---|
| Thứ 2 | 0.5% (2) | 2.8% (11) | 5.7% (22) | 6.0% (23) | 12.2% (47) | 27.2% |
| Thứ 3 | 1.6% (6) | 0.0% (0) | 2.3% (9) | 4.9% (19) | 6.2% (24) | 15.0% |
| Thứ 4 | 4.1% (16) | 2.1% (8) | 1.3% (5) | 1.3% (5) | 3.6% (14) | 12.4% |
| Thứ 5 | 7.8% (30) | 4.9% (19) | 1.0% (4) | 0.3% (1) | 2.3% (9) | 16.3% |
| Thứ 6 | 12.4% (48) | 7.8% (30) | 5.4% (21) | 2.6% (10) | 0.8% (3) | 29.0% |
| Tổng | 26.4% | 17.6% | 15.8% | 15.0% | 25.1% | 100% |

Gộp thành 9 profile theo pha (đầu tuần = thứ 2–3, giữa tuần = thứ 4, cuối tuần = thứ 5–6):

| profile | n | Tỷ lệ | Ngẫu nhiên | Lệch so với ngẫu nhiên (điểm %) | Biên độ tuần (pip, trung vị) | Đóng cửa trong biên (%, trung vị) | P(đáy trước đỉnh) |
|---|---|---|---|---|---|---|---|
| đáy đầu tuần / đỉnh đầu tuần | 19 | 4.9% [3.2–7.6] | 5.2% | -0.2 [-3.3; +2.8] | 160 | 63 | 63% |
| đáy đầu tuần / đỉnh giữa tuần | 31 | 8.0% [5.7–11.2] | 6.4% | +1.6 [-2.1; +5.2] | 158 | 61 | 100% |
| đáy đầu tuần / đỉnh cuối tuần | 113 | 29.3% [25.0–34.0] | 33.0% | -3.7 [-10.2; +2.8] | 186 | 80 | 100% |
| đáy giữa tuần / đỉnh đầu tuần | 24 | 6.2% [4.2–9.1] | 7.7% | -1.5 [-5.1; +2.1] | 142 | 45 | 0% |
| đáy giữa tuần / đỉnh giữa tuần | 5 | 1.3% [0.6–3.0] | 0.3% | +1.0 [-0.2; +2.3] | 214 | 61 | 40% |
| đáy giữa tuần / đỉnh cuối tuần | 19 | 4.9% [3.2–7.6] | 5.9% | -1.0 [-4.2; +2.2] | 143 | 70 | 100% |
| đáy cuối tuần / đỉnh đầu tuần | 127 | 32.9% [28.4–37.7] | 32.0% | +0.9 [-5.7; +7.5] | 164 | 24 | 0% |
| đáy cuối tuần / đỉnh giữa tuần | 25 | 6.5% [4.4–9.4] | 5.9% | +0.5 [-2.8; +3.9] | 165 | 22 | 0% |
| đáy cuối tuần / đỉnh cuối tuần | 23 | 6.0% [4.0–8.8] | 3.6% | +2.4 [-0.7; +5.4] | 144 | 34 | 48% |

Tên gọi quen dùng của ICT cho các ô chính: *đáy đầu tuần / đỉnh cuối tuần* = tuần tăng kinh điển (classic buy week), *đỉnh đầu tuần / đáy cuối tuần* = tuần giảm kinh điển, *đáy giữa tuần / đỉnh cuối tuần* = đảo chiều thứ Tư, hai ô *đầu tuần / đầu tuần* và *giữa tuần / giữa tuần* = seek & destroy (cả hai cực trị in sớm rồi tuần đi ngang trong biên đó).


Ngày nào hay đặt cực trị tuần:

| Ngày | P(đặt đáy tuần) | P(đặt đỉnh tuần) | P(đặt một trong hai) | Ngẫu nhiên, đáy | Lệch so với ngẫu nhiên (điểm %) |
|---|---|---|---|---|---|
| Thứ 2 | 27.2% [23.0–31.8] | 26.4% [22.3–31.0] | 53.1% | 27.6% | -0.4 [-6.7; +5.9] |
| Thứ 3 | 15.0% [11.8–18.9] | 17.6% [14.1–21.7] | 32.6% | 17.0% | -2.0 [-7.2; +3.2] |
| Thứ 4 | 12.4% [9.5–16.1] | 15.8% [12.5–19.8] | 26.9% | 13.9% | -1.5 [-6.2; +3.3] |
| Thứ 5 | 16.3% [13.0–20.3] | 15.0% [11.8–18.9] | 31.1% | 17.5% | -1.2 [-6.5; +4.1] |
| Thứ 6 | 29.0% [24.7–33.7] | 25.1% [21.1–29.7] | 53.4% | 24.0% | +5.0 [-1.2; +11.3] |

## 5. Biên độ tuần hoàn thành tới đâu sau mỗi ngày

Cột *% biên tuần đã in* = (đỉnh cao nhất − đáy thấp nhất tính đến hết ngày đó) / biên độ cả tuần. Hai cột cuối là cái dùng được sáng thứ Ba và thứ Tư: xác suất cực trị tuần **vẫn còn ở phía trước**.

| Hết ngày | n | % biên tuần đã in (trung vị) | % biên tuần đã in (Q1–Q3) | P(đỉnh tuần chưa in) | P(đáy tuần chưa in) | P(cả hai đã in) |
|---|---|---|---|---|---|---|
| Thứ 2 | 386 | 40% | 30–57% | 73.6% [69.0–77.7] | 72.8% [68.2–77.0] | 1% |
| Thứ 3 | 386 | 62% | 47–76% | 56.0% [51.0–60.8] | 57.8% [52.8–62.6] | 5% |
| Thứ 4 | 386 | 79% | 64–96% | 40.2% [35.4–45.1] | 45.3% [40.4–50.3] | 20% |
| Thứ 5 | 386 | 98% | 85–100% | 25.1% [21.1–29.7] | 29.0% [24.7–33.7] | 47% |
| Thứ 6 | 386 | 100% | 100–100% | 0.0% [0.0–1.0] | 0.0% [0.0–1.0] | 100% |

## 6. Thông tin đầu tuần có dự báo được profile tuần không

Kiểm định thẳng: nếu biết nến thứ Hai (hướng đóng cửa, biên độ so với ATR20, vị trí đóng cửa trong biên), có đoán được tuần sẽ là tuần tăng kinh điển hay giảm kinh điển không. *Tuần tăng* ở đây = đáy tuần in trước đỉnh tuần; đó là biến nhị phân duy nhất đáng đoán vì nó quyết định chiều của chân giãn.

| Điều kiện | n | P(đáy tuần trước đỉnh tuần) | Lệch so với tỷ lệ gốc (điểm %) |
|---|---|---|---|
| Không điều kiện (tỷ lệ gốc) | 386 | 48.7% [43.8–53.7] |  |
| Thứ Hai đóng cửa tăng | 239 | 50.6% [44.3–56.9] | +1.9 [-6.1; +10.0] |
| Thứ Hai đóng cửa giảm | 142 | 44.4% [36.4–52.6] | -4.3 [-13.9; +5.2] |
| Thứ Hai biên hẹp (< 0,7 ATR20) | 110 | 39.1% [30.5–48.4] | -9.6 [-20.0; +0.8] |
| Thứ Hai biên rộng (> 1,3 ATR20) | 51 | 56.9% [43.3–69.5] | +8.2 [-6.3; +22.6] |
| Thứ Hai đóng ở 1/3 trên biên ngày | 150 | 52.7% [44.7–60.5] | +4.0 [-5.5; +13.4] |
| Thứ Hai đóng ở 1/3 dưới biên ngày | 124 | 43.5% [35.1–52.3] | -5.2 [-15.2; +4.9] |
| Đáy tuần đã in trong thứ Hai | 105 | 99.0% [94.8–99.8] | +50.3 [+45.0; +55.7] * |
| Đỉnh tuần đã in trong thứ Hai | 102 | 1.0% [0.2–5.3] | -47.7 [-53.1; -42.4] * |

Hai dòng cuối gần như hiển nhiên (nếu đáy tuần nằm ở thứ Hai thì nó đi trước đỉnh tuần, trừ khi đỉnh cũng ở thứ Hai); chúng ở đây để thấy *mức* thông tin mà việc biết một cực trị đã in mang lại, so với việc đọc hình dạng nến thứ Hai — bốn dòng giữa đều không ra khỏi nhiễu.


Biên thứ Hai có giữ được cả tuần không — đây là câu hỏi dùng được sáng thứ Ba:

| Tập tuần | n | P(đáy thứ Hai là đáy tuần) | Ngẫu nhiên | P(đỉnh thứ Hai là đỉnh tuần) | Ngẫu nhiên  | P(biên thứ Hai bị phá cả hai phía) | Ngẫu nhiên   | Lệch cột cuối (điểm %) |
|---|---|---|---|---|---|---|---|---|
| Mọi tuần | 386 | 27.2% [23.0–31.8] | 28% | 26.4% [22.3–31.0] | 26% | 46.9% [42.0–51.9] | 47% | +0.2 [-6.8; +7.3] |
| Thứ Hai đóng cửa tăng | 239 | 34.7% [29.0–41.0] | 41% | 18.0% [13.6–23.4] | 13% | 47.7% [41.5–54.0] | 47% | +1.1 [-8.2; +10.5] |
| Thứ Hai đóng cửa giảm | 142 | 15.5% [10.5–22.3] | 13% | 41.5% [33.8–49.8] | 41% | 43.7% [35.8–51.9] | 46% | -2.8 [-13.7; +8.1] |
| Thứ Hai biên hẹp (< 0,7 ATR20) | 110 | 10.0% [5.7–17.0] | 17% | 26.4% [19.0–35.3] | 23% | 63.6% [54.3–72.0] | 60% | +3.2 [-13.3; +19.7] |
| Thứ Hai biên rộng (> 1,3 ATR20) | 51 | 45.1% [32.3–58.6] | 36% | 31.4% [20.3–45.0] | 36% | 25.5% [15.5–38.9] | 30% | -4.7 [-21.9; +12.5] |

Cùng kiểu kiểm định ở mức ngày: biết trạng thái lúc 03:00 New York, có đoán được đáy ngày đã in chưa.

| Điều kiện tại 03:00 | n | P(đáy ngày in trước 09:00) | Lệch (điểm %) |
|---|---|---|---|
| Không điều kiện (tỷ lệ gốc) | 1915 | 51.7% [49.5–54.0] |  |
| Đáy chạy tới 03:00 nằm ở khối Á | 1425 | 53.1% [50.5–55.7] | +1.4 [-2.1; +4.8] |
| Đáy chạy tới 03:00 nằm ở khối Luân Đôn | 490 | 47.8% [43.4–52.2] | -4.0 [-9.0; +1.0] |
| Giá tại 03:00 trên mở 00:00 | 953 | 55.3% [52.1–58.4] | +3.5 [-0.3; +7.4] |
| Giá tại 03:00 dưới mở 00:00 | 953 | 48.0% [44.8–51.1] | -3.8 [-7.7; +0.1] |
| Đã quét đáy ngày hôm trước | 409 | 54.8% [49.9–59.5] | +3.0 [-2.3; +8.3] |
| Đã quét đỉnh ngày hôm trước | 453 | 55.2% [50.6–59.7] | +3.4 [-1.7; +8.5] |
| Biên tới 03:00 < 0,4 ATR20 | 1222 | 48.5% [45.7–51.3] | -3.2 [-6.8; +0.4] |

Hướng đi có nối tiếp không — kiểm định trực tiếp cái mà "phác thảo hướng" cần. Mốc quy chiếu trong ngày là giá mở 00:00 New York (true day open), trong tuần là giá mở tuần.

| Kiểm định | n | P(đóng cửa cùng phía) | Ngẫu nhiên | Lệch (điểm %) |
|---|---|---|---|---|
| Giá tại 03:00 trên mở 00:00 | 953 | 58.8% [55.6–61.8] | 64.0% | -5.3 [-9.6; -0.9] * |
| Giá tại 03:00 dưới mở 00:00 | 953 | 58.1% [55.0–61.2] | 62.1% | -3.9 [-8.3; +0.5] |
| Giá tại 09:00 trên mở 00:00 | 953 | 74.4% [71.5–77.1] | 75.5% | -1.1 [-5.0; +2.7] |
| Giá tại 09:00 dưới mở 00:00 | 957 | 73.5% [70.6–76.2] | 74.3% | -0.9 [-4.8; +3.1] |
| Thứ Hai đóng cửa tăng → tuần đóng cửa cùng phía | 239 | 58.2% [51.8–64.2] | 65.2% | -7.0 [-16.1; +2.0] |
| Thứ Hai đóng cửa giảm → tuần đóng cửa cùng phía | 142 | 59.9% [51.6–67.6] | 62.8% | -3.0 [-13.7; +7.7] |

## 7. Phân bổ — setup PO3 theo trạng thái profile biết được lúc vào lệnh

Bộ quy tắc **v1.0** (quét biên giờ trước trong 30 phút, độ sâu quét < 0,25 ATR, CISD trước phút 30, SL = cực trị + 0,25 ATR, TP = 2R, thoát sau 60 phút, phí 1 pip khứ hồi). **Không** áp điều kiện FVG của v1.1 — điều kiện đó cố ý không đo trên dữ liệu cũ. n = 795 setup trên 2 cặp. Mọi cột phân nhóm đều tính từ thông tin có tại lúc nến CISD đóng, không nhìn trước.


Risk mỗi lệnh (khoảng cách vào lệnh → SL) tính bằng pip, theo giờ — để đối chiếu với biên độ còn lại ở mục 2:

| Giờ | n | Risk Q1 (pip) | Risk trung vị (pip) | Risk Q3 (pip) | Khoảng cách tới TP 2R, trung vị (pip) |
|---|---|---|---|---|---|
| 03:00 | 473 | 6 | 7 | 9 | 15 |
| 09:00 | 322 | 6 | 8 | 10 | 16 |

**Ngày trong tuần**

| Ngày trong tuần | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| Thứ 3 | 259 | 22.8% [18.1–28.3] | 47.1% | -0.055 [-0.206; +0.096] |
| Thứ 4 | 259 | 21.2% [16.7–26.6] | 45.9% | -0.012 [-0.163; +0.139] |
| Thứ 5 | 277 | 18.8% [14.6–23.8] | 53.4% | -0.198 [-0.339; -0.057] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Giờ**

| Giờ | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| 03:00 | 473 | 16.5% [13.4–20.1] | 48.0% | -0.131 [-0.237; -0.026] |
| 09:00 | 322 | 27.3% [22.8–32.4] | 50.3% | -0.032 [-0.174; +0.111] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Hướng**

| Hướng | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| bán | 399 | 20.3% [16.6–24.5] | 49.1% | -0.105 [-0.224; +0.015] |
| mua | 396 | 21.5% [17.7–25.8] | 48.7% | -0.077 [-0.198; +0.045] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Trạng thái biên tuần**

| Trạng thái biên tuần | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| còn ≥ 2R khoảng trống tới biên tuần đối diện | 575 | 21.6% [18.4–25.1] | 48.9% | -0.082 [-0.183; +0.018] |
| quét biên tuần cùng phía | 113 | 20.4% [14.0–28.7] | 49.6% | -0.066 [-0.295; +0.163] |
| sát biên tuần đối diện | 103 | 17.5% [11.3–25.9] | 48.5% | -0.177 [-0.400; +0.046] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Khối đặt cực trị ngày cùng phía**

| Khối đặt cực trị ngày cùng phía | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| Luân Đôn | 252 | 23.8% [19.0–29.4] | 49.2% | -0.016 [-0.172; +0.140] |
| New York | 105 | 27.6% [20.0–36.8] | 50.5% | -0.042 [-0.292; +0.208] |
| Á | 438 | 17.6% [14.3–21.4] | 48.4% | -0.145 [-0.256; -0.035] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Vị trí so với mở 00:00**

| Vị trí so với mở 00:00 | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| dưới mở 00:00 | 413 | 20.1% [16.5–24.2] | 48.4% | -0.092 [-0.210; +0.025] |
| trên mở 00:00 | 382 | 21.7% [17.9–26.1] | 49.5% | -0.089 [-0.213; +0.035] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Vị trí trong biên ngày tới lúc đó**

| Vị trí trong biên ngày tới lúc đó | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| nửa dưới | 398 | 18.6% [15.1–22.7] | 49.2% | -0.136 [-0.254; -0.019] |
| nửa trên | 397 | 23.2% [19.3–27.6] | 48.6% | -0.045 [-0.169; +0.078] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

**Biên độ ngày**

| Biên độ ngày | n | P(TP) | P(SL) | Kỳ vọng R [CI95] |
|---|---|---|---|---|
| hẹp | 199 | 22.1% [16.9–28.4] | 47.2% | -0.017 [-0.192; +0.158] |
| rộng | 137 | 16.8% [11.5–23.9] | 53.3% | -0.229 [-0.426; -0.032] |
| trung bình | 459 | 21.6% [18.1–25.6] | 48.4% | -0.082 [-0.194; +0.030] |
| TẤT CẢ | 795 | 20.9% [18.2–23.8] | 48.9% | -0.091 [-0.176; -0.006] |

## 8. Hạn chế

- Mẫu ngày và tuần là histdata M1 từ 2023; chỉ hai cặp FX tương quan cao, nên n tuần hiệu dụng nhỏ hơn con số in ra. Hai cặp cùng một tuần không độc lập; khoảng tin cậy ở mục 4–6 vì thế **lạc quan**.
- Nhãn profile là hậu nghiệm. Chỉ mục 2, 3, 5, 6, 7 dùng được trong lúc giao dịch.
- Bước đi ngẫu nhiên không có phiên và không có ngày trong tuần, nên nó là mốc so cho *hình dạng* phân phối, không phải mô hình thị trường.
- Biên ngày 17:00→17:00 đã đối chiếu với feed H1 Dukascopy trên bốn ngày mẫu: lệch ≤ 0,6 pip ở đỉnh và 0,0 pip ở đáy, đúng 24 nến H1 mỗi ngày. Khoảng 12% số ngày có dưới 1300 nến M1 (ngày lễ, ngày nửa phiên) nhưng vẫn trên ngưỡng 900, nên cực trị của chúng có thể thiếu một phần cửa sổ.
- Mục 7 chia nhỏ cùng một tập setup thành nhiều nhóm; với n mỗi nhóm vài chục, chênh lệch kỳ vọng trong khoảng ±0,3 R là nhiễu. Không đổi quy tắc dựa trên một dòng của bảng đó.
