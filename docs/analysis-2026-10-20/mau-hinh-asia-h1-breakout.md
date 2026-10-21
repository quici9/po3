# Mẫu hình: Asia H1 breakout 00:00–05:00 → retrace 25% → 1 SD

Trạng thái: **đang backtest thủ công, chưa chốt** (ghi lại 2026-10-21; FVG M15 chỉ ghi nhận, không dùng để lọc). Không sửa định nghĩa trong lúc forward-test.

Tài liệu này chỉ ghi tỉ lệ xảy ra. Entry, SL, TP do người trade tự quyết, không tính ở đây.

## 1. Định nghĩa

Mọi mốc giờ là giờ New York (tự theo DST).

1. **Asia range**: High và Low từ 20:00 đến 00:00. Asia của thứ Hai là tối Chủ nhật.
2. **Breakout**: nến H1 đầu tiên **close** ra ngoài Asia, tính từ nến 00:00.
   - Nến này phải mở trong khoảng 00:00–05:00.
   - Nếu nến close ngoài đầu tiên mở lúc 06:00 trở đi thì bỏ ngày đó. Không lấy nến khác thay.
   - Close bằng đúng High hoặc Low của Asia thì chưa tính là close ngoài.
   - **FVG M15 chỉ ghi nhận, không lọc**: ghi lại nến H1 breakout có FVG M15 cùng hướng hay không (cả 3 nến M15 trong giờ đó, nến M15 1-2-3 hoặc 2-3-4; phá lên: Low nến 3 > High nến 1, phá xuống: High nến 3 < Low nến 1; không đặt độ rộng tối thiểu). Có hay không đều tính là breakout.
3. **Retrace 25%**: giá chạm mức cách cực trị nến breakout 25% chiều dài nến, trong khoảng từ lúc nến close đến trước 11:00.
   - Phá lên: mức = High nến − 25% × (High − Low).
   - Phá xuống: mức = Low nến + 25% × (High − Low).
4. **Điều kiện bỏ qua**: lúc chạm 25%, giá đã từng chạm 1 SD (tính từ lúc nến breakout mở). Gặp ở 9–15% số ngày chạm 25%.
5. **Target 1 SD**: mức Asia bị phá cộng thêm 1 lần độ rộng Asia (phá lên: Asia High + độ rộng; phá xuống: Asia Low − độ rộng).

Lệnh vào trước 11:00. Sau 11:00 để lệnh chạy tự do, nên thống kê đo tới 16:00.

## 2. Tỉ lệ (2023-01 đến 2026-09)

Ngẫu nhiên là cùng phép đo trên bước đi ngẫu nhiên có cùng độ biến động theo từng giờ. Đây là mức nền mà một mẫu hình không có thông tin gì cũng đạt được.

| bước | EURUSD | XAUUSD | NAS100 |
|---|---|---|---|
| Có breakout 00:00–05:00, trên mọi ngày | 88% | 76% | 85% |
| Chạm 25% trước 11:00, trên ngày breakout | 95% | 97% | 98% |
| Lúc chạm 25%, 1 SD chưa tới | 85% | 91% | 89% |
| **Sau đó tới 1 SD trước 16:00** | **65%** (ngẫu nhiên 64%) | **61%** (ngẫu nhiên 54%) | **74%** (ngẫu nhiên 72%) |
| Sau đó tới 1 SD trước 11:00 | 60% | 52% | 66% |
| Trọn chuỗi, trên mọi ngày | 47% | 41% | 55% |
| Số ngày đủ chuỗi mỗi tuần | 2,3 | 2,0 | 2,7 |
| Số tuần có ít nhất 1 lần | 95% | 95% | 99% |

- Phá lên và phá xuống cho tỉ lệ như nhau ở cả 3 symbol.
- Nến breakout 00–01 và 02–05 cho tỉ lệ như nhau.
- Khoảng 85–90% số ngày tới 1 SD thì tới trước 11:00.

### Nếu chỉ lấy ngày có FVG M15

Để so sánh khi forward-test: tỉ lệ khi chỉ giữ các ngày nến breakout có FVG M15.

| | EURUSD | XAUUSD | NAS100 |
|---|---|---|---|
| Nến breakout có FVG M15 (trên ngày breakout) | 51% (ngẫu nhiên 53%) | 57% (ngẫu nhiên 55%) | 57% (ngẫu nhiên 52%) |
| Sau khi chạm 25%, tới 1 SD trước 16:00: không lọc FVG | 65% | 61% | 74% |
| Như trên, có FVG M15 | 67% (ngẫu nhiên 66%) | 61% (ngẫu nhiên 53%) | 75% (ngẫu nhiên 74%) |
| Số ngày đủ chuỗi mỗi tuần: không lọc → có FVG | 2,3 → 1,1 | 2,0 → 1,1 | 2,7 → 1,5 |
| Tuần có ít nhất 1 lần, có FVG | 69% | 74% | 86% |

- Điều kiện FVG chỉ giữ lại khoảng một nửa số ngày breakout. Tỉ lệ có FVG gần bằng mức ngẫu nhiên, nên FVG M15 trong nến H1 breakout chủ yếu là hệ quả hình học của một nến H1 chạy một chiều.
- Tỉ lệ tới 1 SD gần như không đổi (chênh 0–2 điểm, nằm trong sai số). FVG không làm mẫu hình mạnh hơn mà chỉ giảm số ngày giao dịch đi một nửa.
- Với XAUUSD, mức chênh so với ngẫu nhiên vẫn giữ khoảng +8 điểm khi có FVG.
- Nếu bạn dùng FVG làm điểm vào lệnh (thay cho mức 25%) thì đó là câu hỏi khác, chưa đo.

## 3. XAUUSD: symbol duy nhất cao hơn ngẫu nhiên

EURUSD và NAS100 chỉ ngang mức ngẫu nhiên. Tỉ lệ cao của NAS100 là do biến động lớn, không phải do Asia range.

XAUUSD, tới 1 SD trước 16:00 sau khi chạm 25%:

| năm | thực tế | ngẫu nhiên | chênh |
|---|---|---|---|
| 2023 | 69% (n 102) | 64% | +5 |
| 2024 | 67% (n 182) | 57% | +10 |
| 2025 | 54% (n 171) | 48% | +6 |
| 2026 | 55% (n 108) | 49% | +6 |

- Tỉ lệ thô giảm từ 2025, nhưng mức ngẫu nhiên cùng năm cũng giảm theo. Mức chênh so với ngẫu nhiên vẫn giữ khoảng +6 điểm.
- Thứ Hai: 42%, ngẫu nhiên cũng 42%. Vì mức ngẫu nhiên thấp ngang nhau, thứ Hai thấp không phải do mẫu hình mất tác dụng, nhưng thứ Hai cũng không có ưu thế. Thứ Ba đến thứ Sáu: 62–68%, cao hơn ngẫu nhiên 7–10 điểm.
- Khoảng tin cậy mỗi năm rộng khoảng ±8–10 điểm. Mức chênh từng năm chưa chắc chắn, chỉ tổng 4 năm là rõ.

## 4. Rủi ro

1. Toàn bộ là số trong mẫu. Định nghĩa được chọn sau khi xem dữ liệu, nên số khi trade thật nhiều khả năng thấp hơn.
2. Đã thử nhiều biến thể (lọc nến thân dài, retrace 50%, quét một đầu rồi phá đầu kia, khung 06–10). Thử nhiều thì dễ có một biến thể đẹp do may mắn.
3. Giá feed khác nhau giữa các broker, nhất là NAS100 CFD. Asia range trên TradingView có thể lệch vài pip so với dữ liệu thống kê.

## 5. Forward-test

Giữ cố định 5 bước trên trong 2–3 tháng. Mỗi ngày ghi:

| cột | ghi gì |
|---|---|
| ngày, symbol | |
| giờ nến breakout | 00–05, hoặc "không có" |
| hướng | lên / xuống |
| có FVG M15 | có / không |
| chạm 25% trước 11:00 | có / không, giờ chạm |
| 1 SD đã tới trước khi chạm 25% | có / không |
| tới 1 SD trước 16:00 | có / không, giờ tới |

So với bảng ở mục 2. Với 40 ngày đủ điều kiện, khoảng tin cậy còn rộng khoảng ±15 điểm, nên chỉ phát hiện được sai lệch lớn. Cần khoảng 100 ngày trở lên mới phân biệt được 61% với mức ngẫu nhiên khoảng 50% của 2025–2026.

## 6. Indicator TradingView

File `Asia_H1_Breakout_v1.pine` ở thư mục gốc repo. Indicator chỉ làm bước 1 và 2:

- Tính Asia range nhưng không vẽ, vì đã có indicator khác vẽ.
- Đường dọc 00:00 (liền, bắt đầu) và 06:00 (đứt, kết thúc), từ thứ Hai đến thứ Sáu.
- Alert khi nến H1 đầu tiên close ngoài Asia, mở 00:00–05:00. Mỗi ngày tối đa 1 alert. Alert bắn cả khi có lẫn không có FVG M15, nội dung ghi rõ "CÓ FVG M15" (kèm vùng FVG) hoặc "KHÔNG có FVG M15".
- Label: "▲/▼ BO hh:00 FVG" màu đậm khi có FVG, "no FVG" màu nhạt khi không có.
- Không alert nếu nến close ngoài đầu tiên mở lúc 06:00 trở đi.
- Đánh dấu nến breakout ▲/▼ kèm giờ nến. Rê chuột lên nhãn để xem chi tiết.
- Chỉ vẽ đường dọc và nhãn của ngày giao dịch hiện tại (ngày của nến cuối chart; từ 18:00 NY tính sang ngày hôm sau). Ngày đã qua không hiển thị; sang ngày mới thì hình ngày cũ tự xóa. Cuối tuần vẫn thấy hình của thứ Sáu. Trong Bar Replay, "ngày hiện tại" là ngày đang replay. Alert không bị ảnh hưởng.
- Bar Replay: nhãn hiện đúng lúc nến H1 breakout close (đã thử trên OANDA:EURUSD H1 và M15). Alert không bắn trong replay.
- Nội dung alert có: giá close, mức Asia bị phá, có/không FVG M15 (vùng FVG và giờ nến M15 đầu tiên nếu có), High/Low nến breakout (để tự tính mức 25%), Asia range.
- Chỉ chạy trên H1 hoặc M15. Trên H1, nến M15 lấy bằng `request.security_lower_tf`. Trên M15, nến H1 được dựng lại từ nến chart.
- Trên M15, nếu thiếu nến M15 cuối giờ (không có tick), nến H1 được xét bù ở nến đầu giờ sau, và alert có chữ "(muộn)" ở đầu.

Cách dùng:

1. Thêm indicator vào chart H1 hoặc M15.
2. Tạo alert: Condition chọn indicator, chọn **Any alert() function call**. Mỗi symbol tạo 1 alert.
3. Sửa script hoặc đổi input thì phải xóa alert cũ và tạo lại.

Logic Pine được port từng nến sang `verify_breakout_indicator.py`. Kết quả đối chiếu trên H1 và M15 của cả 3 symbol: 0 ngày lệch so với thống kê (`verify_breakout_indicator.md`). Sửa một bên thì sửa cả bên kia.

## 7. File

| file | nội dung |
|---|---|
| `asia_h1_breakout.py` | tính toàn bộ tỉ lệ (không lọc và có FVG M15), sinh `asia-h1-breakout.md` và `asia-h1-breakout_days.csv` |
| `asia-h1-breakout.md` | bảng chi tiết: từng bước, khoảng tin cậy 95%, theo hướng, năm, giờ nến, thứ |
| `asia-h1-breakout_days.csv` | từng ngày: Asia High/Low, hướng, giờ nến breakout, có FVG M15, giờ chạm 25%, mức SD xa nhất; cột `p_*` không lọc, `f_*` có FVG |
| `verify_breakout_indicator.py` | port Pine từng nến, đối chiếu với file ngày |
| `verify_breakout_indicator.md` | kết quả đối chiếu |

Chạy lại: `python3 docs/analysis-2026-10-20/asia_h1_breakout.py . docs/analysis-2026-10-20`, rồi `verify_breakout_indicator.py` với cùng tham số.

Dữ liệu `data/m1/*_M1_UTC.csv` (histdata) bị lệch 1 giờ trong thời gian châu Âu dùng giờ mùa hè. Hai script tự sửa khi đọc. Các phân tích cũ trong repo dùng dữ liệu này chưa sửa.
