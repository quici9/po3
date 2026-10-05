# Kết luận — weekly profile và daily profile (2026-10-05)

Số liệu: `weekly-daily-profiles.md`, sinh bởi `po3_profiles.py` trên M1 histdata EURUSD + GBPUSD,
2023-01-02 → 2026-09-11: **1915 ngày**, **386 tuần**. Mọi bảng đều có cột đối chiếu với bước đi ngẫu nhiên
Gauss không trôi, biến động hằng số, chạy qua đúng pipeline đó. Đọc kết luận theo thứ tự: cái gì còn lại
sau khi trừ phần số học, cái gì không.

## 1. Daily profile có thật, nhưng nội dung của nó là đường cong biến động theo phiên

Ba khối trong ngày (Á 17:00–02:00, Luân Đôn 02:00–07:00, New York 07:00–17:00) phân bố cực trị ngày lệch
rất mạnh so với ngẫu nhiên, và lệch theo một hướng duy nhất: **cực trị bị rút khỏi phiên Á và dồn về
Luân Đôn với New York.**

| | Đáy ngày ở Á | Đáy ở Luân Đôn | Đáy ở New York |
|---|---|---|---|
| FX | 25,2% | 19,1% | 55,7% |
| Ngẫu nhiên | 43,1% | 15,0% | 41,9% |

Ô lệch mạnh nhất là *đáy New York / đỉnh New York* — 18,7% số ngày, so với 5,0% ở ngẫu nhiên
(+13,7 điểm, CI95 +11,7 đến +15,7). Nghĩa là gần một phần năm số ngày có **cả hai** cực trị in trong
phiên New York; chuỗi ngẫu nhiên gần như không sinh ra dạng này.

Nhưng nội dung thông tin dừng ở đó. Biên độ trung vị theo phiên: Á 20–00 là 18 pip, 00–02 là 11 pip,
Luân Đôn 02–05 là 27 pip, 05–07 là 21 pip, NY sáng 07–11 là 38 pip, NY chiều 11–16 là 34 pip. Xếp các phiên
theo biên độ rồi xếp theo xác suất giữ cực trị ngày (00–02: 2,6%; Á 20–00: 8,2%; Luân Đôn: 13,6%;
NY sáng: 23,8%; NY chiều: 25,7%) thì hai thứ tự trùng nhau, trừ cửa sổ hai giờ 05–07 (biên 21 pip nhưng chỉ
5,5% — nó ngắn hơn các phiên khác). **Daily profile không nói thêm điều gì ngoài "cực trị hình thành ở nơi
có biến động, và nơi đó rộng bao nhiêu giờ".** Nó hữu ích để biết *khi nào* nên có mặt, không hữu ích để
biết *hướng nào*.

Một cảnh báo kỹ thuật: 20,7% đáy ngày rơi vào "ngoài phiên" (16:00–17:00 và 17:00–20:00). Phần lớn là hiệu
ứng biên của cửa sổ ngày 17:00→17:00 — nến đầu hoặc nến cuối của cửa sổ thường là cực trị trong ngày xu hướng.
Ngẫu nhiên cho 35,5% ở cùng nhóm, cao hơn, nên đây là số học chứ không phải cấu trúc.

## 2. Weekly profile không mang thông tin nào

Chín profile tuần theo pha (đầu tuần = thứ 2–3, giữa tuần = thứ 4, cuối tuần = thứ 5–6): **không một ô nào
lệch khỏi ngẫu nhiên ở mức ý nghĩa 95%.** Tuần tăng kinh điển (đáy đầu tuần, đỉnh cuối tuần) 29,3% so với
33,0% ở ngẫu nhiên; tuần giảm kinh điển 32,9% so với 32,0%.

Phân bố ngày đặt cực trị tuần cũng vậy: thứ Hai 27,2%, thứ Ba 15,0%, thứ Tư 12,4%, thứ Năm 16,3%,
thứ Sáu 29,0% — hình chữ U này tái tạo được gần như chính xác bằng bước đi ngẫu nhiên (27,6% / 17,0% /
13,9% / 17,5% / 24,0%), mọi khoảng tin cậy của hiệu đều chứa 0. Hình chữ U là hệ quả của việc lấy cực trị
trên một đoạn hữu hạn, không phải của lịch kinh tế hay hành vi nhà tạo lập.

Hệ quả thẳng: **"tuần này là tuần kiểu gì" không phải một câu hỏi có câu trả lời trước.** Nhãn weekly profile
chỉ gán được chiều thứ Sáu.

## 3. Những hiệu ứng đầu tuần trông mạnh đều là số học

Bảng *biên thứ Hai* nhìn rất thuyết phục: thứ Hai đóng cửa tăng thì 34,7% khả năng đáy thứ Hai là đáy tuần,
thứ Hai đóng cửa giảm thì chỉ 15,5%; thứ Hai biên hẹp thì 63,6% khả năng biên thứ Hai bị phá cả hai phía,
thứ Hai biên rộng thì 25,5%. Cả bốn số đều được bước đi ngẫu nhiên tái tạo trong khoảng nhiễu
(41% / 13% / 60% / 30%).

Đó vẫn là **số hiệu chuẩn dùng được** — xác suất thật, đo trên dữ liệu thật — nhưng không phải lợi thế.
Biết chúng giúp đặt kỳ vọng đúng; không giúp chọn hướng.

## 4. Nối tiếp hướng: bằng hoặc kém ngẫu nhiên

Giá tại 03:00 nằm trên mở 00:00 New York thì 58,8% ngày đóng cửa vẫn trên mốc đó; tại 09:00 là 74,4%.
Nghe như quán tính mạnh. Bước đi ngẫu nhiên cho 64,0% và 75,5% — **cao hơn**. Mức 03:00 thậm chí lệch âm có
ý nghĩa (−5,3 điểm, CI95 −9,6 đến −0,9): thị trường thật quay đầu qua mốc mở 00:00 *thường xuyên hơn* chuỗi
ngẫu nhiên. Thứ Hai đóng cửa tăng → tuần đóng cửa tăng: 58,2% so với 65,2% ngẫu nhiên.

Kết quả này trùng với kết luận cũ của repo (10 yếu tố trước giờ mở đều 50%) và mở rộng nó: **không có mốc
quy chiếu nào trong ngày hay trong tuần — mở 00:00, mở tuần, nến thứ Hai — cho phép phác thảo hướng.**

## 5. Mức DOL: tỷ lệ bị quét đúng bằng ngẫu nhiên, chỉ hình dạng hơi khác

PDH bị quét 49,7% số ngày (ngẫu nhiên 50,8%), PDL 47,6% (49,5%) — không lệch. PWH bị quét 51,8% số tuần,
PWL 47,4%; cả hai phía 12%, một phía 76%, không phía nào 12%.

Chỗ duy nhất lệch: ngày quét **cả hai** mức PDH và PDL chiếm 11% (ngẫu nhiên 9%) và ngày **không quét mức nào**
chiếm 14% (ngẫu nhiên 9%). Ngày thật phân cực hơn một chút — hoặc một phía, hoặc nằm gọn trong biên hôm trước.
Lệch nhỏ, và không chỉ ra phía nào.

Giá trị thực tế của panel DOL vì thế là *hiệu chuẩn mục tiêu*, không phải dự báo: một nửa số ngày lấy PDH,
một nửa lấy PDL, nên đặt TP vượt PDH khi chưa có gì xác nhận là đặt vào một đồng xu.

## 6. Phần dùng được: biên độ còn lại sau giờ quyết định

Đây là bảng có giá trị vận hành cao nhất trong cả đợt phân tích.

| Mốc | P(đỉnh ngày đã in) | P(đáy ngày đã in) | P(cả hai đã in) | Biên độ còn lại (pip): Q1 / trung vị / Q3 |
|---|---|---|---|---|
| 03:00 (thứ 3–5) | 28,5–29,5% | 23,6–25,7% | 0% | 47–55 / 64–71 / 84–92 |
| 09:00 (thứ 3–5) | 50,8–54,7% | 46,9–51,0% | 10–15% | 34–40 / 47–54 / 60–73 |

Đọc: tại 03:00, ba phần tư số ngày chưa in đáy ngày và bảy phần mười chưa in đỉnh ngày — cửa sổ 03:00 nằm
sớm trong ngày, biên độ còn lại trung vị 64–71 pip. Tại 09:00 thì một nửa số ngày đã in xong cực trị phía
này hay phía kia, biên độ còn lại tụt xuống 47–54 pip. Risk trung vị đo được trên 795 setup là 7 pip ở
giờ 03:00 và 8 pip ở giờ 09:00, tức khoảng cách tới TP 2R là 15–16 pip. **Mục tiêu 2R vì thế nằm gọn trong
biên độ còn lại ở cả hai giờ** — kém nhất là 09:00 với Q1 của biên còn lại 34 pip, vẫn gấp đôi khoảng cách
tới TP. Quy tắc TP hiện tại không bị biên độ chặn; nhưng khoảng trống ở 09:00 nhỏ hơn rõ, và đó là lý do
kỹ thuật chứ không phải cảm giác để không nới TP ở giờ đó.

## 7. Phân bổ theo profile: không có nhóm nào đổi dấu kỳ vọng

Chạy lại bộ quy tắc **v1.0** (quét biên giờ trước, độ sâu < 0,25 ATR, CISD trước phút 30, SL cực trị +
0,25 ATR, TP 2R, thoát sau 60 phút, phí 1 pip) trên 795 setup, rồi chia nhóm theo trạng thái profile **biết
được tại lúc nến CISD đóng**:

| Nhóm | n | P(TP) | Kỳ vọng R [CI95] |
|---|---|---|---|
| Tất cả | 795 | 20,9% | −0,091 [−0,176; −0,006] |
| Giờ 09:00 | 322 | 27,3% | −0,032 [−0,174; +0,111] |
| Giờ 03:00 | 473 | 16,5% | −0,131 [−0,237; −0,026] |
| Cực trị ngày cùng phía đặt ở khối Luân Đôn | 252 | 23,8% | −0,016 [−0,172; +0,140] |
| Cực trị ngày cùng phía đặt ở khối Á | 438 | 17,6% | −0,145 [−0,256; −0,035] |
| Ngày biên hẹp | 199 | 22,1% | −0,017 [−0,192; +0,158] |
| Ngày biên rộng | 137 | 16,8% | −0,229 [−0,426; −0,032] |
| Thứ Năm | 277 | 18,8% | −0,198 [−0,339; −0,057] |

Nhóm tốt nhất đạt −0,02 R; không nhóm nào có khoảng tin cậy nằm hẳn trên 0. Trạng thái biên tuần
(quét biên tuần cùng phía / còn ≥ 2R tới biên đối diện / sát biên đối diện) không tách được gì:
−0,07, −0,08, −0,18 R, ba khoảng tin cậy trùm lên nhau.

**Kết luận phân bổ: profile không dùng để phân bổ rủi ro.** Chia nhỏ 795 setup thành tám cách đã là tám lần
thử; đọc dòng tốt nhất của một bảng như thế rồi nâng rủi ro cho nhóm đó chính là cách sinh ra con số +0,08 R
sai trong lần phân tích đầu. Giữ rủi ro phẳng.

## 8. Tổng kết một dòng mỗi mục

1. Daily profile thật, nhưng chỉ nói "cực trị hình thành nơi có biến động" — dùng để **chọn giờ có mặt**.
2. Weekly profile không mang thông tin — **bỏ khỏi quy trình ra quyết định**, giữ lại như nhãn ghi nhật ký.
3. Mọi hiệu ứng "hình dạng nến thứ Hai" đều tái tạo được bằng ngẫu nhiên — **số hiệu chuẩn, không phải lợi thế**.
4. Nối tiếp hướng kém ngẫu nhiên — **không phác thảo hướng, kể cả bằng mốc mở 00:00 hay mở tuần**.
5. PDH/PDL/PWH/PWL bị quét với xác suất của đồng xu — **dùng làm mục tiêu thanh khoản, không làm dự báo**.
6. Biên độ còn lại sau 03:00 và 09:00 là phần đo được dùng được nhất — **dùng để kiểm tra TP có chỗ không**.
7. Không nhóm profile nào đổi dấu kỳ vọng — **rủi ro phẳng, 0,25% mỗi lệnh, không ngoại lệ theo profile**.

Hệ quả với yêu cầu ban đầu ("phác thảo, định hình hướng đi có thể xảy ra trong ngày, trong tuần"): phần
*hướng* không đo được. Phần *biên* và *thời điểm* thì đo được, và khung phác thảo chỉ nên viết ra biên với
thời điểm. Cách làm cụ thể: `phac-thao-ngay-tuan.md`.
