#!/usr/bin/env python3
"""FX-only certification of the PO3 H1 report claims. Robustness: per pair, pooled, per year,
two wick thresholds, with/without NY news hours (08:00 and 10:00 NY), two data feeds.
Usage: python3 po3_fx_verify.py EURUSD,GBPUSD[,USDJPY,...] reports/FX_chung_thuc.md
"""
import sys, os
import numpy as np, pandas as pd
from po3_stats import load_m1, h1_from_m1, load_h1, features, pct, random_walk_null, weekly_null, weekday_stats, md, SESSION, WD

BINS = [(0, 10), (11, 25), (26, 40), (41, 59)]

def dist_row(name, m):
    n = len(m)
    cells = [f"{100*((m>=a)&(m<=b)).mean():.1f}%" for a, b in BINS]
    return f"| {name} | {n} | " + " | ".join(cells) + f" | {pct(int((m<=25).sum()), n)} | {m.median():.0f} | {100*(m==0).mean():.1f}% |"

HDR = ["| Tập | n | 00–10 | 11–25 | 26–40 | 41–59 | ≤25 [CI95] | trung vị | phút 0 |", "|---|---|---|---|---|---|---|---|---|"]

def sel(d, wmin):
    return d[d["directional"] & (d["wick_open"] >= wmin) & d["min_manip"].notna()]

def main():
    pairs = sys.argv[1].split(","); outp = sys.argv[2]
    feats = {}
    for p in pairs:
        feats[p] = features(h1_from_m1(load_m1(f"data/m1/{p}_M1_UTC.csv")))
    pooled = pd.concat(feats.values())
    out = ["# Chứng thực FX — Phân bố thời gian PO3 trên nến H1\n",
           f"Cặp: {', '.join(pairs)} (histdata.com M1, UTC). Khoảng: {pooled.index.min()} → {pooled.index.max()}. Tổng nến H1: {len(pooled)}.\n",
           "Báo cáo gốc: 00–10: 24,5% | 11–25: 46,8% | 26–40: 18,2% | 41–59: 10,5% | ≤25: 71,3%\n"]
    # A. per pair + pooled, wick >= 5%
    out.append("## A. Từng cặp và gộp (nến định hướng r≥0,5; râu phía Open ≥5%)\n"); out += HDR
    for p, d in feats.items(): out.append(dist_row(p, sel(d, 0.05)["min_manip"]))
    out.append(dist_row("**FX gộp**", sel(pooled, 0.05)["min_manip"]))
    nul = random_walk_null()
    for tag, (bins, le25, med, m0, n) in nul.items():
        if tag == ">= 5%": out.append(f"| Random walk ≥5% | {n} | " + " | ".join(f"{b:.1f}%" for b in bins) + f" | {le25:.1f}% | {med:.0f} | {m0:.1f}% |")
    # B. strict wick
    out.append("\n## B. Ngưỡng râu nghiêm hơn (≥15% biên độ)\n"); out += HDR
    for p, d in feats.items(): out.append(dist_row(p, sel(d, 0.15)["min_manip"]))
    out.append(dist_row("**FX gộp**", sel(pooled, 0.15)["min_manip"]))
    for tag, (bins, le25, med, m0, n) in nul.items():
        if tag == ">= 15%": out.append(f"| Random walk ≥15% | {n} | " + " | ".join(f"{b:.1f}%" for b in bins) + f" | {le25:.1f}% | {med:.0f} | {m0:.1f}% |")
    # C. per year (pooled)
    out.append("\n## C. Ổn định theo năm (FX gộp, râu ≥5%)\n"); out += HDR
    x = sel(pooled, 0.05)
    for y, g in x.groupby(x.index.year): out.append(dist_row(str(y), g["min_manip"]))
    # D. per session pooled, and excluding news hours
    out.append("\n## D. Theo phiên (FX gộp, râu ≥5%), có và không có giờ chứa tin NY (08:00 và 10:00 NY)\n"); out += HDR
    for s, g in x.groupby("session"): out.append(dist_row(s, g["min_manip"]))
    xn = x[~x["hour_ny"].isin([8, 10])]
    out.append(dist_row("**FX gộp, bỏ giờ 08 & 10 NY**", xn["min_manip"]))
    out.append(dist_row("NY_AM, bỏ giờ 08 & 10 NY", xn[xn["session"]=="NY_AM"]["min_manip"]))
    # E. CDF pooled per session
    out.append("\n## E. CDF theo phiên (FX gộp, râu ≥5%): đến phút m, % nến đã in xong cực trị thao túng\n")
    ms = [5, 10, 15, 20, 25, 30, 40, 50]
    out.append("| Phiên | " + " | ".join(f"≤{m}" for m in ms) + " |"); out.append("|---|" + "---|"*len(ms))
    for s, g in [("ALL", x)] + list(x.groupby("session")):
        out.append(f"| {s} | " + " | ".join(f"{100*(g['min_manip']<=m).mean():.0f}%" for m in ms) + " |")
    # F. feed cross-check
    out.append("\n## F. Đối chiếu nguồn dữ liệu (Dukascopy so với histdata, cùng khoảng thời gian)\n"); out += HDR
    for p in pairs:
        dp = f"data/m1/{p}_M1_UTC_dukascopy.csv"
        if not os.path.exists(dp): continue
        dd = features(h1_from_m1(load_m1(dp)))
        hh = feats[p][feats[p].index >= dd.index.min()]
        out.append(dist_row(f"{p} histdata", sel(hh, 0.05)["min_manip"]))
        out.append(dist_row(f"{p} Dukascopy", sel(dd, 0.05)["min_manip"]))
    # G. hour-of-day momentum pooled
    out.append("\n## G. Giờ động lượng (FX gộp, giờ New York)\n")
    g = pooled.groupby("hour_ny")
    t = pd.DataFrame({"n": g.size(), "body/ATR": g["body_atr"].mean().round(2), "range/ATR": g["range_atr"].mean().round(2),
                      "P(mở rộng r≥0,65 & biên độ≥0,8ATR)%": g.apply(lambda z: 100*((z["r"]>=0.65)&(z["range_atr"]>=0.8)).mean()).round(1)})
    t["phiên"] = [SESSION.get(h, "other") for h in t.index]; t.index.name = "giờ NY"
    out.append(md(t))
    top = t.sort_values("body/ATR", ascending=False).head(6)
    out.append("\nXếp hạng body/ATR: " + ", ".join(f"{h:02d}:00 ({v})" for h, v in top["body/ATR"].items()))
    # H. weekday on long H1 history (Dukascopy 2021-2026) where available, else histdata
    out.append("\n## H. Ngày trong tuần (Dukascopy H1 2021–2026 nếu có, tuần ≥4 ngày)\n")
    for p in pairs:
        hp = f"data/h1/{p}_H1_UTC.csv"
        if os.path.exists(hp):
            dh = features(load_h1(hp)); out.append(f"### {p} (H1 Dukascopy, {dh.index.min().date()} → {dh.index.max().date()})\n")
        else:
            dh = feats[p]; out.append(f"### {p} (M1 histdata, {dh.index.min().date()} → {dh.index.max().date()})\n")
        tmp = []; weekday_stats(dh, tmp); out += tmp[1:]
    open(outp, "w").write("\n".join(out)); print("written", outp)

if __name__ == "__main__":
    main()
