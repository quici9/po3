# po3 — Thống kê Power of 3 trên nến H1 (FX)

Bot chạy trên GitHub Actions, đo phân bố thời gian tạo cực trị thao túng trong giờ, giờ động lượng cao nhất trong ngày, và ngày phân phối trong tuần trên các cặp FX chính. Gửi tóm tắt qua Telegram, báo cáo chi tiết dạng Markdown đính kèm và commit vào repo.

Nền tảng số liệu và lý do thiết kế: `docs/bao-cao-v2-fx.md` (báo cáo đã xác thực), `docs/chung-thuc-fx.md` (chứng thực FX), `docs/errata-xac-thuc.md` (đối chiếu báo cáo gốc).

## Chu kỳ

| Workflow | Lịch (UTC) | Việc làm |
|---|---|---|
| `monthly` | 03:00 các ngày 3–8 hằng tháng | Tải M1 tháng trước (histdata, fallback Dukascopy), cập nhật `data/h1/<PAIR>.csv.gz`, sinh `reports/monthly/YYYY-MM/report.md`, gửi Telegram, commit. Thoát ngay nếu báo cáo tháng đã có. |
| `annual` | 04:00 ngày 10 tháng 1 | Sinh `reports/annual/YYYY/report.md` (tích lũy + năm, kèm ngày trong tuần), gửi Telegram, commit. |
| `probe-data-sources` | thủ công | Thử tải một tháng từ cả hai nguồn trên runner, báo kết quả qua Telegram. Không ghi dữ liệu. |
| `ci` | mỗi push / PR | `pytest` trên fixture cố định để phát hiện thay đổi định nghĩa ngoài ý muốn. |

Chạy tay: tab Actions → chọn workflow → Run workflow (nhập tháng/năm nếu muốn chạy bù).

## Định nghĩa đóng băng

Mọi ngưỡng và giờ phiên nằm trong `config/definitions.toml`, có trường `version`. Mỗi báo cáo ghi phiên bản đã dùng. Chỉ đổi trong kỳ rà soát hằng năm, kèm tăng `version` và cập nhật số tham chiếu trong `tests/test_po3.py`.

- Nến định hướng: thân ≥ 50% biên độ. Râu thao túng: râu phía mở cửa ≥ 5% (kiểm tra thêm với 15%).
- Cực trị thao túng: đáy của nến tăng / đỉnh của nến giảm; phút = nến M1 đầu tiên chạm mức đó.
- Phiên theo giờ New York (tz database, tự xử lý DST): Á 19–23, London 02–04, NY AM 08–10, NY PM 13–15.
- Cảnh báo tháng: |z| ≥ 3 so với nền (toàn bộ lịch sử trừ tháng đó); độ phủ giờ ngày thường < 95% → cờ dữ liệu.

## Dữ liệu

- `data/h1/<PAIR>.csv.gz`: một dòng mỗi nến H1 (OHLCV, số nến M1, phút tạo đáy, phút tạo đỉnh, nguồn). Không phụ thuộc định nghĩa, đủ để tính lại mọi thống kê. Đây là thứ duy nhất được commit.
- M1 thô không lưu trong repo. histdata: giờ EST cố định, đã quy về UTC. Dukascopy: UTC, giá chia 1e5 (1e3 với cặp JPY).
- Lịch sử ban đầu: 2023-01 → 2026-08 cho EURUSD, GBPUSD, USDJPY, dựng từ histdata.

## Chạy cục bộ

```
pip install -r requirements.txt
export PYTHONPATH=src
python -m po3 probe   --month 2026-08              # thử nguồn dữ liệu
python -m po3 update  --month 2026-08              # tải và cập nhật facts (bỏ qua nếu đã có, --force để tải lại)
python -m po3 monthly --month 2026-08              # báo cáo tháng (thêm --notify để gửi Telegram)
python -m po3 annual  --year 2025
pytest -q
```

Biến môi trường khi gửi Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (trên GitHub là Secrets cùng tên). Bot chỉ gửi, không nhận lệnh.

## Vận hành

- **Tháng không có tin nhắn:** xem tab Actions. Nếu cả hai nguồn thất bại, bot đã gửi tin "tải dữ liệu thất bại"; chạy lại `monthly` thủ công sau vài ngày. Workflow tự thử lại mỗi ngày đến mùng 8.
- **Cron bị tắt** (GitHub tắt lịch sau 60 ngày repo không có commit): bot tự commit mỗi tháng nên bình thường không xảy ra; nếu có, bật lại trong tab Actions.
- **Thêm cặp:** thêm vào `pairs` trong `config/definitions.toml`, chạy `update` cho các tháng lịch sử cần có (hoặc `bootstrap` từ file M1 cục bộ), commit `data/h1/<PAIR>.csv.gz`.
- **Tải lại một tháng:** Run workflow `monthly` với `month` và `force = true`.
- **Đổi định nghĩa:** chỉ trong kỳ năm; sửa `config/definitions.toml`, tăng `version`, cập nhật số trong `tests/test_po3.py`, ghi lý do trong commit.
