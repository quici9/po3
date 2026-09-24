# Kết luận: AMD, cửa sổ mở rộng và FVG sau MSS — London và NY AM, thứ Ba/Tư/Năm

Bảng số đầy đủ: `amd-killzone-tue-thu.md` (sinh bởi `po3_amd_killzone.py`). Dữ liệu: EURUSD, GBPUSD, USDJPY, M1 histdata, 2023-01-03 → 2026-09-10. Phạm vi: giờ New York 02–04 và 08–10, thứ Ba/Tư/Năm. 10.031 nến H1, 4.468 nến định hướng (thân ≥ 50%), 3.190 nến có râu thao túng ≥ 5%. Nền so sánh: bước ngẫu nhiên chạy cùng pipeline.

## 1. Cửa sổ phân phối / mở rộng

**Giờ trong killzone.** London mở rộng ở 03:00 và 04:00 (thân/ATR 0,69 mỗi giờ; mỗi giờ là giờ thân lớn nhất của killzone trong ~40% số ngày). 02:00 yếu (0,49; 21%). NY AM: 09:00 mạnh nhất (0,94; 36%), 10:00 gần bằng (0,84; 36%), 08:00 yếu hơn (0,75; 28%). Xác suất một giờ là nến mở rộng (thân ≥ 65%, biên độ ≥ 0,8 ATR) khoảng 26–28% cho mọi giờ trừ 02:00 (19%).

**Ngày trong tuần.** 09:00 NY thứ Năm (1,08) và thứ Tư (0,99) là hai ô mạnh nhất. Thứ Ba đồng đều hơn giữa London và NY AM. 02:00 thứ Năm yếu nhất (0,43; 15%).

**Trong nến H1** (nến định hướng có râu thao túng, cực trị từ phút 1): pha mở rộng bắt đầu (MSS) ở trung vị phút 16; đến phút 10 mới 34% nến đã có MSS, phút 20: 60%, phút 30: 78%, phút 40: 90%. Pha mở rộng kết thúc (cực trị thuận hướng) ở trung vị phút 55; một nửa số nến in cực trị trong 5 phút cuối, 20% đúng phút 59. Khoảng từ MSS đến cực trị thuận trung vị 33 phút. Quý 15 phút có tiến triển lớn nhất: London là quý 1 (32%), NY AM là quý 3, phút 30–44 (31%; thứ Năm 36%).

Phân bố phút MSS gần trùng bước ngẫu nhiên (trung vị 15 so với 16). Khác biệt so với nền chỉ ở chỗ 17,9% nến in cực trị ngay phút 0 (nền 9,5%) và mở rộng trong FX bắt đầu sớm hơn vài phút.

## 2. Xác suất pha AMD theo phút (nến định hướng có râu thao túng ≥ 5%, n = 3.190)

| Phút | Tích lũy | Thao túng | Đảo cấu trúc | Phân phối | Hoàn tất |
|---|---|---|---|---|---|
| 00–04 | 24% | 48% | 6% | 22% | 0% |
| 05–09 | 5% | 41% | 16% | 38% | 0% |
| 10–14 | 2% | 30% | 17% | 51% | 1% |
| 15–19 | 1% | 22% | 14% | 61% | 2% |
| 20–24 | 0% | 16% | 12% | 69% | 3% |
| 25–29 | 0% | 11% | 10% | 74% | 4% |
| 30–34 | 0% | 6% | 7% | 79% | 8% |
| 35–39 | 0% | 3% | 6% | 80% | 12% |
| 40–44 | 0% | 1% | 5% | 77% | 18% |
| 45–49 | 0% | 1% | 3% | 71% | 26% |
| 50–54 | 0% | 0% | 1% | 61% | 38% |
| 55–59 | 0% | 0% | 0% | 37% | 62% |

Tích lũy (giá còn trong ±0,15 ATR quanh Open) hầu như chỉ tồn tại trong 5 phút đầu và biến mất sau phút 10. Thao túng chiếm ưu thế đến phút 9, còn khoảng một phần ba ở phút 10–14 và dưới 10% từ phút 30. Phân phối vượt 50% từ phút 10–14, đạt đỉnh 79–80% ở phút 30–39, rồi giảm vì nến bắt đầu "hoàn tất". Với mọi nến định hướng (kể cả nến không râu), Phân phối đã chiếm 39% ngay 5 phút đầu.

So với bước ngẫu nhiên: tích lũy ở 5 phút đầu chỉ 24% so với 49% của nền, tức giá FX rời vùng Open nhanh hơn hẳn. Từ phút 15 trở đi hai bảng gần như trùng nhau.

## 3. Sau thao túng và MSS/CISD: FVG và tiếp tục mở rộng

**3a. Nến H1 đã biết là định hướng** (có nhìn trước; n = 2.605 nến có MSS trong giờ). Chân đẩy từ cực trị thao túng đến MSS để lại FVG trong 91% trường hợp. Sau MSS, 74% nến tiếp tục vượt đỉnh chân đẩy mà không quay về FVG trước; 17% quay về FVG rồi mới tiếp tục. Tính trên các nến có FVG: quay về FVG trước khi tiếp tục 18,5%; quay về FVG lúc bất kỳ trong 60 phút 48% (trong phần còn lại của giờ: 39%); chạm 50% FVG 39%; đóng cửa xuyên FVG 23%; quét lại đáy thao túng 7,7%. Độ sâu hồi sau MSS: trung vị 19% chân đẩy, 62% nến hồi dưới 25%, 14% hồi 50–100%. Dùng CISD thay MSS: FVG 80%, đi thẳng 61%, về FVG rồi tiếp tục 19%. Bước ngẫu nhiên cho các con số gần tương đương (về FVG trước khi tiếp tục 16%, bất kỳ lúc nào 42%).

Kết luận 3a: trong một nến PO3 "đẹp", kịch bản sách vở "quét, MSS, hồi về FVG, rồi mở rộng" chỉ xảy ra ở khoảng 1 trong 6 nến. Phần lớn nến đi thẳng từ MSS. Câu "tiếp tục mở rộng" ở đây là hiển nhiên vì đã biết nến đóng cửa định hướng.

**3b. Thiết lập thời gian thực** (không nhìn trước; giờ mở cửa bên trong biên giờ trước, quét đáy hoặc đỉnh giờ trước trong 30 phút đầu, rồi MSS trong 60 phút; n = 8.482 lần quét, 91% có MSS). Cửa sổ 60 phút sau MSS, xét sự kiện nào đến trước:

| Kết cục sau MSS | FX | Bước ngẫu nhiên |
|---|---|---|
| Chạm đỉnh giờ trước trước khi mất đáy thao túng | 30% | 20% |
| Mất đáy thao túng trước | 51% | 57% |
| Không bên nào trong 60 phút | 19% | 24% |
| Mở rộng thêm ≥ 1 chân đẩy trước khi mất đáy | 38% | 42% |
| Lấy lại Open giờ trước khi mất đáy | 69% | 66% |
| Quay về FVG trước khi phân định | 60% | 65% |
| Trong số quay về FVG: chạm đỉnh giờ trước | 13% | 7% |
| Trong số quay về FVG: mất đáy | 68% | 75% |
| Trong số không quay về FVG: chạm đỉnh giờ trước | 56% | 43% |
| Nến H1 đóng cùng hướng thiết lập | 37% | 37% |
| Nến H1 định hướng cùng hướng | 12% | 13% |

Kết luận 3b: quét thanh khoản giờ trước rồi MSS xảy ra ở hầu hết các giờ killzone (85% số giờ có ít nhất một hướng) nên tự nó không chọn lọc gì. Sau MSS, giá quay về FVG là chuyện thường (60%), nhưng đó là dấu hiệu xấu: nhóm quay về FVG mất đáy ở 68% và chỉ 13% tới được thanh khoản đối diện, trong khi nhóm không quay về đạt mục tiêu 56%. Thiết lập này không dự báo hướng đóng cửa của nến H1 tốt hơn bước ngẫu nhiên (37% so với 37%). Lợi thế duy nhất vượt nền là xác suất chạm đỉnh giờ trước trước khi mất đáy (30% so với 20%), và lợi thế này tập trung ở các thiết lập không hồi về FVG.

Lưu ý khi đọc nền so sánh ở 3b: bước ngẫu nhiên có độ sâu quét nhỏ hơn (0,23 ATR so với 0,31) và biên độ giờ trước khác FX, nên chênh lệch dưới 5 điểm không nên coi là tín hiệu.

## Ghi chú bổ sung 2026-09-21

Phân tích tiếp theo (`ket-luan-2-rr-sltp-bias.md`, `rr-sltp-bias-03-09.md`) mô phỏng lệnh thật trên thiết lập ở mục 3b và kết luận: sau khi sửa lỗi nhìn trước trong bộ lọc quét nông, không có tổ hợp SL/TP nào cho kỳ vọng dương sau phí. Các con số "quét nông tốt hơn" ở trên vẫn đúng về mặt mô tả nhưng không đủ để giao dịch.

## Định nghĩa vận hành (tóm tắt)

- Nến định hướng: thân ≥ 50% biên độ. Râu thao túng: râu phía Open ≥ 5% biên độ.
- Tích lũy: giá còn trong dải ±0,15 ATR24 quanh Open. Thao túng: từ lúc rời dải đến phút in cực trị ngược hướng. Đảo cấu trúc: từ cực trị đến MSS. Phân phối: từ MSS đến phút in cực trị thuận hướng. Hoàn tất: sau đó.
- MSS: nến M1 đóng cửa vượt swing high (fractal 1 trái 1 phải) cuối cùng trước đáy thao túng. CISD: đóng cửa vượt Open của chuỗi nến M1 giảm liên tiếp dẫn vào đáy. CISD đến trước hoặc cùng lúc MSS trong 98% trường hợp, sớm hơn khoảng 3 phút.
- FVG: khoảng trống 3 nến đầu tiên trong chân đẩy từ đáy đến nến MSS (cho phép thêm 1 nến sau MSS).
- "Tiếp tục": giá vượt đỉnh của chân đẩy tại thời điểm xác nhận. "Mất đáy": giá thấp hơn cực trị thao túng.
- Nến giảm được xử lý bằng cách đảo dấu giá, nên mọi câu chữ "đáy/đỉnh" đọc đối xứng.
