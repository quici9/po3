# Xác thực báo cáo "Phân Tích PO3 Nến H1" — Errata và định nghĩa vận hành

Ngày kiểm tra: 2026-09-17. Phạm vi: kiểm tra nguồn trích dẫn và tính nhất quán nội bộ của báo cáo gốc; đề xuất định nghĩa vận hành để bot thống kê đo lại các con số.

## 1. Kết luận tổng quan

- Phần **khái niệm** (PO3/AMD, chuỗi OLHC/OHLC, Premium/Discount so với giá mở cửa, Killzone London 02:00–05:00 NY, Silver Bullet 10:00–11:00 NY) đúng với tài liệu ICT phổ biến.
- Phần **số liệu định lượng** (71,3%, 46,8%, ma trận xác suất AMD, tỷ lệ profile theo phiên, 97,75% trên 3.245 nến) **không có nguồn kiểm chứng được**. Các nguồn được gắn (Reddit "MACRO", Scribd PDF, video YouTube) là bài thảo luận/tài liệu tổng quan, không phải nghiên cứu có dữ liệu. Tìm kiếm web không tìm thấy các con số này ở bất kỳ đâu. Cần xem chúng là **giả thuyết để bot đo lại**, không phải sự thật.
- Có **3 lỗi khái niệm** cần sửa: (a) "True H1 Open tại xx:15" không tồn tại trong Quarterly Theory; (b) "ICT Macro xx:50–xx:10 mỗi giờ" là khái quát sai; (c) quy đổi giờ EST sang GMT+7 sai 1 giờ trong mùa DST.
- Báo cáo dùng **3 cách chia thời gian trong giờ khác nhau** và mâu thuẫn nhau.

## 2. Bảng xác thực từng luận điểm

| # | Luận điểm trong báo cáo | Nguồn gắn | Kết quả kiểm tra | Hành động |
|---|---|---|---|---|
| 1 | 97,75% trong 3.245 nến (10 năm) có râu ngược chiều | [5] video YouTube tiếng Pháp "98% de Probabilité", đăng 26/04/2026 | Là video của một trader, không phải khảo sát công bố. Con số gần như **hiển nhiên**: nến nào có Open khác cực trị đều có râu ngược chiều, nên ~98% không mang lợi thế thống kê nào. | Bỏ hoặc ghi rõ "trivial, không có edge". |
| 2 | Phân bố phút tạo cực trị thao túng: 24,5% / 46,8% / 18,2% / 10,5%; tổng 71,3% trong 25 phút đầu; đỉnh 64% ở phút 11–25 | [10] Reddit r/InnerCircleTraders "MACRO" | Là bài thảo luận, không có dữ liệu. Không tìm thấy con số nào trên web. Bốn số cộng đúng 100% và 24,5+46,8=71,3 cho thấy được sinh ra để khớp nhau. | Đánh dấu **CHƯA KIỂM CHỨNG**. Đây là giả thuyết H1 để bot đo. |
| 3 | Ma trận xác suất AMD theo 4 cửa sổ (68/22/8/2, 18/64/15/3, 7/11/74/8, 7/3/18/72) | [1][2][10][11] bài tổng quan PO3 | Không nguồn nào chứa ma trận này. Ngoài ra "xác suất pha" không có định nghĩa đo lường (làm sao đo "68% tích lũy"?). | Đánh dấu CHƯA KIỂM CHỨNG. Thay bằng chỉ số đo được (xem mục 4). |
| 4 | Tỷ lệ profile theo phiên: Á 60/25/15, London 50/35/15, NY 40/40/20 | [6][7] Scribd PDF | Không kiểm chứng được; không có định nghĩa phân loại kèm theo nên không thể tái lập. | Đánh dấu CHƯA KIỂM CHỨNG. Giả thuyết H2. |
| 5 | Z-Swing: ~50% đảo tại Fib ext 1.0; 82% trong 1.0–2.0; >2.5 thì <15% | [11] Reddit "PO3 Z Swing Studies" | Bài viết tồn tại (có trong danh mục nguồn) nhưng không truy cập được để kiểm tra mẫu/phương pháp. Có một trích dẫn hỏng "([])" trong văn bản. | Ghi "nghiên cứu cộng đồng, cỡ mẫu không rõ". Sửa trích dẫn hỏng. |
| 6 | "True H1 Open" = giá mở nến M15 thứ hai (xx:15), theo Quarterly Theory | [13] quartersequence.com, [22] oracleinsights.io | **Sai.** Cả hai nguồn đều định nghĩa chu kỳ nội ngày là **90 phút**, True Open tại +22,5 phút (hoặc Q2 của 90 phút). **Không nguồn nào định nghĩa True Open cho chu kỳ 60 phút.** Việc chia H1 thành 4×M15 là suy diễn tương tự, không phải lý thuyết gốc. | Sửa thành "giả thuyết mở rộng; cần đo so sánh mốc xx:15 với mốc True Open 90 phút chuẩn". |
| 7 | ICT Macro diễn ra cố định mỗi giờ tại xx:50–xx:10 | [15] LuxAlgo | **Sai.** Nguồn liệt kê các cửa sổ cụ thể: 8:50–9:10, 9:50–10:10, 10:50–11:10, 11:50–12:10, 13:10–13:40, 15:15–15:45 (NY) và London 2:33–3:00, 4:03–4:30. Không phải mọi giờ, và các macro London không nằm ở :50–:10. | Sửa: "một số macro NY trùng biên giờ; không khái quát cho mọi giờ". |
| 8 | Nghiên cứu vi cấu trúc xác nhận bùng nổ khối lượng tại biên giờ | [25] arXiv 2607.09426 (Kim & Hansen, "The Quarter-Hour Effect") | Bài có thật. Phạm vi: **6 hợp đồng perpetual trên Binance (crypto)**; bùng nổ tại mốc 1 phút, 5 phút, 15 phút. Hỗ trợ hiện tượng chu kỳ theo đồng hồ nhưng **không** kiểm chứng PO3 và **không** áp dụng trực tiếp cho FX/chỉ số. | Thu hẹp phạm vi phát biểu. |
| 9 | Quy đổi giờ: London 02:00–05:00 EST = 14:00–17:00 GMT+7; NY 08:00–11:00 EST = 20:00–23:00 GMT+7 | [6][13] | Chỉ đúng mùa đông (EST = UTC−5). Mùa DST (tháng 3–11, EDT = UTC−4) sớm hơn 1 giờ: London 13:00–16:00, NY 19:00–22:00 giờ VN. Hôm nay (09/2026) đang là EDT. | Sửa: ghi giờ theo múi America/New_York, bot phải dùng tz database, không cộng offset cố định. |
| 10 | Chia thời gian trong giờ | nội bộ báo cáo | Mâu thuẫn: bảng 4 Quý dùng 00–15/15–30/30–45/45–60; ma trận dùng 00–10/11–25/26–45/46–60; profile Classic Expansion dùng 00–15/15–25/25–50/50–60. | Bot đo theo phút (bin 5 phút) và để dữ liệu quyết định ranh giới. |
| 11 | Phiên Á 18:00–00:00 EST | [13] | ICT thường dùng 19:00 hoặc 20:00–00:00 NY. Khác biệt nhỏ. | Chọn một định nghĩa và cố định trong bot. |
| 12 | OLHC cho nến tăng / OHLC cho nến giảm; Premium/Discount so với Open | [1][2] | Đúng với ICT. | Giữ. |
| 13 | London KZ 02:00–05:00 NY; Silver Bullet 10:00–11:00 NY; tin 08:30/10:00 NY | [6][15] | Đúng. | Giữ. |

## 3. Tại sao các con số phải được đo lại

Báo cáo không nêu: công cụ, cỡ mẫu, thời kỳ, cách xác định "nến định hướng", cách xác định "phút tạo cực trị". Không có các định nghĩa này thì mọi tỷ lệ phần trăm đều không thể tái lập và không thể so sánh giữa các tuần. Bot của bạn cần cố định định nghĩa trước rồi mới đo; sau khi đo, thay toàn bộ số liệu trong báo cáo gốc bằng số đo thật kèm cỡ mẫu và khoảng tin cậy.

## 4. Định nghĩa vận hành đề xuất cho bot

### 4.1. Dữ liệu và thời gian
- Nguồn tối thiểu: nến **M1** OHLC (để biết phút tạo cực trị). Nến H1 **tự dựng từ M1** để biên nến nhất quán với dữ liệu phút.
- Lưu timestamp UTC. Gán phiên/giờ theo **America/New_York** (tz database, tự xử lý DST). Chỉ số "phút trong giờ" không phụ thuộc múi giờ (mọi múi giờ liên quan đều lệch nguyên giờ), nhưng nhãn phiên thì có.
- Phiên (giờ NY): Á 19:00–00:00; London 02:00–05:00 (Killzone) hoặc 02:00–08:00 (mở rộng); NY AM 08:00–11:00; NY PM 13:00–16:00. Giờ ngoài các phiên gắn nhãn "khác", không bỏ.
- Mỗi cặp/tài sản thống kê riêng, không gộp.
- Gắn thẻ nến đặc biệt: nến chứa tin hạng nhất (lịch kinh tế tĩnh: NFP, CPI, FOMC, PPI...), giờ đầu sau mở cửa cuối tuần, ngày lễ. Thống kê có/không có các nến này.

### 4.2. Nến H1 và cực trị thao túng
- Hướng: tăng nếu Close > Open; giảm nếu Close < Open. Tỷ lệ thân r = |C−O| / (H−L).
- "Nến định hướng": r ≥ 0,5 (ngưỡng cố định, ghi rõ trong báo cáo).
- Cực trị thao túng: nến tăng → **Low**; nến giảm → **High**. Phút tạo cực trị = phút M1 đầu tiên chạm mức đó (0–59).
- Có thao túng thật hay không: râu phía Open ≥ 5% biên độ nến (dưới ngưỡng này coi là "không có pha M", tức Trend Runaway).
- Chuỗi hợp lệ PO3: nến tăng phải có Low **trước** High (OLHC); nến giảm có High trước Low (OHLC). Ghi tỷ lệ hợp lệ.
- Kiểm định giả thuyết True Open: đo song song P(Low < Open giờ) và P(Low < Open nến M15 lúc xx:15) cho nến tăng; so với mốc True Open 90 phút chuẩn.

### 4.3. Phân loại profile nến H1 (loại trừ lẫn nhau, xét theo thứ tự)
1. **News/Outlier**: biên độ ≥ 2,5 × ATR(H1, 24) hoặc trùng lịch tin hạng nhất.
2. **Trend Runaway**: r ≥ 0,75 và râu phía Open < 5%.
3. **Classic Expansion**: biên độ ≥ 0,8 × ATR; r ≥ 0,65; râu phía Open 5–30%; râu phía Close ≤ 15%; chuỗi OLHC/OHLC hợp lệ.
4. **Consolidation Reversal**: r < 0,4 và một râu ≥ 50% biên độ.
5. **Seek & Destroy**: r < 0,3 và cả hai râu ≥ 25%.
6. **Khác**: phần còn lại.

Ngưỡng được hiệu chỉnh một lần trên dữ liệu nền rồi **đóng băng**; đổi ngưỡng giữa chừng sẽ làm các tuần không so sánh được với nhau.

### 4.4. Ba thống kê mục tiêu
- **Phân bố phút tạo cực trị thao túng** theo phiên: histogram bin 5 phút và **đường tích lũy (CDF)** "đến phút m, X% nến đã in xong cực trị". CDF là thứ dùng được lúc giao dịch trực tiếp.
- **Giờ động lượng cao nhất**: theo từng giờ trong ngày (giờ NY): P(Classic Expansion), trung bình thân/ATR, trung bình biên độ/ATR, kèm khoảng tin cậy Wilson và n.
- **Ngày phân phối trong tuần**: tuần = từ mở cửa Chủ nhật 18:00 NY đến đóng cửa Thứ Sáu. Hướng tuần = Close so với Open tuần. Đo ba thứ: ngày tạo cực trị ngược hướng (ngày thao túng), ngày tạo cực trị thuận hướng (ngày kết thúc phân phối), ngày có thân thuận hướng lớn nhất (ngày phân phối chính). Kèm biên độ trung bình theo thứ.

### 4.5. Cỡ mẫu và phát hiện dịch chuyển
- Một tuần chỉ có 5 nến cho mỗi giờ-trong-ngày và 15–30 nến cho mỗi phiên. Không thể ước lượng xác suất theo tuần đơn lẻ.
- Bot chạy hàng tuần nhưng báo cáo theo cửa sổ trượt 4 tuần / 13 tuần / 52 tuần, so với nền nhiều năm (tối thiểu 2 năm dữ liệu trước khi tin số liệu).
- Dịch chuyển phân bố: so sánh histogram 4 tuần với nền 52 tuần bằng Jensen–Shannon divergence hoặc chi-square; báo cáo trung vị phút và tỷ lệ "≤ 25 phút" kèm khoảng tin cậy; chỉ cảnh báo khi khoảng tin cậy 4 tuần không chứa giá trị nền. Theo dõi dạng CUSUM qua nhiều tuần thay vì phản ứng theo từng tuần.
- Thống kê ngày trong tuần: mỗi năm chỉ ~50 mẫu cho mỗi thứ; cần 2–3 năm.

## 5. Việc đầu tiên bot nên làm
Chạy trên dữ liệu nền để đo lại bốn giả thuyết của báo cáo: (H1) 71,3% cực trị trong 25 phút đầu; (H2) tỷ lệ profile theo phiên; (H3) London/NY có tỷ lệ Classic Expansion cao nhất tại giờ nào; (H4) Thứ nào là ngày phân phối. Kết quả đo thật thay thế toàn bộ số liệu trong báo cáo gốc.

## 6. Kết quả đo thực tế (cập nhật 2026-09-17)

Dữ liệu: histdata.com M1 (EST cố định, đã quy về UTC), 2023-01 → 2026-09-11, 4 tài sản: EURUSD, GBPUSD, XAUUSD, NSXUSD (Nasdaq 100 CFD). Đối chiếu bằng Dukascopy M1 cho EURUSD (2023-09 → 2026-09): kết quả trùng khớp trong 0,3 điểm phần trăm. Script: `po3_stats.py`; báo cáo chi tiết từng tài sản trong `reports/`. Định nghĩa như mục 4. Mỗi tài sản ~20.000–22.000 nến H1, ~193 tuần.

### 6.1. H1 — Phút tạo cực trị thao túng (nến định hướng r ≥ 0,5, râu phía Open ≥ 5%)

| Nguồn | 00–10 | 11–25 | 26–40 | 41–59 | ≤ 25 phút | Trung vị phút |
|---|---|---|---|---|---|---|
| **Báo cáo gốc** | 24,5% | 46,8% | 18,2% | 10,5% | 71,3% | — |
| EURUSD (n=6.787) | 68,2% | 20,6% | 8,7% | 2,4% | 88,8% | 5 |
| GBPUSD (n=6.828) | 69,1% | 19,7% | 8,5% | 2,7% | 88,8% | 4 |
| XAUUSD (n=6.641) | 68,6% | 20,0% | 9,3% | 2,0% | 88,7% | 5 |
| NSXUSD (n=6.525) | 66,5% | 21,0% | 10,2% | 2,3% | 87,5% | 5 |
| Random walk (cùng bộ lọc) | 56,6% | 28,3% | 11,7% | 3,4% | 84,9% | 8 |

Kết luận: **giả thuyết "đỉnh thao túng ở phút 11–25" bị bác bỏ** trên cả 4 tài sản. Cực trị ngược hướng dồn vào 10 phút đầu, và dồn mạnh hơn cả bước ngẫu nhiên. Trong số nến định hướng có râu thao túng ≥ 5%, khoảng 21% có cực trị ngay phút 0 (Open chính là cực trị hoặc chạm trong phút đầu) so với 7,8% ở random walk; tính trên toàn bộ nến định hướng (kể cả 30% nến không có râu phía Open) con số là 39%: đây là dấu hiệu quán tính xuyên biên giờ, không phải "Judas swing". Với ngưỡng râu nghiêm hơn (≥ 15%), EURUSD cho 56,1 / 28,2 / 12,2 / 3,5% (random walk 44,4 / 35,6 / 15,7 / 4,3%): kết luận không đổi.

Ngoại lệ đáng chú ý: NSXUSD phiên NY AM có 24,9% cực trị rơi vào phút 26–40 và chỉ 72% trong 25 phút đầu (trung vị phút 10), do tin 08:30/10:00 và mở cửa 09:30 NY. Đây là phiên duy nhất mà cửa sổ 26–40 có ý nghĩa.

Kiểm định mốc "True Open xx:15" (EURUSD): chỉ 15,8% nến tăng (20,0% nến giảm) có cực trị hình thành sau phút 15 và vượt qua Open xx:15. Kịch bản "quét True Open trong Q2" là thiểu số.

Chuỗi OLHC/OHLC hợp lệ 97–98%: gần như hiển nhiên với nến định hướng, không phải bằng chứng cho PO3.

### 6.2. H2 — Tỷ lệ profile theo phiên (EURUSD; các tài sản khác tương tự trong ±3 điểm)

| Phiên | ClassicExp | ConsolRev | News/Outlier | Seek&Destroy | TrendRunaway | Khác |
|---|---|---|---|---|---|---|
| Á | 4,8% | 30,2% | 0,7% | 6,4% | 8,4% | 49,5% |
| London | 10,2% | 28,6% | 3,4% | 7,1% | 6,7% | 43,9% |
| NY AM | 8,8% | 28,3% | 14,1% | 5,5% | 5,4% | 37,9% |
| NY PM | 7,8% | 29,6% | 2,2% | 6,2% | 7,4% | 46,8% |

Kết luận: các tỷ lệ trong báo cáo (Á S&D 60%, London ClassicExp 50%, NY ClassicExp 40%) **không đúng** với định nghĩa hình thái ở mục 4.3. Classic Expansion theo định nghĩa chặt chỉ chiếm 5–10% ở mọi phiên. Phiên Á không bị Seek & Destroy chi phối (6–7%). Điểm khác biệt thật giữa các phiên nằm ở tỷ lệ News/Outlier (NY AM 12–16%) và ở độ lớn thân nến, không phải ở hình dạng nến.

### 6.3. H3 — Giờ có động lượng cao nhất (giờ New York, thân nến / ATR24 và P(mở rộng: r ≥ 0,65 và biên độ ≥ 0,8 ATR))

| Giờ NY | EURUSD | GBPUSD | XAUUSD | NSXUSD |
|---|---|---|---|---|
| 03:00 | 0,63 / 24,6% | 0,71 / 26,6% | 0,51 / 19,4% | — |
| 04:00 | 0,72 / 27,9% | 0,72 / 27,4% | 0,50 / 20,9% | — |
| 08:00 | 0,75 / 26,0% | 0,74 / 25,9% | 0,64 / 23,1% | 0,54 / 20,6% |
| 09:00 | **0,96 / 26,6%** | **0,88 / 26,1%** | **0,89 / 26,9%** | 0,88 / 27,2% |
| 10:00 | 0,84 / 24,3% | 0,81 / 25,3% | 0,85 / 23,0% | **1,06 / 27,1%** |
| 11:00 | 0,84 / 26,9% | 0,82 / 26,0% | 0,77 / 24,8% | 0,98 / 30,9% |
| 12:00 | 0,59 / 24,2% | 0,62 / 26,5% | 0,55 / 21,7% | 0,70 / 26,9% |
| 17:00–18:00 | 0,23–0,26 / 3–4% | tương tự | tương tự | tương tự |

Kết luận: với FX và vàng, **09:00 NY** là giờ động lượng cao nhất, kế đến 10:00 và 11:00; London mạnh nhất tại 04:00 NY (FX) và yếu với vàng. Với Nasdaq, **10:00 và 11:00 NY** dẫn đầu. Silver Bullet 10:00–11:00 của báo cáo đúng với Nasdaq, còn với FX thì 09:00 mạnh hơn. Giờ 17:00–18:00 NY (rollover) gần như không có mở rộng.

### 6.4. H4 — Ngày trong tuần (193 tuần mỗi tài sản)

| Thứ | Ngày thao túng (cực trị ngược hướng tuần) EUR/GBP/XAU/NSX | Ngày phân phối chính (thân thuận hướng lớn nhất) EUR/GBP/XAU/NSX | Random walk: thao túng / phân phối chính | Biên độ ngày / TB (EURUSD) |
|---|---|---|---|---|
| Mon | 52 / 50 / 59 / 48% | 16 / 14 / 19 / 15% | 55,9% / 20% | 0,93 |
| Tue | 24 / 24 / 17 / 20% | 20 / 19 / 22 / 19% | 19,5% / 20% | 0,98 |
| Wed | 12 / 14 / 14 / 21% | 22 / 24 / 18 / 24% | 12,6% / 20% | 1,05 |
| Thu | 8 / 6 / 8 / 7% | **29 / 27 / 19 / 25%** | 8,2% / 20% | 1,07 |
| Fri | 4 / 6 / 4 / 4% | 14 / 16 / 23 / 18% | 3,8% / 20% | 0,97 |

Kết luận: "Thứ Hai là ngày thao túng" (≈50%) **trùng với random walk (55,9%)** nên không mang thông tin; đó là hệ quả cơ học của việc tuần đóng cửa có hướng. Thông tin thật nằm ở cột phân phối chính: **Thứ Năm** (và Thứ Tư) cao hơn mức nền 20% với FX và Nasdaq (EURUSD 29%, CI 23–36%), Thứ Hai và Thứ Sáu thấp hơn nền (14–16%). Vàng gần như phẳng. Biên độ ngày lớn nhất vào Thứ Năm, nhỏ nhất Thứ Hai.

### 6.5. Hệ quả cho bot hàng tuần
- Chỉ số theo dõi dịch chuyển trong giờ nên là **CDF theo phiên** (ví dụ EURUSD London: ≤5' 50%, ≤10' 64%, ≤15' 75%, ≤25' 87%) so với cửa sổ 4 tuần gần nhất; và **tỷ lệ cực trị tại phút 0** như chỉ báo quán tính xuyên giờ.
- Mọi so sánh phải kèm mốc random walk; nếu không, phần lớn "mẫu hình" chỉ là cơ học của việc điều kiện hóa theo hướng nến.
- NY AM của chỉ số Mỹ cần tách riêng vì phân bố khác hẳn (đỉnh phụ ở 26–40 phút).


## 7. Chứng thực riêng cho FX (cập nhật 2026-09-17)

Theo yêu cầu phạm vi chỉ FX, bản chứng thực độc lập trên ba cặp chính thuộc ba họ tiền khác nhau (EURUSD, GBPUSD, USDJPY; histdata M1 2023-01 → 2026-09, đối chiếu Dukascopy cho EURUSD và GBPUSD) nằm trong `reports/FX_chung_thuc.md` và bản `.docx` cùng tên. Bản này kiểm tra độ bền của kết luận theo: từng cặp và gộp, hai ngưỡng râu (5% và 15%), từng năm 2023–2026, từng phiên, có và không có giờ chứa tin NY, hai nguồn dữ liệu, và mốc random walk. Vàng và chỉ số không được dùng cho kết luận FX.
