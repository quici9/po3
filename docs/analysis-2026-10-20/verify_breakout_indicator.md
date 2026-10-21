# Đối chiếu indicator Asia_H1_Breakout_v1 với thống kê

Port từng nến của Pine (`verify_breakout_indicator.py`) chạy trên nến chart dựng từ M1, so với `asia-h1-breakout_days.csv`.
Chỉ so trên những ngày thống kê giữ lại (đủ dữ liệu). Khớp = cùng có/không tín hiệu (breakout 00:00–05:00), cùng hướng, cùng giờ nến, cùng có/không FVG M15.

| symbol | khung chart | ngày so | tín hiệu thống kê | tín hiệu indicator | trong đó có FVG | lệch | xét muộn |
|---|---|---|---|---|---|---|---|
| EURUSD | H1 | 844 | 743 | 743 | 380 | 0 | 0 |
| EURUSD | M15 | 844 | 743 | 743 | 380 | 0 | 0 |
| XAUUSD | H1 | 838 | 638 | 638 | 362 | 0 | 0 |
| XAUUSD | M15 | 838 | 638 | 638 | 362 | 0 | 0 |
| NSXUSD | H1 | 833 | 709 | 709 | 403 | 0 | 0 |
| NSXUSD | M15 | 833 | 709 | 709 | 403 | 0 | 0 |

Tổng số ngày lệch: 0.
