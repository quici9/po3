# Quy trình giao dịch thủ công hằng ngày — PO3 H1 tại 03:00 và 09:00 New York

**Phiên bản quy tắc: v1.1 (2026-09-24).** Khác v1.0 ở một điểm: CISD phải kèm FVG (mục 3). Điều kiện này chưa được đo trên dữ liệu cũ và cố ý không đo; chỉ nhật ký thật từ 2026-09-24 mới đánh giá được. Indicator `ICT_Future_Killzones_With_Deadlines_v7.pine` đánh dấu và alert đúng bộ quy tắc này; cách kiểm chứng ở mục 7.

Khung kỷ luật rút từ số đo trong thư mục này. Lưu ý thẳng: với quy tắc dưới đây, kỳ vọng đo được trong mẫu là **âm sau phí** (`ket-luan-2-rr-sltp-bias.md`, mục 2). Quy trình vì thế có hai mục đích: giữ kỷ luật nếu vẫn giao dịch, và tạo nhật ký đủ sạch để thống kê lại sau 100 lệnh. Repo này chỉ làm thống kê và báo cáo; mọi lệnh đều vào tay.

## 1. Lịch trong ngày (giờ New York; giờ Việt Nam cộng 11 giờ mùa hè, 12 giờ mùa đông)

| Giờ NY | Việc |
|---|---|
| 02:50 | Chuẩn bị cho nến 03:00 |
| 03:00–03:30 | Quan sát quét và chờ CISD |
| 03:30 | Hết cửa sổ vào lệnh |
| 03:55 | Đóng lệnh còn mở |
| 08:50 | Chuẩn bị cho nến 09:00 (kiểm tra tin 08:30) |
| 09:00–09:30 | Quan sát quét và chờ CISD |
| 09:30 | Hết cửa sổ vào lệnh |
| 09:55 | Đóng lệnh còn mở |

Chỉ thứ Ba, Tư, Năm. Chỉ EURUSD và GBPUSD. Không giao dịch 02:00, 04:00, 08:00, 10:00.

## 2. Trước giờ (10 phút)

1. Ghi đỉnh và đáy của giờ liền trước (02:00 hoặc 08:00).
2. Ghi ATR 24 giờ tính bằng pip, và ngưỡng quét nông = 0,25 ATR (thường 5–7 pip với EURUSD ở London).
3. Lịch tin: nến 09:00 chỉ giao dịch nếu tin 08:30 đã ra ít nhất 30 phút và không có tin 10:00 lớn. Nến 03:00 bỏ nếu có tin châu Âu trong giờ.
4. Không đặt bias. Không có yếu tố nào trước giờ mở dự báo được hướng (10 yếu tố đo được đều 50%). Nếu thấy mình "chờ mua" hay "chờ bán", ghi vào nhật ký và bỏ qua.

## 3. Trong giờ

**Phút 0–10: chỉ quan sát.** Đây là pha thao túng; hai phần ba cực trị in trong 10 phút đầu. Giờ phải mở cửa bên trong biên giờ trước; mở ngoài biên là tiếp diễn, nghỉ.

**Phút 0–30: điều kiện quét.** Giá quét qua đáy (thiết lập mua) hoặc đỉnh (thiết lập bán) giờ trước. Độ sâu quét tính đến lúc chuẩn bị vào phải dưới 0,25 ATR. Quét sâu hơn là tiếp diễn xu hướng, nghỉ. Quét cả hai biên trong cùng giờ, nghỉ.

**Xác nhận: CISD trước phút 30.** Một nến M1 đóng cửa vượt giá mở của chuỗi nến M1 giảm liên tiếp dẫn vào đáy quét (đối xứng cho bán). CISD đến sớm hơn MSS khoảng 3 phút và trùng MSS ở 98% trường hợp. Nến CISD phải bắt đầu ở phút 29 trở về trước.

**Bắt buộc có FVG (v1.1).** Trong chân đẩy từ đáy quét đến nến CISD, hoặc hoàn thành ở nến ngay sau CISD, phải có một FVG tăng (đáy nến sau cao hơn đỉnh nến trước nó hai nến) rộng ít nhất 0,5 pip. Không có FVG thì giờ này không có setup theo hướng đó, kể cả khi sau đó xuất hiện CISD thứ hai. Ngưỡng 0,5 pip là để lọc nhiễu feed (trung vị FVG đo được 0,7 pip; FVG dưới 0,5 pip tồn tại hay không tùy nguồn dữ liệu), không phải bộ lọc độ mạnh.

**Vào lệnh:** lệnh thị trường ngay khi nến xác nhận đóng (nến CISD nếu FVG đã có, hoặc nến ngay sau nếu FVG hoàn thành ở đó). Không đặt lệnh chờ ở FVG: 60% lệnh có giá quay về FVG, nhưng nhóm đó mất đáy ở 68%.

**SL:** dưới cực trị quét thêm 0,25 ATR. **TP:** 2R, hoặc đỉnh/đáy giờ trước nếu mốc đó nằm trong 1,5–2R.

**Trong lệnh:** giá đóng cửa M1 trở lại trong FVG của chân đẩy thì dời SL về hòa vốn hoặc đóng. Không nhồi, không vào lại sau SL, một lệnh mỗi giờ mỗi cặp.

**Sau phút 30 chưa có CISD:** bỏ giờ này. **Phút 55:** đóng lệnh còn mở tại giá thị trường; một nửa số lệnh kết thúc kiểu này.

## 4. Sau giờ (5 phút)

Ghi nhật ký theo `nhat-ky-mau.csv`. Bắt buộc: phiên bản quy tắc (`rule_version`), độ rộng FVG theo pip (`fvg_pip`), phút quét, độ sâu quét theo pip và ATR, phút CISD, giá vào dự kiến và giá khớp, trượt giá, SL, TP, lý do thoát, phút thoát, R trước phí, phí thực, R sau phí, và cột vi phạm quy tắc nếu có. Ghi cả những giờ **không** vào lệnh và lý do (không quét, quét sâu, không CISD, có tin). Đó là mẫu số của thống kê sau này.

## 5. Rà soát

- **Hằng tuần, 15 phút:** đếm vi phạm quy tắc (vào trước CISD, không thoát phút 55, vào khi quét sâu, có bias, đặt lệnh ở FVG). Mục tiêu 0. Không đọc lãi lỗ tuần vì quá ít lệnh.
- **Hằng tháng:** chạy lại `po3_rr_session.py` trên tháng mới để có số liệu mô phỏng cùng tháng, rồi so với nhật ký. Chênh lệch giữa hai bên là chi phí thực thi (trượt giá và phí). Trên 0,1 R mỗi lệnh là phí thực tế đã vượt giả định 1 pip.
- **Sau 100 lệnh nhật ký:** tính kỳ vọng sau phí và khoảng tin cậy 95%. Kỳ vọng ≤ 0: đóng giả thuyết, ghi kết luận vào `docs/`. Kỳ vọng > 0 và khoảng tin cậy trên 0: mới nâng rủi ro mỗi lệnh lên 0,5%. Cho đến lúc đó: 0,25% tài khoản mỗi lệnh, hoặc giao dịch giấy.
- **Tháng 1 hằng năm:** kỳ duy nhất được đổi quy tắc. Ghi phiên bản quy tắc vào nhật ký để không trộn hai bộ quy tắc trong một thống kê.

## 6. Tuyệt đối tránh

- Đổi quy tắc sau một chuỗi thua hoặc thắng ngắn. Chuỗi 5 SL liên tiếp nằm trong kỳ vọng.
- Thêm bộ lọc mới rồi kiểm lại trên dữ liệu cũ. Đó chính là cách sinh ra con số +0,08 R sai trong lần phân tích đầu.
- Bỏ quy tắc thoát phút 55 hay quy tắc không bias vì cảm giác.
- Đọc lãi lỗ theo tuần. Đơn vị đánh giá là 100 lệnh.
- Tin vào số trong mẫu. Chỉ nhật ký thật mới quyết định.

## 7. Indicator và kiểm chứng

- `ICT_Future_Killzones_With_Deadlines_v7.pine` (chart M1, OANDA): vẽ killzone/deadline như v6, thêm mũi tên `CISD BUY/SELL`, đường CISD (nằm ngang tại mức CISD, từ nến gốc của chuỗi nến ngược chiều đến nến xác nhận), box FVG và một alert duy nhất khi có CISD + FVG (đặt alert kiểu "Any alert() function call"). Bảng góc trên phải cho biết đang ở bước nào trong giờ.
- Lớp debug (tắt mặc định): biên giờ trước, ngưỡng 0,25 ATR, điểm quét, lý do bỏ, bảng đối chiếu 10 ngày và Pine Logs, mỗi giờ một dòng.
- `verify_indicator.py EURUSD --days 10` in cùng định dạng từ Dukascopy (`data/fetch_dukascopy.py` rồi `data/build_csv_dukascopy.py`). So theo tầng: PH/PL và ATR lệch ≤ 0,3 pip là feed; phút CISD lệch ≤ 1 là feed; kết quả cuối (SIGNAL/SKIP) phải trùng, trừ FVG sát 0,5 pip.
- Kiểm chứng 2026-09-24 trên 18 giờ (15–23/09, hai cặp): 17 giờ trùng kết quả; 1 giờ khác (EURUSD 23/09 03:00) vì FVG 0,5 pip trên OANDA và 0,4 pip trên Dukascopy.
