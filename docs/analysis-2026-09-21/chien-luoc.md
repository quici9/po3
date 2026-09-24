# Chiến lược PO3 H1 tại 03:00 và 09:00 New York — trạng thái: CHỈ THEO DÕI, KHÔNG GIAO DỊCH TIỀN THẬT

**Đính chính 2026-09-21.** Bản đầu của file này khuyến nghị giao dịch tổ hợp "quét nông + CISD" với kỳ vọng +0,08 R. Con số đó đến từ một lỗi nhìn trước trong bộ lọc độ sâu quét (đo bằng đáy cuối cùng, kể cả đáy hình thành sau khi vào lệnh). Đo đúng, tổ hợp này cho **+0,07 R trước phí và −0,08 R sau phí 1 pip** trên 736 lệnh EURUSD/GBPUSD (2023-01 → 2026-09), P(SL) 42%. Không có tổ hợp SL/TP nào dương. Xem `ket-luan-2-rr-sltp-bias.md` mục 2.

Vì vậy chiến lược dưới đây được giữ lại **làm giả thuyết để kiểm chứng bằng nhật ký giao dịch thủ công** (quy trình ở `quy-trinh.md`), không phải để giao dịch tiền thật. Kiểm chứng thêm trên các tháng mới bằng cách chạy lại `po3_rr_session.py`; repo này chỉ làm thống kê và báo cáo.

## 1. Quy tắc đã chốt (phiên bản 1.0)

| Mục | Quy tắc |
|---|---|
| Cặp | EURUSD, GBPUSD tính vào kết quả; USDJPY chỉ theo dõi |
| Giờ, ngày | Nến H1 03:00 và 09:00 New York; thứ Ba, Tư, Năm |
| Điều kiện | Giờ mở cửa trong biên giờ liền trước; quét đáy/đỉnh giờ trước trong 30 phút đầu; độ sâu quét < 0,25 ATR **tại lúc xác nhận**; CISD trước phút 30; không có thiết lập ngược chiều cùng giờ |
| Vào lệnh | Giá đóng nến M1 CISD |
| SL | Cực trị quét ± 0,25 ATR |
| TP | 2R, hoặc biên giờ trước nếu nằm trong 1,5–2R |
| Thoát | Cuối giờ nếu chưa chạm SL/TP |
| Phí | 1 pip khứ hồi trong sổ sách R |

## 2. Điều dữ liệu nói về chiến lược này

- Trước phí, kỳ vọng gần 0 (+0,07 R). Thiết lập không phân biệt được lệnh thắng và thua tốt hơn bước ngẫu nhiên.
- Sau phí 1 pip, âm (−0,08 R). Với rủi ro 6–9 pip mỗi lệnh, phí là 0,12–0,16 R, lớn hơn toàn bộ lợi thế gộp.
- Không có bias nào trước giờ mở (10 yếu tố đều 50%), nên không có cách lọc hướng để nâng tỷ lệ thắng.
- Hồi về FVG là dấu hiệu hỏng, không phải điểm vào. Điều này đúng nhưng chỉ giúp thoát sớm, không tạo lợi thế vào lệnh.
- Những gì có giá trị thật từ toàn bộ phân tích là các phủ định: không có đỉnh thao túng ở phút 11–25, không có bias theo phiên trước, không có "hồi về FVG rồi mở rộng", và quét thanh khoản không phải tín hiệu.

## 3. Điều kiện để chiến lược được xét lại

Nhật ký thủ công từ 2026-10 (mẫu `nhat-ky-mau.csv`) là dữ liệu ngoài mẫu:

- Dưới 100 lệnh ngoài mẫu: chưa kết luận, tiếp tục ghi.
- Từ 100 lệnh: kỳ vọng ≤ 0 → **dừng theo dõi, đóng giả thuyết**. Đây là kịch bản kỳ vọng.
- Kỳ vọng > 0 và khoảng tin cậy 95% trên 0 → mới đáng xem xét giao dịch bằng tiền thật, bắt đầu 0,25% tài khoản mỗi lệnh.

Không nới quy tắc giữa chừng. Muốn thử biến thể (ví dụ MSS thay CISD, giờ khác, ngưỡng quét khác) thì đo lại bằng `po3_rr_session.py` với tham số mới và ghi thành phiên bản quy tắc riêng trong nhật ký. Mỗi biến thể thử thêm làm tăng khả năng "tìm thấy" lợi thế giả, nên giới hạn tối đa hai biến thể cùng lúc và đòi hỏi khoảng tin cậy trên 0.

## 4. Nếu vẫn muốn giao dịch thủ công theo PO3

Quy trình ở `quy-trinh.md` vẫn dùng được như khung kỷ luật. Nhưng hãy coi nó là **giấy** cho đến khi cổng ở mục 3 đạt. Số liệu hiện tại nói rằng lệnh vào theo CISD sau quét ở 03:00/09:00 sẽ thua phí trong dài hạn.
