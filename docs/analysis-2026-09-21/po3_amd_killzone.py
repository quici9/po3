#!/usr/bin/env python3
"""AMD phase timing, expansion window and FVG-retrace statistics on H1 candles, restricted to the
London (02-04 NY) and NY AM (08-10 NY) killzones on Tue/Wed/Thu. FX histdata M1, UTC.

Usage: python3 po3_amd_killzone.py EURUSD,GBPUSD,USDJPY out.md

Operational definitions (bullish wording; bearish candles are handled by price negation):
  directional H1: body/range >= 0.5.   manipulation wick: open-side wick/range >= 0.05
  t_m  minute of the counter-direction extreme (first M1 touching the H1 low)
  t_a  accumulation end: first minute price leaves the band open +/- BAND_ATR*ATR24
  MSS  first M1 close above the last fractal swing high (1 left / 1 right) printed before the low
  CISD first M1 close above the open of the last run of consecutive bearish M1 bars leading into the low
  FVG  first 3-bar gap (low[i+1] > high[i-1]) inside the leg low -> MSS bar (+1 bar)
  t_d  minute of the with-trend extreme (first M1 touching the H1 high)
  phases per minute: A [0, min(t_a,t_m))  M [min(t_a,t_m), t_m]  R (t_m, t_mss)  D [t_mss, t_d]  done (t_d, 59]
Real-time variant: sweep of the previous hour's low within the first SWEEP_MAX_MIN minutes, then MSS as above
(running low, swing high looked up to 60 bars back across the hour boundary); no knowledge of how the H1 closes.
"""
import sys, math
import numpy as np, pandas as pd

TZ = "America/New_York"
KZ = {2: "London", 3: "London", 4: "London", 8: "NY_AM", 9: "NY_AM", 10: "NY_AM"}
WDS = {1: "Tue", 2: "Wed", 3: "Thu"}
BAND_ATR = 0.15
R_DIR = 0.5
WICK_MIN = 0.05
WIN = 60
SWEEP_MAX_MIN = 30
BINS5 = [(a, a + 4) for a in range(0, 60, 5)]

# ------------------------------------------------------------------ helpers
def wilson(k, n, z=1.96):
    if n == 0: return float("nan"), float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h

def pct(k, n):
    p, lo, hi = wilson(k, n)
    return f"{100*p:.1f}% [{100*lo:.1f}–{100*hi:.1f}]"

def md(df):
    cols = [str(df.index.name or "")] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        lines.append("| " + " | ".join([str(idx)] + ["" if (isinstance(v, float) and math.isnan(v)) else str(v) for v in row.values]) + " |")
    return "\n".join(lines)

# ------------------------------------------------------------------ loading
def load_m1(path):
    df = pd.read_csv(path, parse_dates=["ts_utc"])
    df["ts_utc"] = df["ts_utc"].dt.tz_localize("UTC")
    return df.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)

def random_walk_m1(n_hours, seed=7, sub=6):
    """Continuous Gaussian random walk, `sub` sub-steps per minute, aggregated to M1 OHLC."""
    rng = np.random.default_rng(seed)
    n = n_hours * 60
    steps = rng.standard_normal((n, sub)) * 1e-4
    path = np.cumsum(steps.ravel()).reshape(n, sub) + 1.0
    o = np.r_[1.0, path[:-1, -1]]
    h = np.maximum(path.max(axis=1), o); l = np.minimum(path.min(axis=1), o); c = path[:, -1]
    ts = pd.date_range("2030-01-01", periods=n, freq="1min", tz="UTC")
    return pd.DataFrame({"ts_utc": ts, "open": o, "high": h, "low": l, "close": c, "volume": 0.0})

class Series:
    """M1 arrays plus per-hour index. Hours with < 30 bars are dropped from H1 stats but their bars stay."""
    def __init__(self, df, scope=True):
        self.o = df["open"].values.astype(float); self.h = df["high"].values.astype(float)
        self.l = df["low"].values.astype(float); self.c = df["close"].values.astype(float)
        ts = df["ts_utc"]
        self.minute = ts.dt.minute.values
        hk = ts.dt.floor("1h").values
        hours, starts = np.unique(hk, return_index=True)
        self.hours = pd.DatetimeIndex(hours, tz="UTC"); self.s = starts; self.e = np.r_[starts[1:], len(df)]
        self.n_m1 = self.e - self.s
        ny = self.hours.tz_convert(TZ)
        self.hour_ny = ny.hour.values; self.wd = ny.weekday.values; self.date_ny = ny.date
        self.H1o = self.o[self.s]; self.H1c = self.c[self.e - 1]
        self.H1h = np.maximum.reduceat(self.h, self.s); self.H1l = np.minimum.reduceat(self.l, self.s)
        self.valid = self.n_m1 >= 30
        rng = np.where(self.valid, self.H1h - self.H1l, np.nan)
        self.atr = pd.Series(rng).rolling(24, min_periods=12).mean().shift(1).values
        prev_adjacent = np.r_[False, (self.hours[1:] - self.hours[:-1]) == pd.Timedelta("1h")]
        self.prev_ok = prev_adjacent & np.r_[False, self.valid[:-1]]
        if scope:
            self.in_scope = np.isin(self.hour_ny, list(KZ)) & np.isin(self.wd, list(WDS))
        else:
            self.in_scope = np.ones(len(self.hours), bool)
        self.kz = np.array([KZ.get(x, "other") for x in self.hour_ny]); self.wdn = np.array([WDS.get(x, "other") for x in self.wd])

    def view(self, sign):
        """Bullish-oriented arrays: sign=+1 as is, sign=-1 negated (high<->low swapped). Cached."""
        if sign > 0: return self.o, self.h, self.l, self.c
        if not hasattr(self, "_neg"): self._neg = (-self.o, -self.l, -self.h, -self.c)
        return self._neg

# ------------------------------------------------------------------ structure primitives (bullish wording)
def swing_high_level(h, lo_idx, start):
    for k in range(lo_idx - 1, start, -1):
        if h[k] > h[k - 1] and h[k] > h[k + 1]: return h[k]
    if lo_idx > start: return h[start:lo_idx].max()
    return None

def cisd_level(o, c, lo_idx, start):
    k = lo_idx
    if not c[k] < o[k]: k -= 1
    if k < start or not c[k] < o[k]: return o[lo_idx]
    while k - 1 >= start and c[k - 1] < o[k - 1]: k -= 1
    return o[k]

def first_close_above(c, level, a, b):
    for j in range(a, b):
        if c[j] > level: return j
    return None

def first_fvg(h, l, a, b, N):
    """First bullish FVG with bars (i-1, i, i+1), a <= i-1, i+1 <= b. Returns (idx_formed, bottom, top)."""
    for i in range(a + 1, min(b, N - 1)):
        if l[i + 1] > h[i - 1]: return i + 1, h[i - 1], l[i + 1]
    return None

def follow_through(h, l, c, lo_idx, conf_idx, fvg, end, targets=None):
    """Events after confirmation, scanned in [start, end). Returns dict of first-event indices and depth.
    targets: {name: level}; event name -> first bar whose high >= level. 'ext1' = ref_hi + 1 leg is always added."""
    ref_hi = h[lo_idx:conf_idx + 1].max(); start = conf_idx + 1
    if fvg is not None:
        idx_f, bot, top = fvg
        ref_hi = max(ref_hi, h[lo_idx:idx_f + 1].max()); start = max(start, idx_f + 1)
    leg = ref_hi - l[lo_idx]
    tg = dict(targets or {}); tg["ext1"] = ref_hi + leg
    ev = dict(returned=None, ce=None, invalid=None, swept=None, cont=None, **{k: None for k in tg})
    minlow = np.inf
    for j in range(start, end):
        if fvg is not None:
            if ev["returned"] is None and l[j] <= top: ev["returned"] = j
            if ev["ce"] is None and l[j] <= (top + bot) / 2: ev["ce"] = j
            if ev["invalid"] is None and c[j] < bot: ev["invalid"] = j
        if ev["swept"] is None and l[j] < l[lo_idx]: ev["swept"] = j
        for k, lv in tg.items():
            if ev[k] is None and h[j] >= lv: ev[k] = j
        if ev["cont"] is None:
            minlow = min(minlow, l[j])
            if h[j] > ref_hi: ev["cont"] = j
    ev["depth"] = (ref_hi - minlow) / leg if (leg > 0 and np.isfinite(minlow)) else np.nan
    ev["ref_hi"] = ref_hi
    return ev

def race(ev, good, bad="swept"):
    """Which came first in the window: `good` target, `bad` (manipulation low taken), or neither."""
    g, b = ev.get(good), ev.get(bad)
    if g is not None and (b is None or g < b): return "target"
    if b is not None: return "fail"
    return "neither"

def before(ev, key, *decisive):
    """True if event `key` happened before the earliest of the decisive events (or at all if none happened)."""
    k = ev.get(key)
    if k is None: return False
    d = [ev[x] for x in decisive if ev.get(x) is not None]
    return (not d) or k < min(d)

def classify(fvg, ev):
    if fvg is None:
        return "noFVG_cont" if ev["cont"] is not None else "noFVG_stall"
    r, k = ev["returned"], ev["cont"]
    if r is not None and (k is None or r <= k):
        return "retrace_cont" if k is not None else "retrace_fail"
    if k is not None: return "cont_no_retrace"
    return "stall"

# ------------------------------------------------------------------ per-hour analyses
def h1_conditional(S, i, sign):
    """PO3 phases for a directional H1 candle i, oriented by sign. Returns record or None."""
    o, h, l, c = S.view(sign); s, e = S.s[i], S.e[i]; N = len(o)
    O = o[s]; H = h[s:e].max(); L = l[s:e].min(); C = c[e - 1]
    rng = H - L
    if rng <= 0 or not (C > O): return None
    r = (C - O) / rng; wick_open = (O - L) / rng; wick_close = (H - C) / rng
    idx_m = s + int(np.argmin(l[s:e])); idx_d = s + int(np.argmax(h[s:e]))
    t_m = S.minute[idx_m]; t_d = S.minute[idx_d]
    band = BAND_ATR * S.atr[i]
    k = next((j for j in range(s, e) if (h[j] - O) > band or (O - l[j]) > band), None)
    t_a = S.minute[k] if k is not None else 60
    rec = dict(pair=None, i=i, sign=sign, kz=S.kz[i], wd=S.wdn[i], hour_ny=S.hour_ny[i], date=S.date_ny[i],
               r=r, wick_open=wick_open, wick_close=wick_close, range_atr=rng / S.atr[i], body_atr=(C - O) / S.atr[i],
               t_m=t_m, t_d=t_d, t_a=min(t_a, t_m), idx_m=idx_m, idx_d=idx_d, manip=wick_open >= WICK_MIN,
               t_mss=np.nan, t_cisd=np.nan, fvg=False, fvg_min=np.nan, cls_h1=None, cls_60=None, depth_60=np.nan,
               ret_min=np.nan, cont_min=np.nan, ce_60=False, inval_60=False, swept_60=False,
               cls_cisd_60=None, fvg_cisd=False, ret_any_60=False, ret_any_h1=False, ext1_60=False)
    # quarter with largest with-trend progress (close-to-close per 15 min block)
    q = []
    for a in range(0, 60, 15):
        idx = [j for j in range(s, e) if a <= S.minute[j] <= a + 14]
        q.append((c[idx[-1]] - (o[idx[0]])) if idx else -np.inf)
    rec["best_q"] = int(np.argmax(q))
    if idx_m == s and t_m == 0:
        rec["t_mss"] = 0; return rec
    lvl = swing_high_level(h, idx_m, s)
    idx_mss = first_close_above(c, lvl, idx_m + 1, e) if lvl is not None else None
    lvl_c = cisd_level(o, c, idx_m, s)
    idx_cisd = first_close_above(c, lvl_c, idx_m + 1, e)
    if idx_cisd is not None: rec["t_cisd"] = S.minute[idx_cisd]
    if idx_mss is None: return rec
    rec["t_mss"] = S.minute[idx_mss]
    fvg = first_fvg(h, l, idx_m, idx_mss + 1, N)
    rec["fvg"] = fvg is not None
    if fvg is not None: rec["fvg_min"] = S.minute[fvg[0]] if fvg[0] < e else 60
    ev_h1 = follow_through(h, l, c, idx_m, idx_mss, fvg, e)
    ev_60 = follow_through(h, l, c, idx_m, idx_mss, fvg, min(idx_mss + 1 + WIN, N))
    rec["cls_h1"] = classify(fvg, ev_h1); rec["cls_60"] = classify(fvg, ev_60)
    rec["depth_60"] = ev_60["depth"]
    rec["ret_min"] = S.minute[ev_h1["returned"]] if ev_h1["returned"] is not None else np.nan
    rec["cont_min"] = S.minute[ev_h1["cont"]] if ev_h1["cont"] is not None else np.nan
    rec["ce_60"] = ev_60["ce"] is not None; rec["inval_60"] = ev_60["invalid"] is not None; rec["swept_60"] = ev_60["swept"] is not None
    rec["ret_any_60"] = ev_60["returned"] is not None; rec["ret_any_h1"] = ev_h1["returned"] is not None
    rec["ext1_60"] = ev_60["ext1"] is not None
    if idx_cisd is not None:
        fvg_c = first_fvg(h, l, idx_m, idx_cisd + 1, N)
        rec["fvg_cisd"] = fvg_c is not None
        rec["cls_cisd_60"] = classify(fvg_c, follow_through(h, l, c, idx_m, idx_cisd, fvg_c, min(idx_cisd + 1 + WIN, N)))
    return rec

def realtime_setup(S, i, sign):
    """Sweep of previous hour's low within the first SWEEP_MAX_MIN minutes, then MSS. No H1-close knowledge."""
    if not S.prev_ok[i]: return None
    o, h, l, c = S.view(sign); s, e = S.s[i], S.e[i]; N = len(o)
    PL = min(l[S.s[i - 1]:S.e[i - 1]]); PH = max(h[S.s[i - 1]:S.e[i - 1]])
    if o[s] < PL: return None   # hour must open inside the previous hour's range: a sweep, not a gap/continuation
    sweep = next((j for j in range(s, e) if S.minute[j] <= SWEEP_MAX_MIN and l[j] < PL), None)
    if sweep is None: return None
    rec = dict(pair=None, i=i, sign=sign, kz=S.kz[i], wd=S.wdn[i], hour_ny=S.hour_ny[i], sweep_min=S.minute[sweep],
               mss=False, t_mss=np.nan, mss_in_hour=False, fvg=False, cls_60=None, depth_60=np.nan,
               swept_60=False, ce_60=False, inval_60=False, target_60=False, h1_dir=(c[e - 1] > o[s]),
               h1_directional=((c[e - 1] - o[s]) / max(h[s:e].max() - l[s:e].min(), 1e-12)) >= R_DIR,
               race_ph=None, race_ext1=None, race_open=None, ret_before=False, ret_any=False, sweep_depth_atr=np.nan)
    lo = sweep; idx_mss = None
    for j in range(sweep, min(sweep + WIN, N)):
        if l[j] < l[lo]: lo = j
        if j == lo: continue
        lvl = swing_high_level(h, lo, max(lo - 60, 0))
        if lvl is not None and c[j] > lvl: idx_mss = j; break
    if idx_mss is None: return rec
    rec.update(mss=True, t_mss=S.minute[idx_mss], mss_in_hour=idx_mss < e)
    fvg = first_fvg(h, l, lo, idx_mss + 1, N); rec["fvg"] = fvg is not None
    ev = follow_through(h, l, c, lo, idx_mss, fvg, min(idx_mss + 1 + WIN, N), targets={"ph": PH, "open": o[s]})
    rec["cls_60"] = classify(fvg, ev); rec["depth_60"] = ev["depth"]
    rec["swept_60"] = ev["swept"] is not None; rec["ce_60"] = ev["ce"] is not None; rec["inval_60"] = ev["invalid"] is not None
    rec["target_60"] = ev["ph"] is not None
    rec["race_ph"] = race(ev, "ph"); rec["race_ext1"] = race(ev, "ext1"); rec["race_open"] = race(ev, "open")
    rec["ret_any"] = ev["returned"] is not None
    rec["ret_before"] = before(ev, "returned", "ph", "swept")
    rec["sweep_depth_atr"] = (PL - l[lo]) / S.atr[i]
    return rec

def run_series(S, pair):
    h1, rt, hours = [], [], []
    for i in range(len(S.hours)):
        if not (S.valid[i] and S.in_scope[i]) or not np.isfinite(S.atr[i]) or S.atr[i] <= 0: continue
        O, H, L, C = S.H1o[i], S.H1h[i], S.H1l[i], S.H1c[i]; rng = H - L
        if rng <= 0: continue
        r = abs(C - O) / rng
        hours.append(dict(pair=pair, i=i, kz=S.kz[i], wd=S.wdn[i], hour_ny=S.hour_ny[i], date=S.date_ny[i],
                          r=r, range_atr=rng / S.atr[i], body_atr=abs(C - O) / S.atr[i], directional=r >= R_DIR,
                          expansion=(r >= 0.65) and (rng / S.atr[i] >= 0.8)))
        if r >= R_DIR:
            rec = h1_conditional(S, i, 1 if C > O else -1)
            if rec: rec["pair"] = pair; h1.append(rec)
        for sign in (1, -1):
            rec = realtime_setup(S, i, sign)
            if rec: rec["pair"] = pair; rt.append(rec)
    return pd.DataFrame(hours), pd.DataFrame(h1), pd.DataFrame(rt)

# ------------------------------------------------------------------ statistics
def phase_matrix(d):
    """P(phase) per minute 0..59 over directional candles d. Returns DataFrame minute x phase (%)."""
    d = d[d["t_d"] >= d["t_m"]]
    n = len(d); M = np.zeros((60, 5))
    t_a = d["t_a"].values; t_m = d["t_m"].values; t_x = d["t_mss"].values; t_d = d["t_d"].values
    for m in range(60):
        A = (m < t_a) & (t_m > 0)
        Mn = (m >= t_a) & (m <= t_m) & (t_m > 0)
        x = np.where(np.isnan(t_x), 61, t_x)
        R = (m > t_m) & (m < x) & (m <= t_d) & (t_m > 0)
        D = (m >= x) & (m <= t_d) & (m >= t_m) & ~Mn
        D |= (t_m == 0) & (m <= t_d)
        done = m > t_d
        M[m] = [A.mean(), Mn.mean(), R.mean(), D.mean(), done.mean()]
    return pd.DataFrame(M * 100, columns=["Tích lũy", "Thao túng", "Đảo cấu trúc", "Phân phối", "Hoàn tất"])

def bin_table(M):
    rows = []
    for a, b in BINS5:
        rows.append(M.iloc[a:b + 1].mean().round(1).rename(f"{a:02d}–{b:02d}"))
    t = pd.DataFrame(rows); t.index.name = "Phút"
    return t

def dist_5min(x, label):
    x = pd.Series(x).dropna(); n = len(x)
    cells = {f"{a:02d}–{b:02d}": round(100 * ((x >= a) & (x <= b)).mean(), 1) for a, b in BINS5}
    row = pd.Series(cells, name=label); row["n"] = n; row["trung vị"] = float(x.median()) if n else np.nan
    return row

def outcome_row(d, col, label):
    n = len(d); vc = d[col].value_counts()
    def p(k): return pct(int(vc.get(k, 0)), n) if n else ""
    return pd.Series({"n": n, "Có FVG": pct(int(d["fvg"].sum()), n) if n else "",
                      "Tiếp tục, không về FVG": p("cont_no_retrace"), "Về FVG rồi tiếp tục": p("retrace_cont"),
                      "Về FVG rồi thất bại": p("retrace_fail"), "Không về FVG, không tiếp tục": p("stall"),
                      "Không FVG, tiếp tục": p("noFVG_cont"), "Không FVG, không tiếp tục": p("noFVG_stall")}, name=label)

def fvg_detail_row(d, label):
    f = d[d["fvg"]]; n = len(f)
    if n == 0: return pd.Series({"n (có FVG)": 0}, name=label)
    ret = f["cls_60"].isin(["retrace_cont", "retrace_fail"]).sum()
    cont_after_ret = (f["cls_60"] == "retrace_cont").sum()
    return pd.Series({"n (có FVG)": n, "Về FVG trước khi tiếp tục": pct(int(ret), n), "Về FVG bất kỳ lúc nào (60 phút)": pct(int(f["ret_any_60"].sum()), n),
                      "Về FVG trong giờ H1": pct(int(f["ret_any_h1"].sum()), n),
                      "Chạm CE (50% FVG, 60 phút)": pct(int(f["ce_60"].sum()), n), "Đóng cửa xuyên FVG (60 phút)": pct(int(f["inval_60"].sum()), n),
                      "Quét lại đáy thao túng (60 phút)": pct(int(f["swept_60"].sum()), n),
                      "Mở rộng thêm ≥ 1 chân đẩy (60 phút)": pct(int(f["ext1_60"].sum()), n)}, name=label)

def groups(d, extra_pair=True):
    out = [("Tất cả", d)]
    for kz in ["London", "NY_AM"]: out.append((kz, d[d["kz"] == kz]))
    for wd in ["Tue", "Wed", "Thu"]: out.append((wd, d[d["wd"] == wd]))
    for kz in ["London", "NY_AM"]:
        for wd in ["Tue", "Wed", "Thu"]: out.append((f"{kz} {wd}", d[(d["kz"] == kz) & (d["wd"] == wd)]))
    if extra_pair:
        for p in sorted(d["pair"].unique()): out.append((p, d[d["pair"] == p]))
    return out

def main():
    pairs = sys.argv[1].split(","); outp = sys.argv[2]
    HR, H1, RT = [], [], []
    for p in pairs:
        S = Series(load_m1(f"data/m1/{p}_M1_UTC.csv"))
        a, b, c = run_series(S, p); HR.append(a); H1.append(b); RT.append(c)
        print(p, len(a), len(b), len(c), flush=True)
    HR = pd.concat(HR); H1 = pd.concat(H1); RT = pd.concat(RT)
    S0 = Series(random_walk_m1(30000), scope=False)
    HR0, H10, RT0 = run_series(S0, "RW"); print("RW", len(HR0), len(H10), len(RT0), flush=True)
    d0 = H10[H10["manip"]]

    out = [f"# AMD, cửa sổ mở rộng và FVG sau MSS — London và NY AM, thứ Ba/Tư/Năm (FX)\n",
           f"Cặp: {', '.join(pairs)} (histdata.com M1, UTC). Phạm vi: giờ New York 02–04 (London) và 08–10 (NY AM), thứ Ba/Tư/Năm theo lịch New York. "
           f"Khoảng: {HR['date'].min()} → {HR['date'].max()}. Nến H1 trong phạm vi: {len(HR)}, trong đó định hướng (thân ≥ 50%): {len(H1)}, "
           f"có râu thao túng ≥ 5%: {int(H1['manip'].sum())}.\n",
           "Nền so sánh: bước ngẫu nhiên Gaussian (30.000 giờ, 6 bước con mỗi phút), chạy qua đúng cùng một pipeline, không lọc phiên.\n",
           "Định nghĩa vận hành: xem docstring của `po3_amd_killzone.py` cùng thư mục. Mọi con số dạng `x% [a–b]` là tỷ lệ kèm khoảng tin cậy Wilson 95%.\n"]

    # ---------------- 1. expansion window
    out.append("## 1. Khoảng thời gian xảy ra phân phối / mở rộng\n")
    out.append("### 1a. Giờ nào trong killzone mở rộng (mỗi killzone-ngày có đủ 3 giờ)\n")
    rows = []
    for (kz), g in HR.groupby("kz"):
        days = g.groupby(["pair", "date"])
        full = [x for _, x in days if len(x) == 3]
        n = len(full)
        big_body = pd.Series([x.loc[x["body_atr"].idxmax(), "hour_ny"] for x in full]).value_counts(normalize=True) * 100
        big_rng = pd.Series([x.loc[x["range_atr"].idxmax(), "hour_ny"] for x in full]).value_counts(normalize=True) * 100
        for hr, gg in g.groupby("hour_ny"):
            rows.append(pd.Series({"killzone": kz, "giờ NY": f"{hr:02d}:00", "n nến": len(gg),
                                   "P(định hướng r≥0,5)": f"{100*gg['directional'].mean():.1f}%",
                                   "P(mở rộng r≥0,65 & biên độ≥0,8 ATR)": f"{100*gg['expansion'].mean():.1f}%",
                                   "thân/ATR TB": round(gg["body_atr"].mean(), 2), "biên độ/ATR TB": round(gg["range_atr"].mean(), 2),
                                   "là giờ thân lớn nhất của killzone": f"{big_body.get(hr, 0):.1f}%",
                                   "là giờ biên độ lớn nhất": f"{big_rng.get(hr, 0):.1f}%", "n killzone-ngày": n}))
    t = pd.DataFrame(rows).set_index("killzone"); out.append(md(t))
    out.append("\nTheo ngày trong tuần (thân/ATR trung bình mỗi giờ; P(mở rộng) trong ngoặc):\n")
    rows = []
    for wd in ["Tue", "Wed", "Thu"]:
        g = HR[HR["wd"] == wd]; row = {"ngày": wd, "n": len(g)}
        for hr in [2, 3, 4, 8, 9, 10]:
            gg = g[g["hour_ny"] == hr]; row[f"{hr:02d}:00"] = f"{gg['body_atr'].mean():.2f} ({100*gg['expansion'].mean():.0f}%)"
        rows.append(row)
    out.append(md(pd.DataFrame(rows).set_index("ngày")))

    out.append("\n### 1b. Trong nến H1 định hướng: pha mở rộng bắt đầu và kết thúc ở phút nào\n")
    out.append("Bắt đầu = phút MSS (đóng cửa M1 vượt swing high cuối trước cực trị thao túng). Kết thúc = phút in cực trị thuận hướng. "
               "Chỉ nến có râu thao túng ≥ 5% (nến không râu mở rộng từ phút 0). Tỷ lệ % theo ô 5 phút.\n")
    dm = H1[H1["manip"]]; dm1 = dm[dm["t_m"] >= 1]; d01 = d0[d0["t_m"] >= 1]
    out.append(f"Nến có râu ≥ 5% nhưng in cực trị ngay phút 0 (không có pha thao túng để đo MSS): {pct(int((dm['t_m']==0).sum()), len(dm))}; "
               f"bước ngẫu nhiên: {pct(int((d0['t_m']==0).sum()), len(d0))}. Các dòng MSS dưới đây chỉ tính nến có cực trị từ phút 1 trở đi.\n")
    rows = []
    for label, g in groups(dm1):
        rows.append(dist_5min(g["t_mss"], f"{label}: MSS (bắt đầu mở rộng)"))
        rows.append(dist_5min(g["t_d"], f"{label}: cực trị thuận hướng (kết thúc)"))
    rows.append(dist_5min(d01["t_mss"], "Bước ngẫu nhiên: MSS")); rows.append(dist_5min(d01["t_d"], "Bước ngẫu nhiên: cực trị thuận hướng"))
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nCác mốc khác (nến định hướng có râu ≥ 5%, cực trị từ phút 1):\n")
    rows = []
    for label, g in groups(dm1) + [("Bước ngẫu nhiên", d01)]:
        n = len(g); has_mss = g["t_mss"].notna() & (g["t_mss"] > 0); has_cisd = g["t_cisd"].notna()
        both = has_mss & has_cisd
        rows.append(pd.Series({"n": n, "P(MSS trong giờ)": pct(int(has_mss.sum()), n), "P(CISD trong giờ)": pct(int(has_cisd.sum()), n),
                               "trung vị phút thao túng": g["t_m"].median(), "trung vị phút MSS": g.loc[has_mss, "t_mss"].median(),
                               "trung vị phút CISD": g.loc[has_cisd, "t_cisd"].median(),
                               "CISD trước hoặc cùng MSS": pct(int((g.loc[both, "t_cisd"] <= g.loc[both, "t_mss"]).sum()), int(both.sum())),
                               "trung vị phút cực trị thuận": g["t_d"].median(),
                               "MSS→cực trị thuận (phút, trung vị)": (g.loc[has_mss, "t_d"] - g.loc[has_mss, "t_mss"]).median()}, name=label))
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nQuý 15 phút có tiến triển thuận hướng lớn nhất (đóng cửa cuối quý trừ mở cửa đầu quý), mọi nến định hướng trong phạm vi:\n")
    rows = []
    for label, g in groups(H1) + [("Bước ngẫu nhiên", H10)]:
        vc = g["best_q"].value_counts(normalize=True) * 100
        rows.append(pd.Series({"n": len(g), **{f"Q{q+1} ({q*15:02d}–{q*15+14:02d})": f"{vc.get(q, 0):.1f}%" for q in range(4)}}, name=label))
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))

    # ---------------- 2. AMD by minute
    out.append("\n## 2. Xác suất pha AMD theo phút trong H1\n")
    out.append("Đọc: tại phút m của một nến H1 định hướng trong phạm vi, xác suất nến đang ở pha nào. "
               "Tích lũy = giá còn trong dải ±0,15 ATR quanh Open; Thao túng = đã rời dải nhưng chưa in cực trị ngược hướng; "
               "Đảo cấu trúc = đã in cực trị, chưa có MSS; Phân phối = từ MSS đến khi in cực trị thuận hướng; Hoàn tất = sau cực trị thuận hướng. "
               "Nến không râu thao túng (< 5%) tính là Phân phối từ phút 0. Giá trị là trung bình của 5 phút trong ô.\n")
    for label, g in [("Tất cả nến định hướng trong phạm vi", H1), ("Chỉ nến có râu thao túng ≥ 5%", dm),
                     ("London (râu ≥ 5%)", dm[dm["kz"] == "London"]), ("NY AM (râu ≥ 5%)", dm[dm["kz"] == "NY_AM"]),
                     ("Bước ngẫu nhiên (định hướng, râu ≥ 5%)", d0)]:
        out.append(f"\n**{label}** (n = {len(g)})\n"); out.append(md(bin_table(phase_matrix(g))))
    out.append("\nTheo ngày trong tuần (râu ≥ 5%), gộp hai killzone — cột Phân phối theo ô 5 phút:\n")
    rows = []
    for wd in ["Tue", "Wed", "Thu"]:
        M = phase_matrix(dm[dm["wd"] == wd]); rows.append(bin_table(M)["Phân phối"].rename(wd))
    t = pd.DataFrame(rows).T; t.index.name = "Phút"; out.append(md(t))
    out.append("\nBảng đầy đủ theo từng phút (râu ≥ 5%, hai killzone gộp) ở Phụ lục A.\n")

    # ---------------- 3. FVG after MSS
    out.append("\n## 3. Sau thao túng và MSS/CISD: giá có quay về FVG không, có tiếp tục mở rộng không\n")
    out.append("### 3a. Nến H1 định hướng đã biết (có nhìn trước: biết nến đóng cửa định hướng)\n")
    out.append("Mẫu: nến định hướng, râu ≥ 5%, có MSS trong giờ. FVG = khoảng trống 3 nến đầu tiên trong chân đẩy từ cực trị thao túng đến nến MSS. "
               "\"Tiếp tục\" = giá vượt đỉnh của chân đẩy tại lúc xác nhận MSS. Cửa sổ theo dõi: 60 nến M1 sau MSS (có thể sang giờ kế).\n")
    dmss = dm[dm["t_mss"].notna() & (dm["t_mss"] > 0)]
    rows = [outcome_row(g, "cls_60", label) for label, g in groups(dmss)] + [outcome_row(H10[H10["manip"] & H10["t_mss"].notna() & (H10["t_mss"] > 0)], "cls_60", "Bước ngẫu nhiên")]
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nChi tiết trên các trường hợp có FVG (cửa sổ 60 phút sau MSS):\n")
    rows = [fvg_detail_row(g, label) for label, g in groups(dmss)] + [fvg_detail_row(H10[H10["manip"] & H10["t_mss"].notna() & (H10["t_mss"] > 0)], "Bước ngẫu nhiên")]
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nCùng thống kê nhưng chỉ trong phần còn lại của giờ H1 (không sang giờ kế):\n")
    rows = [outcome_row(g, "cls_h1", label) for label, g in groups(dmss, extra_pair=False)]
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nDùng CISD làm xác nhận thay cho MSS (cửa sổ 60 phút):\n")
    dc = dm[dm["cls_cisd_60"].notna()].copy(); dc["fvg"] = dc["fvg_cisd"]
    rows = [outcome_row(g, "cls_cisd_60", label) for label, g in groups(dc, extra_pair=False)]
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nĐộ sâu hồi (retrace) sau MSS trước khi tiếp tục, tính theo % chân đẩy (cực trị thao túng → đỉnh chân đẩy), cửa sổ 60 phút:\n")
    rows = []
    for label, g in groups(dmss, extra_pair=False) + [("Bước ngẫu nhiên", H10[H10["manip"] & H10["t_mss"].notna() & (H10["t_mss"] > 0)])]:
        dd = g["depth_60"].dropna(); n = len(dd)
        rows.append(pd.Series({"n": n, "trung vị": f"{100*dd.median():.0f}%", "≤ 25%": f"{100*(dd<=0.25).mean():.1f}%", "25–50%": f"{100*((dd>0.25)&(dd<=0.5)).mean():.1f}%",
                               "50–100%": f"{100*((dd>0.5)&(dd<=1)).mean():.1f}%", "> 100% (quét lại đáy)": f"{100*(dd>1).mean():.1f}%",
                               "phút quay về FVG (trung vị, trong giờ)": g["ret_min"].median(), "phút tiếp tục (trung vị, trong giờ)": g["cont_min"].median()}, name=label))
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))

    out.append("\n### 3b. Thiết lập thời gian thực (không nhìn trước)\n")
    out.append(f"Mẫu: trong giờ killzone, giờ mở cửa bên trong biên độ giờ liền trước, giá quét đáy (hoặc đỉnh) của giờ liền trước trong {SWEEP_MAX_MIN} phút đầu, "
               "sau đó có MSS trong 60 nến M1 (đáy chạy được cập nhật, swing high tra ngược tối đa 60 nến, xuyên biên giờ). "
               "Không biết trước nến H1 đóng cửa ra sao. Cửa sổ theo dõi 60 nến M1 sau MSS. Cả hai hướng được xét.\n")
    rows = []
    for label, g in groups(RT) + [("Bước ngẫu nhiên", RT0)]:
        n = len(g); m = g[g["mss"]]; nm = len(m); rb = m[m["ret_before"]]; nrb = len(rb)
        rows.append(pd.Series({"n quét": n, "P(MSS trong 60 phút)": pct(int(g["mss"].sum()), n), "trung vị phút MSS": m["t_mss"].median(),
                               "độ sâu quét (ATR, trung vị)": round(float(m["sweep_depth_atr"].median()), 2), "Có FVG": pct(int(m["fvg"].sum()), nm),
                               "Đạt đỉnh giờ trước TRƯỚC khi mất đáy": pct(int((m["race_ph"] == "target").sum()), nm),
                               "Mất đáy thao túng TRƯỚC": pct(int((m["race_ph"] == "fail").sum()), nm),
                               "Không bên nào trong 60 phút": pct(int((m["race_ph"] == "neither").sum()), nm),
                               "Mở rộng ≥ 1 chân đẩy trước khi mất đáy": pct(int((m["race_ext1"] == "target").sum()), nm),
                               "Lấy lại Open giờ trước khi mất đáy": pct(int((m["race_open"] == "target").sum()), nm),
                               "Về FVG trước khi phân định": pct(int(m["ret_before"].sum()), nm),
                               "Trong số về FVG: đạt đỉnh giờ trước": pct(int((rb["race_ph"] == "target").sum()), nrb) if nrb else "",
                               "Trong số về FVG: mất đáy": pct(int((rb["race_ph"] == "fail").sum()), nrb) if nrb else "",
                               "Trong số KHÔNG về FVG: đạt đỉnh giờ trước": pct(int((m[~m["ret_before"]]["race_ph"] == "target").sum()), nm - nrb) if nm - nrb else "",
                               "H1 đóng cùng hướng": pct(int(m["h1_dir"].sum()), nm), "H1 định hướng cùng hướng": pct(int((m["h1_dir"] & m["h1_directional"]).sum()), nm)}, name=label))
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))
    out.append("\nĐọc: sau khi MSS xác nhận, hai kết cục loại trừ nhau được xét theo thứ tự xảy ra: giá chạm đỉnh của giờ liền trước (mục tiêu thanh khoản đối diện) hay giá phá đáy thao túng (thiết lập hỏng). "
               "\"Về FVG trước khi phân định\" = giá quay vào FVG của chân đẩy trước khi một trong hai kết cục xảy ra.\n")

    # ---------------- appendix
    out.append("\n## Phụ lục A. Pha AMD theo từng phút (nến định hướng, râu ≥ 5%, hai killzone gộp, %)\n")
    M = phase_matrix(dm).round(1); M.index.name = "Phút"; out.append(md(M))
    open(outp, "w").write("\n".join(out)); print("written", outp)
    H1.to_csv(outp.replace(".md", "_h1.csv"), index=False); RT.to_csv(outp.replace(".md", "_rt.csv"), index=False)

if __name__ == "__main__":
    main()
