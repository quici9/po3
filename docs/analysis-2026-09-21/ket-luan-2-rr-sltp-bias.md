# Kết luận 2: R:R sau CISD/MSS, SL/TP, và bias của nến 03:00 và 09:00 (thứ Ba/Tư/Năm, FX)

Bảng đầy đủ: `rr-sltp-bias-03-09.md` (sinh bởi `po3_rr_session.py`). Phạm vi: chỉ nến H1 03:00 và 09:00 giờ New York, thứ Ba/Tư/Năm, EURUSD/GBPUSD/USDJPY, 2023-01 → 2026-09. Nền: bước ngẫu nhiên cùng pipeline, cùng giờ. Phí giả định 1 pip khứ hồi.

## 1. Khoảng cách CISD/MSS → cực trị, và → đỉnh

**Nến đã biết là định hướng** (có nhìn trước, n ≈ 900): vào tại giá đóng nến CISD thì rủi ro trung vị 0,38 ATR (khoảng 6 pip; 5,5 pip ở 03:00, 6,3 pip ở 09:00), R đến đỉnh trung vị 2,8; 68% nến đạt ≥ 2R, 47% đạt ≥ 3R. MSS đến muộn hơn 2–3 phút và rủi ro rộng hơn: 0,47 ATR (7 pip), R trung vị 2,1, 52% đạt ≥ 2R. CISD cho R tốt hơn MSS vì vào sớm hơn với SL gần hơn. Nhưng những con số này chỉ đúng khi biết trước nến sẽ định hướng. Bước ngẫu nhiên cho R còn cao hơn (3,3) vì cùng cách chọn mẫu.

**Thiết lập thời gian thực** (không nhìn trước, n ≈ 2.900 với CISD): rủi ro trung vị 0,35 ATR (5,4 pip) với CISD, 0,48 ATR (7,4 pip) với MSS. SL đặt sát cực trị bị chạm trong 60 phút ở 66% thiết lập CISD và 57% thiết lập MSS. Trước khi bị chạm SL, giá đi được ≥ 1R ở 46% và ≥ 2R ở 27% với CISD. Nền bước ngẫu nhiên cho cùng con số (49% và 29%). Quét nông (< 0,25 ATR) tốt hơn: ≥ 1R ở 58%, ≥ 2R ở 36%. Quét sâu (≥ 0,5 ATR) tệ: ≥ 1R chỉ 34%.

Trả lời câu hỏi: SL ở cực trị không rộng, chỉ 5–7 pip, tức khoảng 0,35–0,5 ATR giờ. Vấn đề không phải rộng mà là quá sát: hai phần ba lệnh CISD bị chạm SL trong giờ.

## 2. SL và TP: mô phỏng lệnh thật

**Đính chính (cùng ngày, khi kiểm tra chéo bằng một cách cài đặt thứ hai):** bản đầu của mục này đo độ sâu quét bằng đáy cuối cùng của thiết lập, kể cả đáy hình thành *sau* khi đã vào lệnh. Đó là lỗi nhìn trước: nó loại bỏ đúng những lệnh mà giá còn đi sâu thêm sau CISD, tức phần lớn lệnh chạm SL. Khi đo độ sâu tại thời điểm xác nhận, kết quả đổi dấu.

Tất cả thiết lập, không lọc: mọi tổ hợp SL và TP đều âm sau phí 1 pip, từ −0,12 đến −0,26 R mỗi lệnh.

Lọc quét nông (< 0,25 ATR, đo lúc xác nhận) với CISD trước phút 30: kỳ vọng **trước phí** chỉ +0,00 đến +0,04 R, **sau phí** −0,11 đến −0,24 R ở mọi tổ hợp SL/TP, khoảng tin cậy hoàn toàn dưới 0. Không có tổ hợp nào dương. Số liệu +0,07 R từng nêu trước đó là sản phẩm của lỗi nhìn trước (dòng "CÓ nhìn trước" trong bảng đầy đủ giữ lại để đối chiếu).

| Tập (CISD ≤ phút 30, thoát cuối giờ) | SL | TP | n | P(TP) | P(SL) | Kỳ vọng trước phí | Kỳ vọng sau phí |
|---|---|---|---|---|---|---|---|
| Quét nông, đo đúng | cực trị | 2R | 1.236 | 27% | 58% | +0,03 R | −0,24 R |
| Quét nông, đo đúng | cực trị + 0,25 ATR | 2R | 1.236 | 14% | 42% | +0,02 R | −0,11 R |
| Quét nông, đo đúng | cực trị + 0,25 ATR | đỉnh giờ trước | 1.213 | 33% | 38% | +0,02 R | −0,12 R |
| Quét nông, CÓ nhìn trước (sai) | cực trị + 0,25 ATR | 2R | 994 | 17% | 32% | +0,20 R | +0,08 R |

Kết luận mục 2: **không có điểm SL/TP nào biến thiết lập này thành dương.** SL rộng hơn giảm số lần chạm SL nhưng cũng giảm R mỗi lệnh thắng tương ứng. Lợi thế gộp của thiết lập gần bằng 0 trước phí, nên bất kỳ phí nào cũng làm nó âm. Điều "an toàn" duy nhất là không giao dịch nó bằng tiền thật.

## 3. Nến 03:00 và 09:00 có bias theo thông tin nào trước đó?

Không có yếu tố nào trong 10 yếu tố kiểm tra dự báo được hướng nến 03:00 hay 09:00. Tất cả nằm trong 47–52% với khoảng tin cậy 95% chứa 50%, và bước ngẫu nhiên cho cùng dải. Kết luận giữ nguyên khi đổi mục tiêu thành khối hai giờ 03–04 và 09–10, khi chỉ tính nến định hướng, và khi tách theo ngày trong tuần.

Các yếu tố đã thử: hướng giờ liền trước (02:00 hoặc 08:00); hướng hai giờ liền trước; hướng phiên liền trước (Á cho 03:00, London cho 09:00); hướng ngày ICT liền trước; giờ trước và phiên trước cùng chiều; giờ trước đóng cửa ngoài biên phiên trước; giờ trước quét một phía biên phiên trước; mở cửa dưới điểm giữa biên phiên trước; mở cửa dưới giá mở 00:00; mở cửa dưới giá mở ngày 17:00.

Hai con số hơi lệch đáng ghi nhận nhưng không đủ để dùng: 09:00 hơi đảo chiều so với 08:00 (47%), và 03:00 hơi thuận theo "mở cửa dưới giá mở ngày → tăng" (52%). Với 20 phép thử thì hai kết quả cỡ này xuất hiện do may rủi là bình thường.

Một quan sát có ích hơn hướng: khi nến 09:00 đi cùng chiều phiên London trước đó, thân nến lớn hơn rõ (1,03 ATR so với 0,83). Tức phiên trước không cho biết 09:00 đi hướng nào, nhưng nếu 09:00 đi cùng hướng London thì nó thường đi xa hơn. Điều này ủng hộ việc chờ xác nhận trong nến rồi mới quyết định, thay vì đặt bias từ trước.
