#!/usr/bin/env python3
"""PO3 H1 statistics: re-measure the hypotheses of the report from Dukascopy M1/H1 data.

Usage:
  python3 po3_stats.py m1 data/m1/EURUSD_M1_UTC.csv   [reports/EURUSD.md]
  python3 po3_stats.py h1 data/h1/EURUSD_H1_UTC.csv   [reports/EURUSD_h1only.md]

Definitions (frozen, see "Xác thực và Errata" section 4):
  directional: body/range >= 0.5 ; manipulation present: open-side wick/range >= 0.05
  manipulation extreme: Low of bullish H1 / High of bearish H1 ; minute = first M1 touching it
  sessions (America/New_York hour): Asia 19-23, London 2-4, NY_AM 8-10, NY_PM 13-15, other
  profile order: News/Outlier > Trend Runaway > Classic Expansion > Consolidation Reversal > Seek&Destroy > Other
"""
import sys, math
import numpy as np, pandas as pd

TZ = "America/New_York"
SESSION = {19: "Asia", 20: "Asia", 21: "Asia", 22: "Asia", 23: "Asia",
           2: "London", 3: "London", 4: "London",
           8: "NY_AM", 9: "NY_AM", 10: "NY_AM",
           13: "NY_PM", 14: "NY_PM", 15: "NY_PM"}
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def md(df):
    """Minimal DataFrame -> markdown table (no tabulate dependency)."""
    cols = [str(df.index.name or "")] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        lines.append("| " + " | ".join([str(idx)] + ["" if (isinstance(v, float) and math.isnan(v)) else str(v) for v in row.values]) + " |")
    return "\n".join(lines)

def random_walk_null(n_sim=200000, seed=7):
    """Random-walk H1 candles (60 Gaussian M1 steps), conditioned like the real sample.
    Returns dict wick_min -> (bin shares, P(<=25), median, P(minute0)) for the manipulation-extreme minute."""
    rng = np.random.default_rng(seed)
    steps = rng.standard_normal((n_sim, 60))
    path = np.concatenate([np.zeros((n_sim, 1)), np.cumsum(steps, axis=1)], axis=1)  # 61 points, 0 = open
    # M1 candle i spans path[i]..path[i+1]; hour low/high over all points
    lo = path.min(axis=1); hi = path.max(axis=1); close = path[:, -1]
    rng_ = hi - lo; body = np.abs(close); r = body / rng_
    bull = close > 0
    wick_open = np.where(bull, -lo, hi) / rng_
    ext_idx = np.where(bull, path.argmin(axis=1), path.argmax(axis=1))
    minute = np.clip(ext_idx - 1, 0, 59)  # point k is the end of M1 bar k-1; point 0 -> minute 0
    out = {}
    for wmin in (0.05, 0.15):
        m = minute[(r >= 0.5) & (wick_open >= wmin)]
        for tag, mm in ((f">= {int(wmin*100)}%", m), (f">= {int(wmin*100)}%, sau phút 0", m[m >= 1])):
            bins = [((mm >= a) & (mm <= b)).mean() * 100 for a, b in [(0, 10), (11, 25), (26, 40), (41, 59)]]
            out[tag] = (bins, (mm <= 25).mean() * 100, float(np.median(mm)), (mm == 0).mean() * 100, len(mm))
    return out

def weekly_null(n_sim=200000, seed=11, steps_per_day=24):
    """Random-walk weeks (5 days x steps_per_day Gaussian steps). Returns per-weekday shares (%) of:
    counter-extreme day, with-trend extreme day, largest with-trend daily body day."""
    rng = np.random.default_rng(seed)
    st = rng.standard_normal((n_sim, 5 * steps_per_day))
    path = np.concatenate([np.zeros((n_sim, 1)), np.cumsum(st, axis=1)], axis=1)
    close = path[:, -1]; bull = close > 0
    days = path[:, 1:].reshape(n_sim, 5, steps_per_day)
    d_open = np.concatenate([np.zeros((n_sim, 1)), days[:, :-1, -1]], axis=1)
    d_close = days[:, :, -1]
    d_hi = np.maximum(days.max(axis=2), d_open); d_lo = np.minimum(days.min(axis=2), d_open)
    lo_day = d_lo.argmin(axis=1); hi_day = d_hi.argmax(axis=1)
    manip = np.where(bull, lo_day, hi_day); withd = np.where(bull, hi_day, lo_day)
    body = (d_close - d_open) * np.where(bull, 1, -1)[:, None]
    dist = body.argmax(axis=1)
    return [(np.mean(manip == w) * 100, np.mean(withd == w) * 100, np.mean(dist == w) * 100) for w in range(5)]

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h

def pct(k, n):
    p, lo, hi = wilson(k, n)
    return f"{100*p:.1f}% [{100*lo:.1f}–{100*hi:.1f}] n={n}"

# ---------------------------------------------------------------- loading
def load_m1(path):
    df = pd.read_csv(path, parse_dates=["ts_utc"])
    df["ts_utc"] = df["ts_utc"].dt.tz_localize("UTC")
    df = df.set_index("ts_utc").sort_index()
    return df

def h1_from_m1(m1):
    hk = m1.index.floor("1h")
    g = m1.groupby(hk)
    h1 = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
               close=("close", "last"), volume=("volume", "sum"), n_m1=("open", "size"))
    # minute of first touch of the hour's low / high
    lo_idx = g["low"].idxmin(); hi_idx = g["high"].idxmax()
    h1["min_low"] = lo_idx.dt.minute.values
    h1["min_high"] = hi_idx.dt.minute.values
    # open of the M1 bar at minute 15 (hypothetical "True H1 Open")
    m15 = m1[m1.index.minute == 15]["open"]
    m15.index = m15.index.floor("1h")
    h1["open15"] = m15.reindex(h1.index)
    h1 = h1[h1["n_m1"] >= 30]  # drop illiquid / partial hours
    return h1

def load_h1(path):
    df = pd.read_csv(path, parse_dates=["ts_utc"])
    df["ts_utc"] = df["ts_utc"].dt.tz_localize("UTC")
    df = df.set_index("ts_utc").sort_index()
    df["min_low"] = np.nan; df["min_high"] = np.nan; df["open15"] = np.nan; df["n_m1"] = 60
    return df

# ---------------------------------------------------------------- features
def features(h1):
    d = h1.copy()
    ny = d.index.tz_convert(TZ)
    d["hour_ny"] = ny.hour; d["wd"] = ny.weekday; d["date_ny"] = ny.date
    d["session"] = d["hour_ny"].map(SESSION).fillna("other")
    d["range"] = d["high"] - d["low"]
    d = d[d["range"] > 0]
    d["bull"] = d["close"] > d["open"]
    d["bear"] = d["close"] < d["open"]
    d["body"] = (d["close"] - d["open"]).abs()
    d["r"] = d["body"] / d["range"]
    d["wick_open"] = np.where(d["bull"], d["open"] - d["low"], d["high"] - d["open"]) / d["range"]
    d["wick_close"] = np.where(d["bull"], d["high"] - d["close"], d["close"] - d["low"]) / d["range"]
    d["atr24"] = d["range"].rolling(24, min_periods=12).mean().shift(1)
    d["range_atr"] = d["range"] / d["atr24"]; d["body_atr"] = d["body"] / d["atr24"]
    d["directional"] = d["r"] >= 0.5
    d["manip"] = d["wick_open"] >= 0.05
    d["min_manip"] = np.where(d["bull"], d["min_low"], d["min_high"])
    d["min_with"] = np.where(d["bull"], d["min_high"], d["min_low"])
    d["seq_ok"] = d["min_manip"] < d["min_with"]   # OLHC for bull, OHLC for bear
    # profile classification (mutually exclusive, ordered)
    prof = np.full(len(d), "Other", dtype=object)
    seq = d["seq_ok"] if d["min_low"].notna().any() else pd.Series(True, index=d.index)
    cond = [
        ("News/Outlier", d["range_atr"] >= 2.5),
        ("TrendRunaway", (d["r"] >= 0.75) & (d["wick_open"] < 0.05)),
        ("ClassicExp", (d["range_atr"] >= 0.8) & (d["r"] >= 0.65) & d["wick_open"].between(0.05, 0.30) & (d["wick_close"] <= 0.15) & seq),
        ("ConsolRev", (d["r"] < 0.4) & ((d["wick_open"] >= 0.5) | (d["wick_close"] >= 0.5))),
        ("Seek&Destroy", (d["r"] < 0.3) & (d["wick_open"] >= 0.25) & (d["wick_close"] >= 0.25)),
    ]
    assigned = pd.Series(False, index=d.index)
    for name, c in cond:
        c = c.fillna(False) & ~assigned
        prof[c.values] = name; assigned |= c
    d["profile"] = prof
    return d

# ---------------------------------------------------------------- stats
def minute_stats(d, out, wick_min=0.05):
    x = d[d["directional"] & (d["wick_open"] >= wick_min) & d["min_manip"].notna()]
    out.append(f"## H1. Phút tạo cực trị thao túng (nến định hướng r>=0.5, râu phía Open >= {int(wick_min*100)}% biên độ)\n")
    out.append("Báo cáo gốc: 00–10: 24,5% | 11–25: 46,8% | 26–40: 18,2% | 41–59: 10,5% | <=25: 71,3%\n")
    bins = [(0, 10), (11, 25), (26, 40), (41, 59)]
    rows = []
    for name, grp in [("ALL", x)] + list(x.groupby("session")):
        m = grp["min_manip"]; n = len(m)
        cells = [f"{100*((m>=a)&(m<=b)).mean():.1f}%" for a, b in bins]
        le25 = pct(int((m <= 25).sum()), n)
        seq = pct(int(grp["seq_ok"].sum()), n)
        rows.append(f"| {name} | {n} | " + " | ".join(cells) + f" | {le25} | {m.median():.0f} | {seq} |")
    x1 = x[x["min_manip"] >= 1]
    for name, grp in [("ALL, chỉ nến có cực trị SAU phút 0", x1)] + [(f"{k} (sau phút 0)", g) for k, g in x1.groupby("session")]:
        m = grp["min_manip"]; n = len(m)
        cells = [f"{100*((m>=a)&(m<=b)).mean():.1f}%" for a, b in bins]
        rows.append(f"| {name} | {n} | " + " | ".join(cells) + f" | {pct(int((m <= 25).sum()), n)} | {m.median():.0f} | {pct(int(grp['seq_ok'].sum()), n)} |")
    out.append("| Phiên | n | 00–10 | 11–25 | 26–40 | 41–59 | <=25 [CI95] | trung vị phút | chuỗi OLHC/OHLC hợp lệ |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    out += rows
    out.append("\n### CDF: đến phút m, bao nhiêu % nến đã in xong cực trị thao túng\n")
    ms = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    out.append("| Phiên | " + " | ".join(f"<={m}" for m in ms) + " |")
    out.append("|---|" + "---|" * len(ms))
    for name, grp in [("ALL", x)] + list(x.groupby("session")):
        mm = grp["min_manip"]
        out.append(f"| {name} | " + " | ".join(f"{100*(mm<=m).mean():.0f}%" for m in ms) + " |")
    # share of candles with no manipulation wick at all
    y = d[d["directional"]]
    out.append(f"\nNến định hướng không có râu thao túng (<5%): {pct(int((~y['manip']).sum()), len(y))}")
    out.append(f"Nến định hướng có cực trị thao túng ở phút 0 (Open = cực trị hoặc chạm ngay phút đầu): {pct(int((y['min_manip']==0).sum()), len(y))}")
    # True open test
    b = d[d["bull"] & d["directional"] & d["open15"].notna()]
    s = d[d["bear"] & d["directional"] & d["open15"].notna()]
    if len(b) and wick_min <= 0.05:
        out.append("\n### Kiểm định mốc neo: Open giờ (xx:00) so với Open M1 lúc xx:15\n")
        out.append(f"Nến tăng: Low < Open giờ (có râu dưới): {pct(int((b['low']<b['open']).sum()), len(b))} ; Low hình thành SAU phút 15 và nằm dưới Open xx:15 (kịch bản 'quét True Open' của báo cáo): {pct(int(((b['low']<b['open15'])&(b['min_low']>=15)).sum()), len(b))}")
        out.append(f"Nến giảm: High > Open giờ (có râu trên): {pct(int((s['high']>s['open']).sum()), len(s))} ; High hình thành SAU phút 15 và nằm trên Open xx:15: {pct(int(((s['high']>s['open15'])&(s['min_high']>=15)).sum()), len(s))}")

def profile_stats(d, out):
    out.append("\n## H2. Tỷ lệ profile nến H1 theo phiên\n")
    out.append("Báo cáo gốc: Á S&D 60% / TrendRunaway 25% / ClassicExp 15% ; London ClassicExp 50% / ConsolRev 35% / News 15% ; NY ClassicExp 40% / ConsolRev 40% / News 20%\n")
    ct = pd.crosstab(d["session"], d["profile"], normalize="index") * 100
    ct["n"] = d.groupby("session").size()
    ct = ct.reindex(["Asia", "London", "NY_AM", "NY_PM", "other"])
    out.append(md(ct.round(1)))

def hour_stats(d, out):
    out.append("\n## H3. Giờ trong ngày (giờ New York) và động lượng\n")
    g = d.groupby("hour_ny")
    t = pd.DataFrame({
        "n": g.size(),
        "P(ClassicExp)%": g["profile"].apply(lambda s: 100 * (s == "ClassicExp").mean()).round(1),
        "P(Expansion r>=0.65 & range>=0.8ATR)%": g.apply(lambda x: 100 * ((x["r"] >= 0.65) & (x["range_atr"] >= 0.8)).mean()).round(1),
        "P(TrendRunaway)%": g["profile"].apply(lambda s: 100 * (s == "TrendRunaway").mean()).round(1),
        "P(S&D)%": g["profile"].apply(lambda s: 100 * (s == "Seek&Destroy").mean()).round(1),
        "body/ATR": g["body_atr"].mean().round(2),
        "range/ATR": g["range_atr"].mean().round(2),
        "mean r": g["r"].mean().round(2),
    })
    t["session"] = [SESSION.get(h, "other") for h in t.index]
    out.append(md(t))
    top = t.sort_values("P(ClassicExp)%", ascending=False).head(5)
    out.append("\nTop 5 giờ theo P(ClassicExp): " + ", ".join(f"{h:02d}:00 NY ({v}%)" for h, v in top["P(ClassicExp)%"].items()))
    top2 = t.sort_values("body/ATR", ascending=False).head(5)
    out.append("Top 5 giờ theo body/ATR: " + ", ".join(f"{h:02d}:00 NY ({v})" for h, v in top2["body/ATR"].items()))

def weekday_stats(d, out):
    out.append("\n## H4. Ngày trong tuần: thao túng và phân phối ở cấp tuần\n")
    # daily bars on NY calendar date
    day = d.groupby("date_ny").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                   close=("close", "last"), n=("open", "size"))
    day.index = pd.to_datetime(day.index)
    day["wd"] = day.index.weekday
    day = day[day["wd"] <= 4]
    day["week"] = day.index.to_period("W-SAT")  # weeks Sun..Sat -> Mon..Fri inside
    day["body_signed"] = day["close"] - day["open"]
    day["range"] = day["high"] - day["low"]
    res = []
    for wk, g in day.groupby("week"):
        if len(g) < 4: continue
        o, c = g["open"].iloc[0], g["close"].iloc[-1]
        bull = c > o
        if c == o: continue
        d_low = g["low"].idxmin().weekday(); d_high = g["high"].idxmax().weekday()
        manip_day = d_low if bull else d_high
        with_day = d_high if bull else d_low
        sb = g["body_signed"] if bull else -g["body_signed"]
        dist_day = sb.idxmax().weekday()
        res.append((manip_day, with_day, dist_day, bull))
    r = pd.DataFrame(res, columns=["manip", "with", "dist", "bull"])
    n = len(r)
    out.append(f"Số tuần: {n} (tuần có >=4 ngày, Close != Open)\n")
    out.append("| Thứ | Ngày tạo cực trị NGƯỢC hướng tuần (thao túng) | Ngày tạo cực trị THUẬN hướng (kết thúc phân phối) | Ngày có thân THUẬN hướng lớn nhất (phân phối chính) | Biên độ ngày TB / ATR |")
    out.append("|---|---|---|---|---|")
    atr = day["range"].mean()
    for w in range(5):
        out.append(f"| {WD[w]} | {pct(int((r['manip']==w).sum()), n)} | {pct(int((r['with']==w).sum()), n)} | {pct(int((r['dist']==w).sum()), n)} | {day[day['wd']==w]['range'].mean()/atr:.2f} |")
    out.append("\nMốc so sánh random walk (tuần 5 ngày, không có cấu trúc), cùng ba cột trên:\n")
    out.append("| Thứ | thao túng | kết thúc phân phối | phân phối chính |")
    out.append("|---|---|---|---|")
    for w, (a, b, c) in enumerate(weekly_null()):
        out.append(f"| {WD[w]} | {a:.1f}% | {b:.1f}% | {c:.1f}% |")

def main():
    mode, path = sys.argv[1], sys.argv[2]
    outp = sys.argv[3] if len(sys.argv) > 3 else None
    if mode == "m1":
        h1 = h1_from_m1(load_m1(path))
    else:
        h1 = load_h1(path)
    d = features(h1)
    out = [f"# PO3 H1 stats — {path}\n", f"Khoảng dữ liệu: {d.index[0]} → {d.index[-1]} (UTC); số nến H1 hợp lệ: {len(d)}; nến định hướng (r>=0.5): {pct(int(d['directional'].sum()), len(d))}\n"]
    if mode == "m1":
        minute_stats(d, out, 0.05)
        minute_stats(d, out, 0.15)
        out.append("\n### Mốc so sánh: bước ngẫu nhiên (random walk) với cùng điều kiện lọc\n")
        out.append("Nến giả lập 60 bước Gaussian, lọc r>=0.5 và râu phía Open >= ngưỡng, rồi đo phút tạo cực trị ngược hướng. Phần vượt trội của dữ liệu thật so với dòng này mới là 'thông tin' của PO3.\n")
        out.append("| Ngưỡng râu | 00–10 | 11–25 | 26–40 | 41–59 | <=25 | trung vị | phút 0 | n |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for tag, (bins, le25, med, m0, n) in random_walk_null().items():
            out.append(f"| {tag} | " + " | ".join(f"{b:.1f}%" for b in bins) + f" | {le25:.1f}% | {med:.0f} | {m0:.1f}% | {n} |")
    profile_stats(d, out); hour_stats(d, out); weekday_stats(d, out)
    txt = "\n".join(out)
    if outp:
        open(outp, "w").write(txt); print("written", outp)
    else:
        print(txt)

if __name__ == "__main__":
    main()
