# Kết luận: win rate và R:R khi vào lệnh tại giá đóng nến CISD (2026-10-08)

Câu hỏi: vào lệnh thị trường ngay khi nến M1 CISD đóng cửa (nến đóng mới tính là xác nhận) thì xác suất thắng ứng với từng mức R:R là bao nhiêu, và có kỳ vọng dương không.

Phạm vi: nến H1 03:00 và 09:00 New York, thứ Ba–Năm, EURUSD và GBPUSD. Setup phát hiện bằng đúng máy trạng thái của `../analysis-2026-09-21/verify_indicator.py` (cùng logic indicator v7), không nhìn trước. Hai bộ quy tắc:

- v1.0: CISD, không cần FVG. 740 lệnh (histdata 2023-01 → 2026-09).
- v1.1: CISD kèm FVG ≥ 0,5 pip (quy tắc hiện hành). 355 lệnh. Nếu FVG hoàn thành ở nến sau CISD thì vào ở giá đóng nến đó.

Kiểm chéo bằng nguồn thứ hai: Dukascopy 2023-09 → 2026-09 (531 và 282 lệnh), file `cisd-rr-winrate-dukascopy.md`.

Bảng đầy đủ: `cisd-rr-winrate.md`. Dữ liệu từng lệnh: `cisd-rr-winrate_trades.csv`. Script: `po3_cisd_rr_winrate.py`.

Lưu ý: v1.1 trước đây cố ý không kiểm lại trên dữ liệu cũ. Lần này đo theo yêu cầu, nên mọi số của v1.1 dưới đây là trong mẫu. Nó không thay nhật ký thật.

## 1. Khoảng SL

- SL đặt đúng cực trị quét: rủi ro trung vị 4,0 pip (v1.0) và 5,7 pip (v1.1).
- Theo ATR 24 giờ: 0,30 và 0,41 ATR.
- Phí 1 pip khứ hồi vì thế bằng 0,17–0,25 R mỗi lệnh. Đây là con số quyết định toàn bộ kết quả.

## 2. Xác suất chạm k R trước khi chạm SL (v1.1, SL đúng cực trị)

| Mục tiêu | Giữ tới phút 55 | Giữ tối đa 4 giờ | Nền ngẫu nhiên (4 giờ) | Win rate cần để hòa vốn sau phí |
|---|---|---|---|---|
| 1R | 47% | 53% | 46% | 60% |
| 1,5R | 33% | 41% | — | 48% |
| 2R | 23% | 36% | 29% | 40% |
| 3R | 11% | 25% | — | 30% |
| 5R | 2% | 15% | — | 20% |

Nền ngẫu nhiên: cùng nến vào, cùng khoảng SL, đi ngược hướng.

Đọc bảng:

- Ở mọi mức R:R, win rate thực tế thấp hơn win rate cần để hòa vốn sau phí.
- Win rate cao hơn nền ngẫu nhiên khoảng 5–7 điểm % trên histdata. Trên Dukascopy cùng giai đoạn, phần chênh này gần như biến mất.
- Giữ tới phút 55 cắt đứt các lệnh R lớn. Ở 2R, hơn một phần tư số lệnh hết giờ trước khi chạm TP hay SL.

## 3. Kỳ vọng mỗi lệnh

Cấu hình đúng quy trình (v1.1, SL = cực trị + 0,25 ATR, TP 2R, thoát phút 55):

- Histdata: chạm TP 10%, chạm SL 34%, hết giờ 57%.
- Histdata: kỳ vọng +0,03 R trước phí, −0,08 R sau phí 1 pip.
- Dukascopy: kỳ vọng −0,07 R trước phí, −0,17 R sau phí.
- Phí 0,5 pip (tài khoản raw spread tốt): vẫn −0,03 R.

Toàn bộ lưới thử: 2 quy tắc × 3 mức SL × 7 mức TP × 2 cách thoát = 84 tổ hợp.

- Trước phí: mọi tổ hợp nằm trong khoảng −0,04 đến +0,17 R (histdata).
- Sau phí 1 pip: chỉ 1 tổ hợp trên histdata dương (+0,02 R, v1.1, SL + 0,1 ATR, TP 4R, giữ 4 giờ). Khoảng tin cậy của nó từ −0,19 đến +0,23. Trên Dukascopy tổ hợp này âm.
- Một tổ hợp dương trong 84 lần thử là đúng mức may rủi. Không phải lợi thế.

## 4. So với các lần đo trước

- Khớp `../analysis-2026-09-21/ket-luan-2-rr-sltp-bias.md` mục 2: 740 lệnh v1.0 ở đây so với 736 lệnh ở đó; kết luận giống nhau.
- Thêm FVG (v1.1) làm SL rộng hơn và loại bớt nửa số lệnh. Nó giảm tỷ lệ phí trên R nhưng không tăng chất lượng hướng: so với nền ngẫu nhiên, chênh lệch của v1.1 còn nhỏ hơn v1.0.
- Chia theo cặp, giờ, thứ, hướng, năm: không nhóm nào có khoảng tin cậy sau phí nằm trên 0. GBPUSD và năm 2024 nhích dương nhưng mỗi nhóm chỉ khoảng 100–180 lệnh, và đó là chọn sau khi đã thấy kết quả.

## 5. Chuỗi thua

- Với quy trình hiện tại, 59% lệnh kết thúc lỗ sau phí.
- Chuỗi lỗ dài nhất trong mẫu: 9 lệnh liên tiếp.
- Mô phỏng 100 lệnh: chuỗi lỗ dài nhất trung vị là 7. Gần một nửa số lần có chuỗi từ 8 lệnh trở lên.
- Chuỗi 8–10 lệnh lỗ là bình thường, không phải dấu hiệu quy tắc hỏng.

## 6. Kết luận

- Vào tại giá đóng nến CISD không có win rate đủ cao cho bất kỳ mức R:R nào sau khi trừ phí.
- Trước phí, kỳ vọng xấp xỉ 0. Đó là đặc điểm của bước ngẫu nhiên.
- Nguyên nhân chính là SL quá nhỏ (4–6 pip). Phí và trượt giá ăn 0,15–0,25 R mỗi lệnh.
- Quy tắc v1.1 trong `../analysis-2026-09-21/quy-trinh.md` giữ nguyên. Không đổi tham số dựa trên bảng này. Trạng thái vẫn là giao dịch giấy hoặc 0,25% tài khoản cho đến khi có 100 lệnh nhật ký thật.
