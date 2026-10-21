#!/usr/bin/env python3
"""Bar-by-bar port of Asia_H1_Breakout_v1.pine, checked against asia-h1-breakout_days.csv.

Usage: python3 verify_breakout_indicator.py <repo_root> <out_dir>

Chart bars (H1, M15) are resampled from the true-UTC M1 data (histdata timezone fix as in
asia_h1_breakout.py), then fed to the same state machine as the Pine script. Every signal must match the
statistics file (column p_brk: breakout candle opens 00:00-05:00; same side, same hour, same M15 FVG flag)
on the days the statistics keep.
Keep this file and the Pine script in sync.
"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asia_h1_breakout import load_true_utc, SYMS, TZ

HOUR = pd.Timedelta(hours=1)
ASIA_START_H, WIN_END_H = 20, 6

def chart_bars(m1, minutes):
    df = m1.set_index("t")[["open", "high", "low", "close"]]
    b = df.resample(f"{minutes}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    b["time_close"] = b.index + pd.Timedelta(minutes=minutes)
    return b

def fvg(side, mh, ml):
    """Pine f_fvg: M15 slots 0-1-2 or 1-2-3 of the hour; NaN (missing slot) compares False like Pine na."""
    if side > 0: return ml[2] > mh[0] or ml[3] > mh[1]
    return mh[2] < ml[0] or mh[3] < ml[1]

def run(bars, m15):
    """Mirror of the Pine script. m15 = M15 bars (on an M15 chart: the chart bars themselves).
    Returns {NY date of 00:00: (side, hour, fvg, late)}."""
    nan = float("nan")
    is_m15 = bars is m15
    by_hour = {}                                     # H1 chart: request.security_lower_tf("15") of each H1 bar
    if not is_m15:
        for tt, hh, ll in zip(m15.index, m15.high, m15.low): by_hour.setdefault(tt.floor("h"), []).append((tt, hh, ll))
    sig = {}
    a_hi = a_lo = day_00 = None
    done = True
    c_t = c_hi = c_lo = c_cl = None; c_ev = True
    mh, ml = [nan] * 4, [nan] * 4
    prev_t, prev_in_asia = None, False
    for t, o, h, l, c, tc in zip(bars.index, bars.open, bars.high, bars.low, bars.close, bars.time_close):
        ny = t.tz_convert(TZ)
        in_asia = ny.hour >= ASIA_START_H
        new_asia = in_asia and (not prev_in_asia or t - prev_t >= 12 * HOUR)
        if new_asia:
            d0 = (ny + pd.Timedelta(days=1)).normalize()           # NY wall-clock midnight of next day
            day_00 = d0.tz_convert("UTC")
            done = not (d0.weekday() < 5)
            a_hi, a_lo = h, l
            c_t, c_ev = None, True
        elif in_asia and a_hi is not None:
            a_hi, a_lo = max(a_hi, h), min(a_lo, l)
        evals = []
        tracking = (not done) and day_00 is not None and t >= day_00
        bucket = t.floor("h")
        if tracking:
            if c_t is None or bucket != c_t:            # Pine: na(c_t) or bucket != c_t
                if c_t is not None and not c_ev:         # late: last chart bar of the hour missing
                    evals.append((c_t, c_cl, fvg(1, mh, ml), fvg(-1, mh, ml), True))
                c_t, c_hi, c_lo, c_cl, c_ev = bucket, h, l, c, False
                mh, ml = [nan] * 4, [nan] * 4
            else:
                c_hi, c_lo, c_cl = max(c_hi, h), min(c_lo, l), c
            for tt, hh, ll in ([(t, h, l)] if is_m15 else by_hour.get(t, [])):
                j = (tt - c_t) // pd.Timedelta(minutes=15)
                if 0 <= j <= 3: mh[j], ml[j] = hh, ll
            if not c_ev and tc >= c_t + HOUR:
                c_ev = True
                evals.append((c_t, c_cl, fvg(1, mh, ml), fvg(-1, mh, ml), False))
        for ct, ccl, fu, fd, late in evals:
            if done: continue
            k = round((ct - day_00) / HOUR)
            side = 1 if ccl > a_hi else -1 if ccl < a_lo else 0
            if side != 0 or k >= WIN_END_H - 1: done = True
            if side != 0 and 0 <= k < WIN_END_H:
                sig[day_00.tz_convert(TZ).strftime("%Y-%m-%d")] = (side, k, bool(fu if side > 0 else fd), late)
        prev_t, prev_in_asia = t, in_asia
    return sig

def main():
    repo, od = sys.argv[1], sys.argv[2]
    ref = pd.read_csv(os.path.join(od, "asia-h1-breakout_days.csv"))
    O = ["# Đối chiếu indicator Asia_H1_Breakout_v1 với thống kê", "",
         "Port từng nến của Pine (`verify_breakout_indicator.py`) chạy trên nến chart dựng từ M1, so với `asia-h1-breakout_days.csv`.",
         "Chỉ so trên những ngày thống kê giữ lại (đủ dữ liệu). Khớp = cùng có/không tín hiệu (breakout 00:00–05:00), cùng hướng, cùng giờ nến, cùng có/không FVG M15.", "",
         "| symbol | khung chart | ngày so | tín hiệu thống kê | tín hiệu indicator | trong đó có FVG | lệch | xét muộn |", "|---|---|---|---|---|---|---|---|"]
    bad_all = 0
    for sym in SYMS:
        m1 = load_true_utc(os.path.join(repo, "data/m1", f"{sym}_M1_UTC.csv"))
        r = ref[ref.sym == sym].set_index("date")
        m15 = chart_bars(m1, 15)
        for tf in (60, 15):
            sig = run(chart_bars(m1, 60), m15) if tf == 60 else run(m15, m15)
            bad = []
            for dte, row in r.iterrows():
                exp = (int(row.side), int(row.brk_hour), bool(row.fvg)) if row.p_brk else None
                got = sig.get(dte); got2 = got[:3] if got else None
                if exp != got2: bad.append((dte, exp, got))
            late = sum(1 for d in r.index if d in sig and sig[d][3])
            bad_all += len(bad)
            O.append(f"| {sym} | {'H1' if tf == 60 else 'M15'} | {len(r)} | {int(r.p_brk.sum())} | "
                     f"{sum(1 for d in r.index if d in sig)} | {sum(1 for d in r.index if d in sig and sig[d][2])} | {len(bad)} | {late} |")
            for b in bad[:5]: O.append(f"|  | lệch: {b[0]} thống kê {b[1]} indicator {b[2]} | | | | | | |")
            print(sym, tf, "mismatch", len(bad), flush=True)
    O += ["", f"Tổng số ngày lệch: {bad_all}."]
    open(os.path.join(od, "verify_breakout_indicator.md"), "w").write("\n".join(O) + "\n"); print("\n".join(O))

if __name__ == "__main__":
    main()
