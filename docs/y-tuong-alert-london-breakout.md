# Ý tưởng: alert London breakout khỏi Asia range

Trạng thái: **ý tưởng, chưa chốt định nghĩa, chưa code** (2026-10-20).

## 1. Bối cảnh

- Quy trình hiện tại: phân tích đa khung, chỉ trên EURUSD. Muốn mở rộng sang XAUUSD và NAS100.
- Bước đầu của quy trình là xác định bias theo killzone, tại các mốc **03:00** và **09:00** giờ New York. Ở mỗi mốc, xem phiên London đang phản ứng thế nào với phiên Asia, chủ yếu tìm **London breakout khỏi Asia range**.
- Nến breakout phải là **nến thân dài, râu ngắn**.

## 2. Phạm vi MVP

- Chỉ alert một sự kiện: **London breakout khỏi Asia range**. Không bắt buộc đúng mốc 03:00/09:00.
- Alert chỉ bắn **sau khi nến breakout đã close**.
- Thời điểm alert nằm trong khoảng **03:00 → hết 10:00 giờ NY**.
- Symbol: EURUSD, XAUUSD, NAS100.

Ngoài phạm vi (để sau): bias đa khung (HTF), SMT EURUSD/DXY, logic riêng cho từng mốc 03:00/09:00, thống kê winrate.

## 3. Nền tảng: Pine Script + TradingView alert

Chọn TradingView thay cho tự chạy service (MT5/API broker + VPS):

- Alert chạy trên server TradingView, không cần máy hay VPS bật.
- `alert.freq_once_per_bar_close` / `barstate.isconfirmed` cho phép alert chỉ bắn sau khi nến close.
- Hàm thời gian nhận `"America/New_York"`, tự xử lý DST. Không gặp lỗi server time của broker MT5 (GMT+2/+3), không lo tuần lệch DST giữa London và NY (cuối tháng 3, cuối tháng 10 đến đầu tháng 11).
- Marker vẽ trên nến lịch sử, kết hợp Bar Replay, thay luôn cho bước replay/backtest khi tinh chỉnh ngưỡng.
- Không cần database. Chống báo trùng bằng biến `var` reset theo ngày.

Lưu ý khi dùng TradingView:

1. **Giới hạn theo gói**: số alert active, có webhook hay không, alert có hết hạn hay không. Cần kiểm tra gói đang dùng.
2. **Mỗi alert gắn với 1 symbol, 1 timeframe, 1 indicator**, nên 3 symbol là 3 alert. Phương án gộp: một script dùng `request.security` quét cả 3 symbol, chỉ cần 1 alert. Đổi lại phức tạp hơn và phải chống repaint.
3. **Alert đóng băng phiên bản script lúc tạo**: sửa script hoặc đổi input thì phải xóa và tạo lại alert.
4. **Kênh nhận**: push app TradingView, email, popup có sẵn. Telegram/Discord cần webhook (gói trả phí) và một bên trung gian. Với MVP, dùng push app là đủ.
5. **Feed giá**: chọn đúng feed broker đang trade (vd `OANDA:EURUSD`), để range khớp giá vào lệnh. Đặc biệt NAS100 CFD khác nhau giữa các broker và khác NQ futures.
6. **Trần mở rộng**: khi cần bias đa khung, lưu lịch sử hay thống kê, cân nhắc tách thành service riêng. Logic đã kiểm chứng trên Pine port sang Python không khó.

Liên quan đến repo: `ICT_Future_Killzones_With_Deadlines_v7.pine` đã có session Asia (`2000-0000`), London (`0200-0500`) và alert mốc 03:00/09:00. Có 2 cách: thêm alert breakout vào v7, hoặc tách thành indicator riêng (gọn hơn, ít phải tạo lại alert khi sửa v7). Nếu viết thêm script Python kiểm chứng trên `data/`, giữ đồng bộ với Pine theo cách v7 đang làm với `verify_indicator.py`.

## 4. Định nghĩa cần chốt

### 4.1 Asia range

Khung giờ NY, lấy High/Low của toàn bộ nến trong khung:

- **20:00–00:00** (Asian killzone theo ICT, trùng session Asia trong v7). Range hẹp, sạch. **Đề xuất mặc định.**
- **19:00–23:00** (session Á trong `config/definitions.toml` của bộ thống kê).
- **18:00/19:00–02:00** (cả phiên Asia đến trước London open). Range rộng hơn.

Cấu hình được theo từng symbol.

### 4.2 Thế nào là breakout

| Cách | Mô tả | Hệ quả |
|---|---|---|
| A | Nến **close** vượt Asia High/Low **lần đầu**, và nến đó phải đạt chuẩn thân dài | Close vượt đầu tiên mà yếu thì không có alert nào trong ngày |
| B | Nến **đạt chuẩn đầu tiên** close vượt level, dù trước đó đã có nến yếu close vượt | Báo nhiều hơn, có thể báo khi giá đã chạy xa |
| C | Nến phải **mở bên trong range và close bên ngoài** (cắt qua level) | Chặt nhất, sát nghĩa "nến breakout" nhất |

Đề xuất: **C**. Nếu giá đã close ngoài range rồi quay về, lần cắt qua tiếp theo vẫn được tính.

### 4.3 Nến thân dài, râu ngắn (lượng hóa)

Ba điều kiện, đều là input:

- `body / (high - low) ≥ 0.6`
- Râu **theo hướng breakout** (râu trên khi break lên, râu dưới khi break xuống) `≤ 0.2 × (high - low)`. Râu này là dấu hiệu bị từ chối nên quan trọng hơn râu phía kia.
- `body ≥ k × ATR(14)` của cùng timeframe, mặc định `k = 1.0`. Điều kiện này loại nến nhỏ nhưng "toàn thân".

Ngưỡng theo ATR áp được cho cả 3 symbol mà không cần chỉnh pip riêng. Các con số trên chỉ là điểm xuất phát, phải tinh chỉnh bằng cách soi marker lịch sử 3–6 tháng.

Tham chiếu: bộ thống kê đang dùng ngưỡng nến định hướng thân ≥ 50% (`config/definitions.toml`), nhưng đó là định nghĩa cho mục đích khác, không bắt buộc phải trùng.

### 4.4 Timeframe nến breakout

M5, M15 hay H1, mỗi timeframe cho tập tín hiệu khác hẳn nhau. Đề xuất mặc định **M15**, có thể chạy song song M5.

### 4.5 Cửa sổ alert và chống trùng

- Chỉ xét nến **close trong khoảng 03:00 → 10:00 NY**. Cần chốt "hết 10:00" là close ≤ 10:00 hay ≤ 10:59.
- Chỉ ngày T2–T6.
- Mỗi phía (High/Low) chỉ báo **lần đầu** trong ngày.
- Nếu sau đó phía bên kia cũng bị break, alert thứ hai ghi rõ **"đã quét cả hai phía"** (cảnh báo Judas swing/reversal).
- Break đã xảy ra **trước 03:00** (London mở khoảng 02:00–03:00 NY): đề xuất **báo bổ sung lúc 03:00 kèm cờ `pre-window`**, vì thông tin này ảnh hưởng đến bias.

### 4.6 Nội dung alert

Symbol, hướng, giờ NY, timeframe, Asia H/L và độ rộng range (so với ADR), OHLC nến, body %, wick %, khoảng cách vượt level, các cờ `both-sides-swept`, `pre-window`, `news-window`.

## 5. Áp dụng cho từng symbol

### EURUSD

Áp nguyên định nghĩa ở mục 4.

### XAUUSD

Áp được nguyên logic. Gold có thanh khoản thật trong phiên Asia (Thượng Hải, Tokyo), nên Asia range có ý nghĩa.

- Biến động lớn hơn nhiều, nên bắt buộc dùng ngưỡng theo ATR.
- Tin 08:30 NY (CPI, NFP...) tạo nến thân rất dài, dễ vượt bộ lọc. Đánh dấu cờ `news-window` (mặc định 08:25–08:45, cấu hình được), không chặn hẳn.

### NAS100

Index không vận hành theo nhịp Asia → London như FX. Định hướng chính đến từ **NY cash open 09:30**, phiên London thường chỉ là pre-market drift.

- Giữ nguyên mô hình Asia → London: chạy được về kỹ thuật nhưng tín hiệu ít giá trị hơn.
- Phương án phù hợp hơn: lấy **range London (02:00–05:00)** hoặc **overnight range (18:00–09:30)**, alert khi **NY AM (09:30–11:00)** break range đó.
- Nến 09:30 mặc định thân rất dài, cần loại trừ hoặc gắn cờ.

Thiết kế chung: mỗi symbol một **rule = (range window, watch window, bộ lọc nến)**. EURUSD và XAUUSD dùng rule Asia → London, NAS100 dùng rule riêng. Cùng logic, chỉ khác input.

## 6. Câu hỏi mở

1. Khung Asia range: 20:00–00:00, 19:00–23:00 hay khung khác?
2. Định nghĩa breakout: A, B hay C?
3. Timeframe nến breakout: M5, M15 hay H1?
4. Ngưỡng ban đầu: body ≥ 60%, râu hướng break ≤ 20%, body ≥ 1×ATR. Có ổn để bắt đầu không?
5. "Hết 10:00" là close ≤ 10:00 hay ≤ 10:59?
6. Break trước 03:00 có báo bổ sung không?
7. NAS100: giữ mô hình Asia → London, hay dùng rule London/overnight range → NY AM?
8. Gói TradingView đang dùng, và feed symbol của broker nào?
9. Mỗi chart một alert, hay một script quét cả 3 symbol?
10. Thêm vào indicator v7 hay tách indicator riêng?

## 7. Bước tiếp theo

1. Chốt các câu hỏi ở mục 6.
2. Viết spec ngắn (định nghĩa đóng băng, có `version`) để duyệt.
3. Viết indicator Pine: vẽ marker trên lịch sử trước, chưa tạo alert.
4. Soi 3–6 tháng trên cả 3 symbol, tinh chỉnh ngưỡng.
5. Tạo alert live.
