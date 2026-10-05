# Khung phác thảo tuần và ngày — viết biên và thời điểm, không viết hướng

Phụ lục vận hành cho `../analysis-2026-09-21/quy-trinh.md`. Mọi con số dưới đây lấy từ
`weekly-daily-profiles.md` (1915 ngày, 386 tuần, EURUSD + GBPUSD, 2023-01 → 2026-09) và đã trừ phần
bước đi ngẫu nhiên tái tạo được — lý do chọn/loại từng mục ở `ket-luan.md`.

**Nguyên tắc chi phối cả khung:** phần *hướng* không đo được, kể cả bằng weekly profile, nến thứ Hai,
mốc mở 00:00 hay mốc mở tuần. Phần *biên độ* và *thời điểm* thì đo được. Bản phác thảo vì thế viết ra
hai kịch bản đối xứng kèm mốc giá, không viết ra một hướng. Nếu bản phác thảo của một ngày chỉ có một
hướng, nó sai định dạng — ghi vào cột vi phạm quy tắc của nhật ký.

## 1. Chọn lọc — cái gì vào khung, cái gì bị loại

| Đưa vào khung | Loại khỏi khung |
|---|---|
| Biên độ còn lại sau 03:00 và 09:00 (mục 2) | Nhãn weekly profile dùng để dự báo (mục 4: không ô nào khác ngẫu nhiên) |
| Khối Luân Đôn và New York là nơi cực trị hình thành (mục 1) | Phiên Á như nơi tìm setup (25% đáy ngày, thấp hơn cả ngẫu nhiên) |
| PDH/PDL/PWH/PWL làm mục tiêu thanh khoản (mục 3) | PDH/PDL làm dự báo hướng (bị quét với xác suất đồng xu) |
| P(biên thứ Hai bị phá cả hai phía) để chuẩn bị hai kịch bản (mục 6) | Hình dạng nến thứ Hai để chọn hướng tuần (ngẫu nhiên tái tạo đủ cả bốn số) |
| Risk và khoảng cách tới TP đối chiếu biên còn lại (mục 7) | Nối tiếp hướng qua mốc mở 00:00 (58,8% so với 64,0% ngẫu nhiên) |

## 2. Phác thảo tuần — chiều thứ Hai sau 17:00 New York, 10 phút

Ghi vào nhật ký tuần, bốn mục, không mục nào là hướng:

1. **Mốc cố định:** giá mở tuần, PWH và PWL của tuần trước, đỉnh/đáy nến thứ Hai.
2. **Hai kịch bản đối xứng,** mỗi kịch bản một dòng: "phá đỉnh thứ Hai tại X → thanh khoản gần nhất là
   PWH tại Y" và "phá đáy thứ Hai tại Z → thanh khoản gần nhất là PWL tại W".
3. **Xác suất hiệu chuẩn** (tra bảng, không tính lại):

   | Câu hỏi | Số đo |
   |---|---|
   | Đỉnh tuần chưa in sau thứ Hai | 73,6% |
   | Đáy tuần chưa in sau thứ Hai | 72,8% |
   | Biên thứ Hai bị phá **cả hai phía** trong tuần | 47% (thứ Hai biên hẹp: 64%; biên rộng: 25%) |
   | PWH bị quét trong tuần | 51,8% |
   | PWL bị quét trong tuần | 47,4% |
   | Quét cả PWH và PWL | 12% |
   | Không quét mức nào | 12% |
   | Biên tuần đã in sau thứ Ba / thứ Tư (trung vị) | 62% / 79% |

4. **Một dòng cấm:** không ghi "tuần này tăng/giảm", không ghi profile dự kiến. Nhãn profile tuần chỉ
   điền chiều thứ Sáu, sau khi tuần đóng, để nhật ký có mẫu số về sau.

Đọc nhanh: gần một nửa số tuần phá cả hai phía biên thứ Hai, và tuần nào thứ Hai biên hẹp thì tỷ lệ đó
lên gần hai phần ba. Đó là lý do khung yêu cầu hai kịch bản chứ không phải một.

## 3. Phác thảo ngày — 02:50 New York, 5 phút, chỉ thứ Ba/Tư/Năm

1. **Mốc cố định:** PDH, PDL, đỉnh/đáy giờ 02:00, mở 00:00, ATR 24 giờ theo pip.
2. **Hai kịch bản đối xứng** quanh biên giờ 02:00, mỗi kịch bản ghi mục tiêu thanh khoản gần nhất.
3. **Xác suất hiệu chuẩn tại 03:00** (thứ Ba/Tư/Năm):

   | Câu hỏi | Số đo |
   |---|---|
   | Đỉnh ngày đã in | 28,5–29,5% |
   | Đáy ngày đã in | 23,6–25,7% |
   | Cả hai đã in | ~0% |
   | Biên độ còn lại (Q1 / trung vị / Q3) | 47–55 / 64–71 / 84–92 pip |
   | Risk trung vị của setup, khoảng cách tới TP 2R | 7 pip, 15 pip |
   | PDH sẽ bị quét trong ngày | ~50% |
   | PDL sẽ bị quét trong ngày | ~48% |
   | Ngày không quét mức nào | 14% |

4. **Tại 08:50, cập nhật lại ba dòng:** đỉnh ngày đã in 50,8–54,7%; đáy ngày đã in 46,9–51,0%; cả hai đã
   in 10–15%; biên độ còn lại 34–40 / 47–54 / 60–73 pip; risk trung vị 8 pip, tới TP 2R là 16 pip.
   Kiểm tra một điều duy nhất: **mục tiêu 2R có nằm trong biên còn lại không.** Có — kể cả ở Q1 — nên đây
   là ô xác nhận, không phải ô quyết định; nó chỉ bắt lỗi những ngày biên đã cạn bất thường.

5. **Cuối ngày, điền nhãn:** khối đặt đáy ngày và khối đặt đỉnh ngày (Á / Luân Đôn / New York), biên độ
   ngày theo ATR20 (hẹp < 0,7 / trung bình / rộng > 1,3). Hai nhãn này là mẫu số cho kỳ rà soát 100 lệnh.

## 4. Phân bổ

**Phân bổ thời gian có mặt.** Giữ đúng phạm vi hiện tại: thứ Ba/Tư/Năm, hai cửa sổ 03:00–03:30 và
09:00–09:30, EURUSD và GBPUSD. Số đo không đòi mở rộng và cũng không đòi thu hẹp: khối Luân Đôn và New York
giữ 75% cực trị ngày, hai cửa sổ hiện tại đã nằm trong hai khối đó; phiên Á giữ 25% cực trị ngày, thấp hơn
cả ngẫu nhiên (43%), nên không thêm cửa sổ nào trong phiên Á.

**Phân bổ rủi ro: phẳng.** 0,25% tài khoản mỗi lệnh, không ngoại lệ theo profile, theo ngày trong tuần,
theo giờ hay theo trạng thái biên tuần. Căn cứ: tám cách chia nhóm 795 setup đều cho kỳ vọng âm, nhóm tốt
nhất −0,02 R, không nhóm nào có khoảng tin cậy nằm hẳn trên 0. Nâng rủi ro cho nhóm "tốt nhất" của một bảng
tám nhóm là lỗi chọn mẫu sau khi xem dữ liệu — đúng lỗi đã sinh ra con số +0,08 R sai trong lần phân tích đầu.

**Những chênh lệch được phép ghi nhận mà không được phép hành động:** giờ 09:00 có P(TP) 27,3% so với 16,5%
ở giờ 03:00; ngày biên rộng cho −0,23 R so với −0,02 R ở ngày biên hẹp; thứ Năm cho −0,20 R. Ba quan sát này
đi vào nhật ký như giả thuyết chờ kiểm, không vào quy tắc. Kỳ duy nhất được đổi quy tắc vẫn là tháng 1
hằng năm.

## 5. Bổ sung cột nhật ký

Thêm năm cột vào `../analysis-2026-09-21/nhat-ky-mau.csv`, điền sau khi ngày đóng:

| Cột | Giá trị |
|---|---|
| `day_blk_low` | khối đặt đáy ngày: `A` / `London` / `NY` |
| `day_blk_high` | khối đặt đỉnh ngày |
| `day_char` | `hep` / `trung_binh` / `rong` theo ATR20 |
| `week_profile` | điền chiều thứ Sáu: `<pha đáy>/<pha đỉnh>`, pha ∈ `dau` / `giua` / `cuoi` |
| `sketch_two_sided` | `1` nếu bản phác thảo sáng hôm đó có đủ hai kịch bản, `0` nếu chỉ có một |

Cột cuối là cột kiểm tra kỷ luật, đọc cùng các cột vi phạm quy tắc trong kỳ rà soát hằng tuần. Bốn cột đầu
để sau 100 lệnh có thể trả lời câu hỏi mà mô phỏng không trả lời được: profile có tương quan với kết quả
**thực thi thật** hay không.
