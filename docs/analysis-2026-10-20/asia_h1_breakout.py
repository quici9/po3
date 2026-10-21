#!/usr/bin/env python3
"""Asia H1 breakout pattern (2026-10-20): occurrence rates only, no entry/SL/TP.

Usage: python3 asia_h1_breakout.py <repo_root> <out_dir>

Pattern (all times America/New_York):
  1. Asia range = high/low of 20:00-00:00 (Monday uses Sunday evening).
  2. Breakout = first H1 candle from 00:00 whose CLOSE is above Asia high / below Asia low.
     Day kept only if that candle opens 00:00-05:00; a first close-outside at 06:00+ drops the day.
  3. Retrace = price touches candle extreme - 25% of candle range (break up; mirrored for down)
     between the candle close and 11:00, while Asia level + 1 Asia width has not printed yet.
  4. Target = broken Asia level + 1 Asia width (1 SD), checked on minutes strictly after the touch minute.
  FVG variant (2026-10-21): the breakout H1 candle must also contain an M15 FVG in the breakout direction,
  with all 3 M15 candles inside that hour (M15 1-2-3 or 2-3-4). Up: low[3] > high[1]; down: high[3] < low[1].
  No minimum size. If the first close-outside candle has no FVG the day is dropped (no later candle is used).

Timezone: data/m1/*_M1_UTC.csv (histdata) are 1h late during EU summer time. True instant =
(ts_utc + 2h) localised to Europe/Athens. Verified against Dukascopy (99.99% OHLC match).
Days with < 80% M1 coverage in Asia or 00:00-16:00 are dropped.
Random-walk baseline: Gaussian log-RW with sigma matched per (day, hour), M1 high/low from the
Brownian-bridge max/min distribution, 3 seeds pooled.
"""
import math, os, sys
import numpy as np, pandas as pd

TZ = "America/New_York"
SYMS = {"EURUSD": "EURUSD", "XAUUSD": "XAUUSD", "NSXUSD": "NAS100 (NSXUSD)"}
SEEDS = [11, 22, 33]
START, END = pd.Timestamp("2023-01-01"), pd.Timestamp("2026-09-30")
WD = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu"]
BRK_HOURS = range(0, 6)       # breakout candle opens 00:00-05:00
RETRACE = 0.25

def M(hh, mm=0): return ((hh * 60 + mm) - 18 * 60) % 1440     # minute index since 18:00 NY of D-1
A0, A1 = M(20), M(0)
T11, T16 = M(11), M(16)

def load_true_utc(path):
    df = pd.read_csv(path, parse_dates=["ts_utc"])
    wall = df["ts_utc"] + pd.Timedelta(hours=2)                 # = EET/EEST wall clock
    t = wall.dt.tz_localize("Europe/Athens", ambiguous="NaT", nonexistent="NaT")
    keep = t.notna().values
    df = df[keep].reset_index(drop=True); df["t"] = t[keep].dt.tz_convert("UTC").reset_index(drop=True)
    return df.drop_duplicates("t").sort_values("t").reset_index(drop=True)

def to_grid(df):
    """-> O,H,L,C arrays (ndays, 1440) on the 18:00-anchored NY grid, dates = NY Mon..Fri."""
    ny = df["t"].dt.tz_convert(TZ).dt.tz_localize(None)
    sh = ny + pd.Timedelta(hours=6)
    sday = sh.dt.normalize()
    m = ((sh - sday).dt.total_seconds() // 60).astype(int).values
    days, di = np.unique(sday.values, return_inverse=True)
    G = {}
    for k, col in zip("OHLC", ["open", "high", "low", "close"]):
        a = np.full((len(days), 1440), np.nan); a[di, m] = df[col].values.astype(float); G[k] = a
    dates = pd.DatetimeIndex(days); keep = dates.weekday < 5
    for k in "OHLC": G[k] = G[k][keep]
    G["dates"] = dates[keep]
    return G

def tf_bars(G, tf):
    nd, nb = G["C"].shape[0], 1440 // tf
    H = G["H"].reshape(nd, nb, tf); L = G["L"].reshape(nd, nb, tf); C = G["C"].reshape(nd, nb, tf)
    ok = ~np.isnan(C); has = ok.any(2)
    li = tf - 1 - np.argmax(ok[:, :, ::-1], axis=2)
    c = np.take_along_axis(C, li[..., None], 2)[..., 0]
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h = np.nanmax(H, axis=2); l = np.nanmin(L, axis=2)
    for a in (c, h, l): a[~has] = np.nan
    return h, l, c

def rw_bb(G, seed):
    C = G["C"]; nd = C.shape[0]; valid = ~np.isnan(C)
    R = np.full(C.shape, np.nan); R[:, 1:] = np.diff(np.log(C), axis=1)
    Rh = R.reshape(nd, 24, 60); cnt = np.sum(~np.isnan(Rh), 2)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sd = np.nanstd(Rh, axis=2, ddof=1); sd = np.where(cnt >= 10, sd, np.nan)
        fb = np.nanmedian(sd, axis=0)
    fb = np.where(np.isnan(fb), np.nanmedian(sd), fb); sd = np.where(np.isnan(sd), fb[None, :], sd)
    sig = np.repeat(sd, 60, axis=1)[valid]
    rng = np.random.default_rng(seed); n = len(sig)
    x = rng.standard_normal(n) * sig
    c0 = math.log(C[valid][0]); lc = np.cumsum(x) + c0; o = np.r_[c0, lc[:-1]]
    mx = (x + np.sqrt(x * x + 2 * sig * sig * rng.exponential(size=n))) / 2
    mn = (x - np.sqrt(x * x + 2 * sig * sig * rng.exponential(size=n))) / 2
    S = {"dates": G["dates"]}
    for k, v in zip("OHLC", [o, o + mx, o + mn, lc]):
        a = np.full(C.shape, np.nan); a[valid] = np.exp(v); S[k] = a
    return S

def fidx(mask):
    if mask.size == 0: return -1
    i = int(np.argmax(mask)); return i if mask[i] else -1

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h

def fvg(Mh, Ml, kb, side):
    """M15 FVG in the breakout direction with all 3 candles inside H1 candle kb. Missing M15 bar (NaN) = no FVG."""
    h, l = Mh[4 * kb:4 * kb + 4], Ml[4 * kb:4 * kb + 4]
    if side == 1: return bool(l[2] > h[0] or l[3] > h[1])
    return bool(h[2] < l[0] or h[3] < l[1])

def day(H, L, Bh, Bl, Bc, Mh, Ml, AH, AL):
    """One session day. H1 candle k opens at 18:00 + k h, so k = 6 is 00:00 and k = 16 is 10:00."""
    kb, side = -1, 0
    for k in range(6, 17):                       # scan 00:00-10:00 so a first close-outside at 06+ is seen
        if Bc[k] > AH: side, kb = 1, k; break
        if Bc[k] < AL: side, kb = -1, k; break
    if kb < 0: return dict(brk=False)
    r = dict(brk=True, side=side, brk_hour=(18 + kb) % 24, fvg=fvg(Mh, Ml, kb, side), touch=False)
    te = (kb + 1) * 60
    if side == 1: h, l, bh, bl, A = H, L, Bh[kb], Bl[kb], AH
    else:         h, l, bh, bl, A = -L, -H, -Bl[kb], -Bh[kb], -AL
    W = AH - AL
    t = fidx(l[te:T11] <= bh - RETRACE * (bh - bl))
    if t < 0: return r
    tt = te + t
    r.update(touch=True, touch_hour=((18 * 60 + tt) % 1440) // 60,
             pre_1sd=bool(np.nanmax(h[te - 60:tt + 1]) >= A + W))
    for name, end in (("11", T11), ("16", T16)):
        seg = h[tt + 1:end]
        r[f"sd_{name}"] = (np.nanmax(seg) - A) / W if np.any(~np.isnan(seg)) else -np.inf
    j = fidx(h[tt + 1:T16] >= A + W)
    r["hit_hour"] = ((18 * 60 + tt + 1 + j) % 1440) // 60 if j >= 0 else -1
    return r

def run(G, sym, src):
    Bh, Bl, Bc = tf_bars(G, 60); Mh, Ml, _ = tf_bars(G, 15)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                 # days with no Asia data -> NaN, dropped by coverage below
        AH = np.nanmax(G["H"][:, A0:A1], 1); AL = np.nanmin(G["L"][:, A0:A1], 1)
    cov_a = np.mean(~np.isnan(G["C"][:, A0:A1]), 1); cov_d = np.mean(~np.isnan(G["C"][:, M(0):T16]), 1)
    dates = G["dates"]; ok = (cov_a >= 0.8) & (cov_d >= 0.8) & (dates >= START) & (dates <= END)
    out = []
    for d in np.nonzero(ok)[0]:
        iso = dates[d].isocalendar()
        r = dict(sym=sym, src=src, date=dates[d].strftime("%Y-%m-%d"), weekday=int(dates[d].weekday()),
                 wk=f"{iso[0]}-W{iso[1]:02d}", asia_high=AH[d], asia_low=AL[d])
        r.update(day(G["H"][d], G["L"][d], Bh[d], Bl[d], Bc[d], Mh[d], Ml[d], AH[d], AL[d]))
        out.append(r)
    return out

def flags(z):
    """p_* = pattern without the FVG condition, f_* = with the M15 FVG condition."""
    z = z.copy()
    z["p_brk"] = z.brk & z.brk_hour.isin(BRK_HOURS)
    z["f_brk"] = z.p_brk & (z.fvg == True)
    for v in "pf":
        z[f"{v}_touch"] = z[f"{v}_brk"] & (z.touch == True)
        z[f"{v}_ready"] = z[f"{v}_touch"] & (z.pre_1sd == False)
        z[f"{v}_hit11"] = z[f"{v}_ready"] & (z.sd_11 >= 1)
        z[f"{v}_full"] = z[f"{v}_ready"] & (z.sd_16 >= 1)
    return z

def p(k, n):
    if n == 0: return "—"
    a, lo, hi = wilson(k, n); return f"{100 * a:.1f}% [{100 * lo:.0f}–{100 * hi:.0f}] ({k}/{n})"

def main():
    repo, od = sys.argv[1], sys.argv[2]
    rows = []
    for sym in SYMS:
        G = to_grid(load_true_utc(os.path.join(repo, "data/m1", f"{sym}_M1_UTC.csv")))
        rows += run(G, sym, "real")
        for i, sd in enumerate(SEEDS): rows += run(rw_bb(G, sd), sym, f"rw{i + 1}")
        print(sym, "done", flush=True)
    D = flags(pd.DataFrame(rows))
    D[D.src == "real"].drop(columns=["src"]).to_csv(os.path.join(od, "asia-h1-breakout_days.csv"), index=False)

    O = ["# Breakout H1 khỏi Asia 00:00–05:00 → retrace 25% → 1 SD", "",
         "Sinh bởi `asia_h1_breakout.py`. Dữ liệu 2023-01 đến 2026-09, giờ New York đã sửa lỗi lệch giờ histdata.",
         "Chỉ đo tỉ lệ xảy ra. Khoảng tin cậy 95% (Wilson). Ngẫu nhiên = bước đi ngẫu nhiên, 3 lần mô phỏng gộp.",
         "Hai bản: **không lọc FVG** (định nghĩa gốc) và **có FVG M15** (nến H1 breakout chứa FVG M15 cùng hướng, cả 3 nến M15 trong giờ đó; "
         "nến close ngoài đầu tiên không có FVG thì bỏ ngày).", ""]
    def rate(Z, k, n):
        dn = Z[n].sum() if isinstance(n, str) else n
        return f"{100 * Z[k].sum() / dn:.0f}%" if dn else "—"
    for sym, name in SYMS.items():
        R = D[(D.sym == sym) & (D.src == "real")]; Q = D[(D.sym == sym) & (D.src != "real")]
        O += [f"## {name} ({len(R)} ngày)", "",
              "| bước | không lọc FVG | ngẫu nhiên | có FVG M15 | ngẫu nhiên |", "|---|---|---|---|---|"]
        def row(lab, k, n):
            cells = []
            for v in "pf":
                kk, nn = f"{v}_{k}", (f"{v}_{n}" if n else None)
                cells += [p(int(R[kk].sum()), int(R[nn].sum()) if nn else len(R)), rate(Q, kk, nn or len(Q))]
            O.append(f"| {lab} | " + " | ".join(cells) + " |")
        row("Có breakout 00:00–05:00 (trên mọi ngày)", "brk", None)
        O.append(f"| Breakout có FVG M15 (trên ngày breakout) | | | {p(int(R.f_brk.sum()), int(R.p_brk.sum()))} | {rate(Q, 'f_brk', 'p_brk')} |")
        row("Chạm 25% trước 11:00 (trên ngày breakout)", "touch", "brk")
        row("Lúc chạm 25%, 1 SD chưa tới (trên ngày chạm)", "ready", "touch")
        row("Sau đó tới 1 SD trước 11:00", "hit11", "ready")
        row("**Sau đó tới 1 SD trước 16:00**", "full", "ready")
        row("Trọn chuỗi (trên mọi ngày)", "full", None)
        O.append("")
        for v, lab in (("p", "không lọc FVG"), ("f", "có FVG M15")):
            g = R.groupby("wk"); wk = g[f"{v}_full"].sum()[g.size() >= 4]
            O.append(f"Theo tuần, {lab}: trung bình {wk.mean():.2f} ngày/tuần; tuần có ít nhất 1 lần {100 * (wk >= 1).mean():.0f}% ({len(wk)} tuần).")
        O += ["", "Tới 1 SD trước 16:00, trên ngày đã chạm 25% khi 1 SD chưa tới:", "",
              "| nhóm | không lọc FVG | ngẫu nhiên | có FVG M15 | ngẫu nhiên |", "|---|---|---|---|---|"]
        groups = [("Phá lên", lambda z: z.side == 1), ("Phá xuống", lambda z: z.side == -1)] + \
                 [(str(y), lambda z, y=y: z.date.str[:4] == str(y)) for y in range(2023, 2027)] + \
                 [("Nến breakout 00–01", lambda z: z.brk_hour <= 1), ("Nến breakout 02–05", lambda z: z.brk_hour >= 2)] + \
                 [(WD[w], lambda z, w=w: z.weekday == w) for w in range(5)]
        for lab, fn in groups:
            cells = []
            for v in "pf":
                rr = R[R[f"{v}_ready"]]; qq = Q[Q[f"{v}_ready"]]; s_, t_ = rr[fn(rr)], qq[fn(qq)]
                cells += [p(int(s_[f"{v}_full"].sum()), len(s_)), f"{100 * t_[f'{v}_full'].mean():.0f}%" if len(t_) else "—"]
            O.append(f"| {lab} | " + " | ".join(cells) + " |")
        O.append("")
    open(os.path.join(od, "asia-h1-breakout.md"), "w").write("\n".join(O)); print("\n".join(O))

if __name__ == "__main__":
    main()
