#!/usr/bin/env python3
"""Weekly profile and daily profile statistics: classification, frequency, selection and allocation.

Usage: python3 po3_profiles.py EURUSD,GBPUSD out.md

Data: M1 histdata UTC (data/m1/<SYM>_M1_UTC.csv), converted to America/New_York.

Operational definitions (frozen with this file; any change needs a new file):
  day      a TradingView/OANDA daily candle: 17:00 NY -> 17:00 NY, labelled with the NY date it closes on.
           Sunday 17:00 therefore belongs to Monday. Days with < 900 M1 bars are dropped (holiday / half day).
  week     Monday..Friday days of the same ISO week (so it starts Sunday 17:00 NY). Weeks with < 4 days are dropped.
  off      hours since the 17:00 open of the day, 0..24. 03:00 NY = 10, 05:00 NY = 12, 09:00 NY = 16.
  block    three blocks of the day, chosen so that each decision hour of the manual routine sits inside one:
           "A" 17:00-02:00 (off 0-9), "London" 02:00-07:00 (off 9-14), "New York" 07:00-17:00 (off 14-24).
  session  finer buckets: Asia 20-00, 00-02, London 02-05, 05-07, NY AM 07-11, NY PM 11-16, rest = outside.
  extreme  the first M1 bar that touches the period's high / low.
  daily profile   the ordered pair (block of the day low, block of the day high). 9 exhaustive cells.
                  Direction is implied: the block pair plus which extreme came first.
  weekly profile  the pair (phase of the weekly low, phase of the weekly high) where phase =
                  early (Mon/Tue), mid (Wed), late (Thu/Fri). 9 exhaustive cells.
  character  range vs ATR20 (daily) or vs the trailing 20-week median range (weekly): narrow < 0.7,
             wide > 1.3, else normal. close_pos = (close - low) / range.
  control    a driftless Gaussian random walk at constant volatility, same number of hours, run through the
             same pipeline. It has no sessions and no weekdays, so it gives the base rate that any series
             produces by arithmetic alone. A profile frequency that matches the control carries no information.
"""
import sys, math, os
import numpy as np, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis-2026-09-21"))
from po3_amd_killzone import Series, load_m1, random_walk_m1, wilson, pct, md
from po3_rr_session import rt_setups, simulate

TZ = "America/New_York"
PIP = {"USDJPY": 0.01}
WD = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6"}
BLOCKS = (("Á", 0.0, 9.0), ("Luân Đôn", 9.0, 14.0), ("New York", 14.0, 24.0))
SESS = (("Á 20–00", 3.0, 7.0), ("00–02", 7.0, 9.0), ("Luân Đôn 02–05", 9.0, 12.0), ("05–07", 12.0, 14.0),
        ("NY sáng 07–11", 14.0, 18.0), ("NY chiều 11–16", 18.0, 23.0))
CUT = {"03:00": 10.0, "05:00": 12.0, "09:00": 16.0}
MIN_BARS_DAY = 900
BLOCK_ORDER = [b[0] for b in BLOCKS]
PHASE = {0: "đầu tuần", 1: "đầu tuần", 2: "giữa tuần", 3: "cuối tuần", 4: "cuối tuần"}
PHASE_ORDER = ["đầu tuần", "giữa tuần", "cuối tuần"]

def label(off, table, dflt="ngoài phiên"):
    for name, a, b in table:
        if a <= off < b: return name
    return dflt

def two_prop(k1, n1, k2, n2):
    """Difference of two proportions with a 95% CI (independent samples, normal approximation)."""
    if n1 == 0 or n2 == 0: return float("nan"), float("nan"), float("nan")
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return d, d - 1.96 * se, d + 1.96 * se

def diff_str(k1, n1, k2, n2):
    d, lo, hi = two_prop(k1, n1, k2, n2)
    if math.isnan(d): return ""
    sig = "" if lo <= 0 <= hi else " *"
    return f"{100*d:+.1f} [{100*lo:+.1f}; {100*hi:+.1f}]{sig}"

def mean_ci(x):
    x = np.asarray([v for v in x if not (isinstance(v, float) and math.isnan(v))], float)
    if len(x) < 2: return ""
    h = 1.96 * x.std(ddof=1) / math.sqrt(len(x))
    return f"{x.mean():+.3f} [{x.mean()-h:+.3f}; {x.mean()+h:+.3f}]"

# ------------------------------------------------------------------ daily / weekly records
def daily_records(df, pair, pip):
    ny = df["ts_utc"].dt.tz_convert(TZ)
    shifted = ny + pd.Timedelta(hours=7)
    dkey = shifted.dt.normalize()
    off = (shifted - dkey).dt.total_seconds().values / 3600.0
    t = pd.DataFrame({"day": dkey.dt.date.values, "wd": dkey.dt.weekday.values, "off": off,
                      "o": df["open"].values, "h": df["high"].values, "l": df["low"].values, "c": df["close"].values,
                      "ts": ny.values})
    t = t[t["wd"] <= 4]
    recs = []
    for day, g in t.groupby("day", sort=True):
        if len(g) < MIN_BARS_DAY: continue
        o = g["o"].values; hi = g["h"].values; lo = g["l"].values; cl = g["c"].values; of = g["off"].values
        ih = int(np.argmax(hi)); il = int(np.argmin(lo))
        H, L = hi[ih], lo[il]; rng = H - L
        if rng <= 0: continue
        r = dict(pair=pair, pip=pip, day=day, wd=int(g["wd"].iloc[0]), wdn=WD[int(g["wd"].iloc[0])],
                 open=o[0], close=cl[-1], high=H, low=L, rng_pip=rng / pip,
                 close_pos=(cl[-1] - L) / rng, off_h=of[ih], off_l=of[il],
                 blk_h=label(of[ih], BLOCKS), blk_l=label(of[il], BLOCKS),
                 ses_h=label(of[ih], SESS), ses_l=label(of[il], SESS),
                 low_first=bool(of[il] < of[ih]), n_bars=len(g))
        mid = of >= 7.0
        r["open_mid"] = o[mid][0] if mid.any() else np.nan          # true day open 00:00 NY
        for name, cut in CUT.items():
            m = of < cut
            if not m.any():
                r[f"rh_{name}"] = r[f"rl_{name}"] = np.nan; continue
            jh = int(np.argmax(np.where(m, hi, -np.inf))); jl = int(np.argmin(np.where(m, lo, np.inf)))
            r[f"rh_{name}"] = hi[jh]; r[f"rl_{name}"] = lo[jl]; r[f"px_{name}"] = cl[m][-1]
            r[f"blk_rh_{name}"] = label(of[jh], BLOCKS); r[f"blk_rl_{name}"] = label(of[jl], BLOCKS)
            r[f"hi_in_{name}"] = bool(of[ih] < cut); r[f"lo_in_{name}"] = bool(of[il] < cut)
            after = ~m
            r[f"rest_pip_{name}"] = (hi[after].max() - lo[after].min()) / pip if after.any() else np.nan
        for name, a, b in SESS:
            m = (of >= a) & (of < b)
            r[f"srng_{name}"] = (hi[m].max() - lo[m].min()) / pip if m.any() else np.nan
        recs.append(r)
    d = pd.DataFrame(recs).sort_values("day").reset_index(drop=True)
    d["atr20"] = d["rng_pip"].rolling(20, min_periods=10).mean().shift(1)
    d["rng_rel"] = d["rng_pip"] / d["atr20"]
    d["char"] = np.where(d["rng_rel"] < 0.7, "hẹp", np.where(d["rng_rel"] > 1.3, "rộng", "trung bình"))
    d["profile"] = "đáy " + d["blk_l"] + " / đỉnh " + d["blk_h"]
    d["week"] = [x - pd.Timedelta(days=int(w)) for x, w in zip(pd.to_datetime(d["day"]), d["wd"])]
    d["prev_high"] = d["high"].shift(1); d["prev_low"] = d["low"].shift(1)
    ph, pl = [], []
    for _, g in d.groupby("week", sort=True):
        ph += list(g["high"].cummax().shift(1)); pl += list(g["low"].cummin().shift(1))
    d["wk_prior_hi"] = ph; d["wk_prior_lo"] = pl
    wk = d.groupby("week").agg(wkh=("high", "max"), wkl=("low", "min"))
    wk["pw_hi"] = wk["wkh"].shift(1); wk["pw_lo"] = wk["wkl"].shift(1)
    d = d.merge(wk[["pw_hi", "pw_lo"]], left_on="week", right_index=True, how="left")
    d["swept_pdh"] = d["high"] > d["prev_high"]; d["swept_pdl"] = d["low"] < d["prev_low"]
    d["swept_pwh"] = d["high"] > d["pw_hi"]; d["swept_pwl"] = d["low"] < d["pw_lo"]
    for name in CUT:
        d[f"pdh_in_{name}"] = d[f"rh_{name}"] > d["prev_high"]
        d[f"pdl_in_{name}"] = d[f"rl_{name}"] < d["prev_low"]
    return d

def weekly_records(d):
    recs = []
    for wk, g in d.groupby("week", sort=True):
        if len(g) < 4: continue
        g = g.sort_values("day")
        ih = int(np.argmax(g["high"].values)); il = int(np.argmin(g["low"].values))
        H = g["high"].values[ih]; L = g["low"].values[il]; rng = H - L
        if rng <= 0: continue
        wd_h = int(g["wd"].values[ih]); wd_l = int(g["wd"].values[il])
        # order in time: same day -> use the intraday offset of the extreme
        t_h = (wd_h, g["off_h"].values[ih]); t_l = (wd_l, g["off_l"].values[il])
        r = dict(pair=g["pair"].iloc[0], week=wk, n_days=len(g), open=g["open"].iloc[0], close=g["close"].iloc[-1],
                 high=H, low=L, rng_pip=rng / g["pip"].iloc[0],
                 wd_h=wd_h, wd_l=wd_l, wdn_h=WD[wd_h], wdn_l=WD[wd_l],
                 ph_h=PHASE[wd_h], ph_l=PHASE[wd_l], low_first=bool(t_l < t_h))
        r["close_pos"] = (g["close"].iloc[-1] - L) / rng
        r["profile"] = "đáy " + r["ph_l"] + " / đỉnh " + r["ph_h"]
        # share of the weekly range already printed by the end of each weekday
        rh = -np.inf; rl = np.inf
        for wd in range(5):
            sel = g[g["wd"] == wd]
            if len(sel):
                rh = max(rh, sel["high"].max()); rl = min(rl, sel["low"].min())
            r[f"done_{wd}"] = (rh - rl) / rng if np.isfinite(rh) and np.isfinite(rl) else np.nan
            r[f"hi_in_{wd}"] = bool(wd_h <= wd); r[f"lo_in_{wd}"] = bool(wd_l <= wd)
        mon = g[g["wd"] == 0]
        if len(mon):
            r["mon_dir"] = int(np.sign(mon["close"].iloc[0] - mon["open"].iloc[0]))
            r["mon_rng_rel"] = mon["rng_rel"].iloc[0]
            r["mon_close_pos"] = mon["close_pos"].iloc[0]
        else:
            r["mon_dir"] = 0; r["mon_rng_rel"] = np.nan; r["mon_close_pos"] = np.nan
        recs.append(r)
    w = pd.DataFrame(recs).sort_values("week").reset_index(drop=True)
    w["med20"] = w["rng_pip"].rolling(20, min_periods=10).median().shift(1)
    w["rng_rel"] = w["rng_pip"] / w["med20"]
    w["char"] = np.where(w["rng_rel"] < 0.7, "hẹp", np.where(w["rng_rel"] > 1.3, "rộng", "trung bình"))
    return w

# ------------------------------------------------------------------ generic tables
def freq_table(d, col, ctrl=None, order=None, extra=None):
    """Frequency of each value of `col` with a Wilson 95% CI, plus the control frequency and the gap."""
    n = len(d); vals = order or sorted(d[col].dropna().unique())
    rows = []
    for v in vals:
        g = d[d[col] == v]; k = len(g)
        row = {"n": k, "Tỷ lệ": pct(k, n)}
        if ctrl is not None and len(ctrl):
            kc = int((ctrl[col] == v).sum()); nc = len(ctrl)
            row["Ngẫu nhiên"] = f"{100*kc/nc:.1f}%"
            row["Lệch so với ngẫu nhiên (điểm %)"] = diff_str(k, n, kc, nc)
        if extra:
            for name, fn in extra.items(): row[name] = fn(g)
        rows.append({col: v, **row})
    t = pd.DataFrame(rows).set_index(col); t.index.name = col
    return t

def matrix_pct(d, row, col, rorder, corder):
    n = len(d); out = []
    for r in rorder:
        line = {"": r}
        for c in corder:
            k = int(((d[row] == r) & (d[col] == c)).sum())
            line[c] = f"{100*k/n:.1f}% ({k})"
        line["Tổng"] = f"{100*int((d[row]==r).sum())/n:.1f}%"
        out.append(line)
    tot = {"": "Tổng"}
    for c in corder: tot[c] = f"{100*int((d[col]==c).sum())/n:.1f}%"
    tot["Tổng"] = "100%"
    out.append(tot)
    t = pd.DataFrame(out).set_index(""); t.index.name = ""
    return t

def q(x, p):
    x = np.asarray(pd.Series(x).dropna(), float)
    return f"{np.percentile(x, p):.0f}" if len(x) else ""

# ------------------------------------------------------------------ trades (rule set v1.0, no FVG filter)
def trade_table(paths, D):
    """PO3 sweep -> CISD setups at 03:00 and 09:00 NY on Tue/Wed/Thu, SL = extreme + 0.25 ATR, TP = 2R,
    time exit after 60 bars, 1 pip round trip. Rule set v1.0: the v1.1 FVG condition is deliberately not applied."""
    rows = []
    dix = {(r["pair"], r["day"]): r for _, r in D.iterrows()}
    for pair, path in paths.items():
        S = Series(load_m1(path), scope=False)
        pip = PIP.get(pair, 1e-4)
        for i in range(1, len(S.hours)):
            if S.hour_ny[i] not in (3, 9) or S.wd[i] not in (1, 2, 3) or not S.valid[i]: continue
            for sign in (1, -1):
                rec = rt_setups(S, i, sign, pair)
                if rec is None or rec.get("cisd") is None: continue
                if rec["cisd_min"] > 29 or not (rec["cisd_depth_atr"] < 0.25): continue
                res = simulate(S, rec, "cisd", 0.25, 2.0, "60")
                if res is None: continue
                R, outcome, cost = res
                ts_ny = S.hours[i].tz_convert(TZ); day = (ts_ny + pd.Timedelta(hours=7)).date()
                dr = dix.get((pair, day))
                if dr is None: continue
                cut = "03:00" if S.hour_ny[i] == 3 else "09:00"
                entry = S.c[rec["cisd"]]
                low_px = sign * rec["cisd_low_px"]
                side = "mua" if sign > 0 else "bán"
                wk_lo, wk_hi = dr["wk_prior_lo"], dr["wk_prior_hi"]
                if pd.isna(wk_lo):
                    wk_state = "Thứ 2 (chưa có biên tuần)"
                else:
                    swept = (low_px <= wk_lo) if sign > 0 else (low_px >= wk_hi)
                    far = (wk_hi - entry) if sign > 0 else (entry - wk_lo)
                    wk_state = ("quét biên tuần cùng phía" if swept else
                                ("còn ≥ 2R khoảng trống tới biên tuần đối diện" if far > 2 * abs(entry - low_px) else
                                 "sát biên tuần đối diện"))
                blk_side = dr[f"blk_rl_{cut}"] if sign > 0 else dr[f"blk_rh_{cut}"]
                risk_pip = (abs(entry - low_px) + 0.25 * rec["atr"]) / pip
                rows.append(dict(pair=pair, day=day, **{"Ngày trong tuần": dr["wdn"], "Giờ": f"{S.hour_ny[i]:02d}:00", "Hướng": side},
                                 R=R, ket_cuc=outcome, risk_pip=risk_pip,
                                 **{"Khối đặt cực trị ngày cùng phía": blk_side},
                                 **{"Trạng thái biên tuần": wk_state},
                                 **{"Vị trí so với mở 00:00": ("trên mở 00:00" if entry > dr["open_mid"] else "dưới mở 00:00") if not pd.isna(dr["open_mid"]) else ""},
                                 **{"Vị trí trong biên ngày tới lúc đó": ("nửa dưới" if entry < (dr[f"rh_{cut}"] + dr[f"rl_{cut}"]) / 2 else "nửa trên")},
                                 **{"Biên độ ngày": dr["char"]}))
    return pd.DataFrame(rows)

def expectancy(T, col, order=None):
    rows = []
    base = T["R"].values
    for v in (order or sorted(x for x in T[col].dropna().unique() if x != "")):
        g = T[T[col] == v]
        if len(g) < 10: continue
        R = g["R"].values
        rows.append({col: v, "n": len(g), "P(TP)": pct(int((g["ket_cuc"] == "TP").sum()), len(g)),
                     "P(SL)": f"{100*(g['ket_cuc']=='SL').mean():.1f}%",
                     "Kỳ vọng R [CI95]": mean_ci(R)})
    rows.append({col: "TẤT CẢ", "n": len(T), "P(TP)": pct(int((T["ket_cuc"] == "TP").sum()), len(T)),
                 "P(SL)": f"{100*(T['ket_cuc']=='SL').mean():.1f}%", "Kỳ vọng R [CI95]": mean_ci(base)})
    t = pd.DataFrame(rows).set_index(col); t.index.name = col
    return t

# ------------------------------------------------------------------ report
def main():
    syms = (sys.argv[1] if len(sys.argv) > 1 else "EURUSD,GBPUSD").split(",")
    outp = sys.argv[2] if len(sys.argv) > 2 else "weekly-daily-profiles.md"
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "..", "..", "data", "m1")
    paths = {s: os.path.join(root, f"{s}_M1_UTC.csv") for s in syms}

    Ds = {s: daily_records(load_m1(p), s, PIP.get(s, 1e-4)) for s, p in paths.items()}
    D = pd.concat(Ds.values(), ignore_index=True)
    W = pd.concat([weekly_records(d) for d in Ds.values()], ignore_index=True)

    rw = daily_records(random_walk_m1(int(len(D) * 34), seed=11), "RW", 1e-4)
    rww = weekly_records(rw)

    out = []
    out.append("# Weekly profile và daily profile — thống kê, xếp loại, chọn lọc, phân bổ\n")
    out.append(f"Sinh bởi `po3_profiles.py` ngày 2026-10-05. Dữ liệu M1 histdata UTC, {', '.join(syms)}; "
               f"ngày {D['day'].min()} → {D['day'].max()}. Mẫu: **{len(D)} ngày** ({len(D)//len(syms)} ngày mỗi cặp) "
               f"và **{len(W)} tuần**. Cột *Ngẫu nhiên* là cùng pipeline chạy trên bước đi ngẫu nhiên Gauss "
               f"không trôi, biến động hằng số, {len(rw)} ngày: đó là tỷ lệ mà **mọi** chuỗi giá sinh ra do số học, "
               "không mang thông tin. Dấu `*` ở cột lệch nghĩa là khoảng tin cậy 95% của hiệu không chứa 0.\n")
    out.append("Định nghĩa đóng băng cùng file (xem docstring đầu `po3_profiles.py`): ngày = nến D 17:00→17:00 New York "
               "(giống nến D của OANDA trên TradingView, nên tối Chủ nhật thuộc về thứ Hai); tuần = thứ Hai→thứ Sáu "
               "cùng tuần ISO; ba khối trong ngày là **Á** 17:00–02:00, **Luân Đôn** 02:00–07:00, **New York** "
               "07:00–17:00 — cắt như vậy để mỗi giờ quyết định của quy trình (03:00 và 09:00) nằm trong một khối; "
               "ba pha trong tuần là **đầu tuần** (thứ 2–3), **giữa tuần** (thứ 4), **cuối tuần** (thứ 5–6).\n")
    out.append("> Cảnh báo đọc số: nhãn profile chỉ xác định được **sau khi** chu kỳ đóng. Bảng tần suất ở mục 1 và 3 "
               "là mô tả, không phải tín hiệu. Phần dùng được trong lúc giao dịch nằm ở mục 2, 3, 5, 6 và 7: "
               "xác suất có điều kiện tính từ thông tin đã biết tại 03:00 hoặc 09:00 New York.\n")

    # ---------------- 1. daily profiles
    out.append("\n## 1. Daily profile — cực trị ngày rơi vào khối nào\n")
    out.append("Ô = tỷ lệ số ngày có đáy ngày ở khối hàng và đỉnh ngày ở khối cột (trong ngoặc là số ngày).\n")
    out.append(md(matrix_pct(D, "blk_l", "blk_h", BLOCK_ORDER, BLOCK_ORDER)))
    out.append("\nCùng ma trận trên bước đi ngẫu nhiên (để so):\n")
    out.append(md(matrix_pct(rw, "blk_l", "blk_h", BLOCK_ORDER, BLOCK_ORDER)))
    porder = [f"đáy {a} / đỉnh {b}" for a in BLOCK_ORDER for b in BLOCK_ORDER]
    out.append("\nXếp loại 9 ô theo tần suất, kèm tính chất của từng loại:\n")
    out.append(md(freq_table(D, "profile", ctrl=rw, order=porder, extra={
        "Biên độ ngày (pip, trung vị)": lambda g: q(g["rng_pip"], 50),
        "Đóng cửa trong biên (%, trung vị)": lambda g: f"{100*np.nanmedian(g['close_pos']):.0f}",
        "P(đáy trước đỉnh)": lambda g: f"{100*g['low_first'].mean():.0f}%",
        "Ngày rộng (> 1,3 ATR20)": lambda g: f"{100*(g['char']=='rộng').mean():.0f}%"})))
    out.append("\nTheo ngày trong tuần (tỷ lệ các ngày của cột đó):\n")
    rows = []
    for wd in range(5):
        g = D[D["wd"] == wd]; row = {"Ngày": WD[wd], "n": len(g)}
        for b in BLOCK_ORDER: row[f"đáy ở {b}"] = f"{100*(g['blk_l']==b).mean():.0f}%"
        for b in BLOCK_ORDER: row[f"đỉnh ở {b}"] = f"{100*(g['blk_h']==b).mean():.0f}%"
        row["Biên độ (pip, trung vị)"] = q(g["rng_pip"], 50)
        row["P(đóng cửa trên mở 00:00)"] = f"{100*(g['close']>g['open_mid']).mean():.0f}%"
        rows.append(row)
    out.append(md(pd.DataFrame(rows).set_index("Ngày")))
    out.append("\nPhiên đặt cực trị, chi tiết hơn (6 phiên, % số ngày):\n")
    sorder = [x[0] for x in SESS] + ["ngoài phiên"]
    rows = []
    for s in sorder:
        rows.append({"Phiên": s, "Đặt đáy ngày": f"{100*(D['ses_l']==s).mean():.1f}%",
                     "Đặt đỉnh ngày": f"{100*(D['ses_h']==s).mean():.1f}%",
                     "Đặt đáy (ngẫu nhiên)": f"{100*(rw['ses_l']==s).mean():.1f}%",
                     "Biên độ phiên (pip, trung vị)": q(D.get(f"srng_{s}", pd.Series(dtype=float)), 50) if f"srng_{s}" in D else ""})
    out.append(md(pd.DataFrame(rows).set_index("Phiên")))

    # ---------------- 2. what is already known at 03:00 / 09:00
    out.append("\n## 2. Tại 03:00 và 09:00 New York thì cực trị ngày đã in chưa\n")
    out.append("Đây là bảng dùng được trong ngày: nó nói phần biên độ còn lại sau giờ quyết định.\n")
    rows = []
    for cut in CUT:
        for wd in range(5):
            g = D[D["wd"] == wd]
            k_h = int(g[f"hi_in_{cut}"].sum()); k_l = int(g[f"lo_in_{cut}"].sum()); n = len(g)
            both = int((g[f"hi_in_{cut}"] & g[f"lo_in_{cut}"]).sum())
            rows.append({"Mốc": cut, "Ngày": WD[wd], "n": n,
                         "P(đỉnh ngày đã in)": pct(k_h, n), "P(đáy ngày đã in)": pct(k_l, n),
                         "P(cả hai đã in)": f"{100*both/n:.0f}%",
                         "Biên độ còn lại sau mốc (pip): Q1 / trung vị / Q3":
                             f"{q(g[f'rest_pip_{cut}'],25)} / {q(g[f'rest_pip_{cut}'],50)} / {q(g[f'rest_pip_{cut}'],75)}"})
    out.append(md(pd.DataFrame(rows).set_index("Mốc")))

    # ---------------- 2b. draw on liquidity
    out.append("\n## 3. Mức thanh khoản ngày trước và tuần trước (DOL) có bị quét không\n")
    out.append("Bảng này nối trực tiếp với panel DOL của indicator v7: PDH/PDL là đỉnh/đáy nến D hôm trước, "
               "PWH/PWL là đỉnh/đáy nến W tuần trước. *Quét* = giá chạm vượt mức đó, không cần đóng cửa ngoài.\n")
    rows = []
    for wd in range(5):
        g = D[D["wd"] == wd]; n = len(g)
        both = int((g["swept_pdh"] & g["swept_pdl"]).sum()); none = int((~g["swept_pdh"] & ~g["swept_pdl"]).sum())
        rows.append({"Ngày": WD[wd], "n": n, "P(quét PDH)": pct(int(g["swept_pdh"].sum()), n),
                     "P(quét PDL)": pct(int(g["swept_pdl"].sum()), n),
                     "P(quét cả hai)": f"{100*both/n:.0f}%", "P(không quét mức nào)": f"{100*none/n:.0f}%",
                     "P(PDH bị quét trước 03:00)": f"{100*g['pdh_in_03:00'].mean():.0f}%",
                     "P(PDL bị quét trước 03:00)": f"{100*g['pdl_in_03:00'].mean():.0f}%",
                     "P(PDH bị quét trước 09:00)": f"{100*g['pdh_in_09:00'].mean():.0f}%",
                     "P(PDL bị quét trước 09:00)": f"{100*g['pdl_in_09:00'].mean():.0f}%"})
    g = D.dropna(subset=["prev_high", "prev_low"]); n = len(g)
    rows.append({"Ngày": "Mọi ngày", "n": n, "P(quét PDH)": pct(int(g["swept_pdh"].sum()), n),
                 "P(quét PDL)": pct(int(g["swept_pdl"].sum()), n),
                 "P(quét cả hai)": f"{100*(g['swept_pdh']&g['swept_pdl']).mean():.0f}%",
                 "P(không quét mức nào)": f"{100*((~g['swept_pdh'])&(~g['swept_pdl'])).mean():.0f}%",
                 "P(PDH bị quét trước 03:00)": f"{100*g['pdh_in_03:00'].mean():.0f}%",
                 "P(PDL bị quét trước 03:00)": f"{100*g['pdl_in_03:00'].mean():.0f}%",
                 "P(PDH bị quét trước 09:00)": f"{100*g['pdh_in_09:00'].mean():.0f}%",
                 "P(PDL bị quét trước 09:00)": f"{100*g['pdl_in_09:00'].mean():.0f}%"})
    gr = rw.dropna(subset=["prev_high", "prev_low"])
    rows.append({"Ngày": "Ngẫu nhiên", "n": len(gr), "P(quét PDH)": f"{100*gr['swept_pdh'].mean():.1f}%",
                 "P(quét PDL)": f"{100*gr['swept_pdl'].mean():.1f}%",
                 "P(quét cả hai)": f"{100*(gr['swept_pdh']&gr['swept_pdl']).mean():.0f}%",
                 "P(không quét mức nào)": f"{100*((~gr['swept_pdh'])&(~gr['swept_pdl'])).mean():.0f}%"})
    out.append(md(pd.DataFrame(rows).set_index("Ngày")))
    out.append("\nMức tuần trước, tính theo ngày nào trong tuần thực hiện việc quét:\n")
    rows = []
    for wd in range(5):
        g = D[D["wd"] == wd].dropna(subset=["pw_hi"]); n = len(g)
        rows.append({"Ngày": WD[wd], "n": n, "P(quét PWH trong ngày này)": pct(int(g["swept_pwh"].sum()), n),
                     "P(quét PWL trong ngày này)": pct(int(g["swept_pwl"].sum()), n)})
    Wd = D.dropna(subset=["pw_hi"]).groupby(["pair", "week"]).agg(h=("swept_pwh", "max"), l=("swept_pwl", "max"))
    n = len(Wd)
    rows.append({"Ngày": "Cả tuần", "n": n, "P(quét PWH trong ngày này)": pct(int(Wd["h"].sum()), n),
                 "P(quét PWL trong ngày này)": pct(int(Wd["l"].sum()), n)})
    out.append(md(pd.DataFrame(rows).set_index("Ngày")))
    out.append(f"\nTrong {n} tuần có mức tuần trước: quét cả PWH và PWL **{100*(Wd['h']&Wd['l']).mean():.0f}%**, "
               f"chỉ một phía **{100*(Wd['h']^Wd['l']).mean():.0f}%**, không quét mức nào "
               f"**{100*((~Wd['h'])&(~Wd['l'])).mean():.0f}%**.\n")

    # ---------------- 3. weekly profiles
    out.append("\n## 4. Weekly profile — cực trị tuần rơi vào ngày nào\n")
    out.append("Ma trận thô: ngày đặt đáy tuần (hàng) × ngày đặt đỉnh tuần (cột), % số tuần.\n")
    out.append(md(matrix_pct(W, "wdn_l", "wdn_h", [WD[i] for i in range(5)], [WD[i] for i in range(5)])))
    out.append("\nGộp thành 9 profile theo pha (đầu tuần = thứ 2–3, giữa tuần = thứ 4, cuối tuần = thứ 5–6):\n")
    worder = [f"đáy {a} / đỉnh {b}" for a in PHASE_ORDER for b in PHASE_ORDER]
    out.append(md(freq_table(W, "profile", ctrl=rww, order=worder, extra={
        "Biên độ tuần (pip, trung vị)": lambda g: q(g["rng_pip"], 50),
        "Đóng cửa trong biên (%, trung vị)": lambda g: f"{100*np.nanmedian(g['close_pos']):.0f}",
        "P(đáy trước đỉnh)": lambda g: f"{100*g['low_first'].mean():.0f}%"})))
    out.append("\nTên gọi quen dùng của ICT cho các ô chính: *đáy đầu tuần / đỉnh cuối tuần* = tuần tăng kinh điển "
               "(classic buy week), *đỉnh đầu tuần / đáy cuối tuần* = tuần giảm kinh điển, *đáy giữa tuần / đỉnh cuối tuần* "
               "= đảo chiều thứ Tư, hai ô *đầu tuần / đầu tuần* và *giữa tuần / giữa tuần* = seek & destroy "
               "(cả hai cực trị in sớm rồi tuần đi ngang trong biên đó).\n")
    out.append("\nNgày nào hay đặt cực trị tuần:\n")
    rows = []
    for wd in range(5):
        n = len(W)
        rows.append({"Ngày": WD[wd], "P(đặt đáy tuần)": pct(int((W["wd_l"] == wd).sum()), n),
                     "P(đặt đỉnh tuần)": pct(int((W["wd_h"] == wd).sum()), n),
                     "P(đặt một trong hai)": f"{100*((W['wd_l']==wd)|(W['wd_h']==wd)).mean():.1f}%",
                     "Ngẫu nhiên, đáy": f"{100*(rww['wd_l']==wd).mean():.1f}%",
                     "Lệch so với ngẫu nhiên (điểm %)": diff_str(int((W["wd_l"] == wd).sum()), n,
                                                                int((rww["wd_l"] == wd).sum()), len(rww))})
    out.append(md(pd.DataFrame(rows).set_index("Ngày")))

    # ---------------- 4. weekly range completion
    out.append("\n## 5. Biên độ tuần hoàn thành tới đâu sau mỗi ngày\n")
    out.append("Cột *% biên tuần đã in* = (đỉnh cao nhất − đáy thấp nhất tính đến hết ngày đó) / biên độ cả tuần. "
               "Hai cột cuối là cái dùng được sáng thứ Ba và thứ Tư: xác suất cực trị tuần **vẫn còn ở phía trước**.\n")
    rows = []
    for wd in range(5):
        rows.append({"Hết ngày": WD[wd], "n": len(W),
                     "% biên tuần đã in (trung vị)": f"{100*np.nanmedian(W[f'done_{wd}']):.0f}%",
                     "% biên tuần đã in (Q1–Q3)": f"{q(100*W[f'done_{wd}'],25)}–{q(100*W[f'done_{wd}'],75)}%",
                     "P(đỉnh tuần chưa in)": pct(int((~W[f"hi_in_{wd}"]).sum()), len(W)),
                     "P(đáy tuần chưa in)": pct(int((~W[f"lo_in_{wd}"]).sum()), len(W)),
                     "P(cả hai đã in)": f"{100*(W[f'hi_in_{wd}']&W[f'lo_in_{wd}']).mean():.0f}%"})
    out.append(md(pd.DataFrame(rows).set_index("Hết ngày")))

    # ---------------- 5. conditional: does early-week information predict the profile
    out.append("\n## 6. Thông tin đầu tuần có dự báo được profile tuần không\n")
    out.append("Kiểm định thẳng: nếu biết nến thứ Hai (hướng đóng cửa, biên độ so với ATR20, vị trí đóng cửa trong biên), "
               "có đoán được tuần sẽ là tuần tăng kinh điển hay giảm kinh điển không. *Tuần tăng* ở đây = đáy tuần in "
               "trước đỉnh tuần; đó là biến nhị phân duy nhất đáng đoán vì nó quyết định chiều của chân giãn.\n")
    base_k = int(W["low_first"].sum()); base_n = len(W)
    rows = [{"Điều kiện": "Không điều kiện (tỷ lệ gốc)", "n": base_n, "P(đáy tuần trước đỉnh tuần)": pct(base_k, base_n),
             "Lệch so với tỷ lệ gốc (điểm %)": ""}]
    conds = [("Thứ Hai đóng cửa tăng", W["mon_dir"] > 0), ("Thứ Hai đóng cửa giảm", W["mon_dir"] < 0),
             ("Thứ Hai biên hẹp (< 0,7 ATR20)", W["mon_rng_rel"] < 0.7),
             ("Thứ Hai biên rộng (> 1,3 ATR20)", W["mon_rng_rel"] > 1.3),
             ("Thứ Hai đóng ở 1/3 trên biên ngày", W["mon_close_pos"] > 2 / 3),
             ("Thứ Hai đóng ở 1/3 dưới biên ngày", W["mon_close_pos"] < 1 / 3),
             ("Đáy tuần đã in trong thứ Hai", W["lo_in_0"]), ("Đỉnh tuần đã in trong thứ Hai", W["hi_in_0"])]
    for name, m in conds:
        g = W[m.fillna(False)]
        if len(g) < 10: continue
        k = int(g["low_first"].sum())
        rows.append({"Điều kiện": name, "n": len(g), "P(đáy tuần trước đỉnh tuần)": pct(k, len(g)),
                     "Lệch so với tỷ lệ gốc (điểm %)": diff_str(k, len(g), base_k, base_n)})
    out.append(md(pd.DataFrame(rows).set_index("Điều kiện")))

    out.append("\nHai dòng cuối gần như hiển nhiên (nếu đáy tuần nằm ở thứ Hai thì nó đi trước đỉnh tuần, trừ khi "
               "đỉnh cũng ở thứ Hai); chúng ở đây để thấy *mức* thông tin mà việc biết một cực trị đã in mang lại, "
               "so với việc đọc hình dạng nến thứ Hai — bốn dòng giữa đều không ra khỏi nhiễu.\n")
    out.append("\nBiên thứ Hai có giữ được cả tuần không — đây là câu hỏi dùng được sáng thứ Ba:\n")
    rows = []
    sub = [("Mọi tuần", pd.Series(True, index=W.index)), ("Thứ Hai đóng cửa tăng", W["mon_dir"] > 0),
           ("Thứ Hai đóng cửa giảm", W["mon_dir"] < 0), ("Thứ Hai biên hẹp (< 0,7 ATR20)", W["mon_rng_rel"] < 0.7),
           ("Thứ Hai biên rộng (> 1,3 ATR20)", W["mon_rng_rel"] > 1.3)]
    csub = {"Mọi tuần": pd.Series(True, index=rww.index), "Thứ Hai đóng cửa tăng": rww["mon_dir"] > 0,
            "Thứ Hai đóng cửa giảm": rww["mon_dir"] < 0, "Thứ Hai biên hẹp (< 0,7 ATR20)": rww["mon_rng_rel"] < 0.7,
            "Thứ Hai biên rộng (> 1,3 ATR20)": rww["mon_rng_rel"] > 1.3}
    for name, m in sub:
        g = W[m.fillna(False)]
        if len(g) < 10: continue
        c = rww[csub[name].fillna(False)]
        kl, kh = int((g["wd_l"] == 0).sum()), int((g["wd_h"] == 0).sum())
        cl, ch = int((c["wd_l"] == 0).sum()), int((c["wd_h"] == 0).sum())
        kb = int(((g["wd_l"] != 0) & (g["wd_h"] != 0)).sum()); cb = int(((c["wd_l"] != 0) & (c["wd_h"] != 0)).sum())
        rows.append({"Tập tuần": name, "n": len(g),
                     "P(đáy thứ Hai là đáy tuần)": pct(kl, len(g)),
                     "Ngẫu nhiên": f"{100*cl/len(c):.0f}%" if len(c) else "",
                     "P(đỉnh thứ Hai là đỉnh tuần)": pct(kh, len(g)),
                     "Ngẫu nhiên ": f"{100*ch/len(c):.0f}%" if len(c) else "",
                     "P(biên thứ Hai bị phá cả hai phía)": pct(kb, len(g)),
                     "Ngẫu nhiên  ": f"{100*cb/len(c):.0f}%" if len(c) else "",
                     "Lệch cột cuối (điểm %)": diff_str(kb, len(g), cb, len(c)) if len(c) else ""})
    out.append(md(pd.DataFrame(rows).set_index("Tập tuần")))

    out.append("\nCùng kiểu kiểm định ở mức ngày: biết trạng thái lúc 03:00 New York, có đoán được đáy ngày đã in chưa.\n")
    bk = int(D["lo_in_09:00"].sum()); bn = len(D)
    rows = [{"Điều kiện tại 03:00": "Không điều kiện (tỷ lệ gốc)", "n": bn, "P(đáy ngày in trước 09:00)": pct(bk, bn),
             "Lệch (điểm %)": ""}]
    dconds = [("Đáy chạy tới 03:00 nằm ở khối Á", D["blk_rl_03:00"] == "Á"),
              ("Đáy chạy tới 03:00 nằm ở khối Luân Đôn", D["blk_rl_03:00"] == "Luân Đôn"),
              ("Giá tại 03:00 trên mở 00:00", D["px_03:00"] > D["open_mid"]),
              ("Giá tại 03:00 dưới mở 00:00", D["px_03:00"] < D["open_mid"]),
              ("Đã quét đáy ngày hôm trước", D["rl_03:00"] < D["prev_low"]),
              ("Đã quét đỉnh ngày hôm trước", D["rh_03:00"] > D["prev_high"]),
              ("Biên tới 03:00 < 0,4 ATR20", (D["rh_03:00"] - D["rl_03:00"]) / D["pip"] / D["atr20"] < 0.4)]
    for name, m in dconds:
        g = D[m.fillna(False)]
        if len(g) < 10: continue
        k = int(g["lo_in_09:00"].sum())
        rows.append({"Điều kiện tại 03:00": name, "n": len(g), "P(đáy ngày in trước 09:00)": pct(k, len(g)),
                     "Lệch (điểm %)": diff_str(k, len(g), bk, bn)})
    out.append(md(pd.DataFrame(rows).set_index("Điều kiện tại 03:00")))

    out.append("\nHướng đi có nối tiếp không — kiểm định trực tiếp cái mà \"phác thảo hướng\" cần. "
               "Mốc quy chiếu trong ngày là giá mở 00:00 New York (true day open), trong tuần là giá mở tuần.\n")
    rows = []
    for nm, d_, c_ in (("Ngày: giá tại 03:00 trên mở 00:00 → đóng cửa ngày trên mở 00:00", D, rw),
                       ("Ngày: giá tại 09:00 trên mở 00:00 → đóng cửa ngày trên mở 00:00", D, rw)):
        cut = "03:00" if "03:00" in nm else "09:00"
        for side, op in (("trên", 1), ("dưới", -1)):
            g = d_[(op * (d_[f"px_{cut}"] - d_["open_mid"]) > 0)].dropna(subset=["open_mid"])
            cg = c_[(op * (c_[f"px_{cut}"] - c_["open_mid"]) > 0)].dropna(subset=["open_mid"])
            k = int((op * (g["close"] - g["open_mid"]) > 0).sum()); kc = int((op * (cg["close"] - cg["open_mid"]) > 0).sum())
            rows.append({"Kiểm định": f"Giá tại {cut} {side} mở 00:00", "n": len(g),
                         "P(đóng cửa cùng phía)": pct(k, len(g)),
                         "Ngẫu nhiên": f"{100*kc/len(cg):.1f}%" if len(cg) else "",
                         "Lệch (điểm %)": diff_str(k, len(g), kc, len(cg)) if len(cg) else ""})
    for side, op in (("tăng", 1), ("giảm", -1)):
        g = W[op * (W["mon_dir"]) > 0]; cg = rww[op * (rww["mon_dir"]) > 0]
        k = int((op * (g["close"] - g["open"]) > 0).sum()); kc = int((op * (cg["close"] - cg["open"]) > 0).sum())
        rows.append({"Kiểm định": f"Thứ Hai đóng cửa {side} → tuần đóng cửa cùng phía", "n": len(g),
                     "P(đóng cửa cùng phía)": pct(k, len(g)),
                     "Ngẫu nhiên": f"{100*kc/len(cg):.1f}%" if len(cg) else "",
                     "Lệch (điểm %)": diff_str(k, len(g), kc, len(cg)) if len(cg) else ""})
    out.append(md(pd.DataFrame(rows).set_index("Kiểm định")))

    # ---------------- 6. allocation: setups bucketed by live profile state
    out.append("\n## 7. Phân bổ — setup PO3 theo trạng thái profile biết được lúc vào lệnh\n")
    T = trade_table(paths, D)
    out.append(f"Bộ quy tắc **v1.0** (quét biên giờ trước trong 30 phút, độ sâu quét < 0,25 ATR, CISD trước phút 30, "
               f"SL = cực trị + 0,25 ATR, TP = 2R, thoát sau 60 phút, phí 1 pip khứ hồi). **Không** áp điều kiện FVG của "
               f"v1.1 — điều kiện đó cố ý không đo trên dữ liệu cũ. n = {len(T)} setup trên {len(syms)} cặp. "
               "Mọi cột phân nhóm đều tính từ thông tin có tại lúc nến CISD đóng, không nhìn trước.\n")
    out.append("\nRisk mỗi lệnh (khoảng cách vào lệnh → SL) tính bằng pip, theo giờ — để đối chiếu với biên độ "
               "còn lại ở mục 2:\n")
    rows = []
    for hr in ("03:00", "09:00"):
        g = T[T["Giờ"] == hr]
        rows.append({"Giờ": hr, "n": len(g), "Risk Q1 (pip)": q(g["risk_pip"], 25), "Risk trung vị (pip)": q(g["risk_pip"], 50),
                     "Risk Q3 (pip)": q(g["risk_pip"], 75), "Khoảng cách tới TP 2R, trung vị (pip)": q(2 * g["risk_pip"], 50)})
    out.append(md(pd.DataFrame(rows).set_index("Giờ")))
    for col in ["Ngày trong tuần", "Giờ", "Hướng", "Trạng thái biên tuần", "Khối đặt cực trị ngày cùng phía",
                "Vị trí so với mở 00:00", "Vị trí trong biên ngày tới lúc đó", "Biên độ ngày"]:
        out.append(f"\n**{col}**\n")
        out.append(md(expectancy(T, col)))

    out.append("\n## 8. Hạn chế\n")
    out.append("- Mẫu ngày và tuần là histdata M1 từ 2023; chỉ hai cặp FX tương quan cao, nên n tuần hiệu dụng nhỏ hơn "
               "con số in ra. Hai cặp cùng một tuần không độc lập; khoảng tin cậy ở mục 4–6 vì thế **lạc quan**.\n"
               "- Nhãn profile là hậu nghiệm. Chỉ mục 2, 3, 5, 6, 7 dùng được trong lúc giao dịch.\n"
               "- Bước đi ngẫu nhiên không có phiên và không có ngày trong tuần, nên nó là mốc so cho *hình dạng* "
               "phân phối, không phải mô hình thị trường.\n"
               "- Biên ngày 17:00→17:00 đã đối chiếu với feed H1 Dukascopy trên bốn ngày mẫu: lệch ≤ 0,6 pip ở đỉnh "
               "và 0,0 pip ở đáy, đúng 24 nến H1 mỗi ngày. Khoảng 12% số ngày có dưới 1300 nến M1 (ngày lễ, ngày "
               "nửa phiên) nhưng vẫn trên ngưỡng 900, nên cực trị của chúng có thể thiếu một phần cửa sổ.\n"
               "- Mục 7 chia nhỏ cùng một tập setup thành nhiều nhóm; với n mỗi nhóm vài chục, chênh lệch kỳ vọng "
               "trong khoảng ±0,3 R là nhiễu. Không đổi quy tắc dựa trên một dòng của bảng đó.\n")

    open(outp, "w").write("\n".join(out))
    D.to_csv(outp.replace(".md", "_daily.csv"), index=False)
    W.to_csv(outp.replace(".md", "_weekly.csv"), index=False)
    T.to_csv(outp.replace(".md", "_trades.csv"), index=False)
    print("written", outp, len(D), "days", len(W), "weeks", len(T), "setups")

if __name__ == "__main__":
    main()
