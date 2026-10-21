#!/usr/bin/env python3
"""Win rate vs R:R for a market entry at the close of the CISD confirmation bar (03:00 / 09:00 NY, Tue-Thu).

Setup detection is the bar-by-bar state machine of ../analysis-2026-09-21/verify_indicator.py (rule v1.1),
extended to emit trades instead of log lines. No lookahead: every filter (sweep depth, FVG) is evaluated
with bars up to and including the entry bar only.

Usage: python3 po3_cisd_rr_winrate.py [--pairs EURUSD,GBPUSD] [--src histdata|dukascopy] [--out report.md]

Rule sets
  v1.0  entry = close of the CISD bar (sweep <= min 30, CISD bar minute <= 29, depth at CISD < 0.25 ATR24,
        other side not swept)
  v1.1  v1.0 + FVG >= 0.5 pip in the leg extreme -> CISD bar; if the FVG completes on the bar after the CISD,
        entry = close of that bar
Trade model (long wording, short mirrored)
  SL      sweep extreme - buffer (0 / 0.1 / 0.25 ATR24); risk = entry - SL
  TP      k R for k in TP_R
  exits   'h55': close of minute 54 of the setup hour if neither SL nor TP was hit (rule v1.x)
          'h4':  hold up to 240 bars, then market
  same bar touching SL and TP counts as SL (conservative)
  cost    COSTS pips round trip, converted to R per trade (cost_pip / risk_pip)
Null      'mirror': same entry bar and same risk distance, opposite direction. With no edge both sides have the
          same expectancy before cost.
"""
import argparse, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "analysis-2026-09-21"))
from verify_indicator import cisd_lvl, first_fvg, PIP, TZ  # noqa: E402

TP_R = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
SL_BUF = [0.0, 0.1, 0.25]
COSTS = [0.0, 0.5, 1.0]
HOLD_H4 = 240
MIN_FVG_PIP = 0.5


def load(pair, src):
    name = f"{pair}_M1_UTC_dukascopy.csv" if src == "dukascopy" else f"{pair}_M1_UTC.csv"
    df = pd.read_csv(os.path.join(HERE, "..", "..", "data", "m1", name), parse_dates=["ts_utc"])
    df["ts_utc"] = df["ts_utc"].dt.tz_localize("UTC")
    return df.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)


def find_trades(df, pair, sweep_max=30, cisd_max=29, depth_max=0.25):
    """Same state machine as verify_indicator.run(); returns one dict per entry (v1.0 and v1.1)."""
    pip = PIP.get(pair, 1e-4); min_gap = MIN_FVG_PIP * pip
    o, h, l, c = (df[x].values.astype(float) for x in ("open", "high", "low", "close"))
    ts = df["ts_utc"]; ny = ts.dt.tz_convert(TZ)
    EPOCH = pd.Timestamp(0, tz="UTC")
    hs_arr = ((ts.dt.floor("h") - EPOCH) // pd.Timedelta("1ms")).values.astype("int64")
    minute = ny.dt.minute.values; hour = ny.dt.hour.values; dow = ny.dt.weekday.values
    date = ny.dt.date.values
    out = []
    cur_hs = None; ch_hi = ch_lo = None; ch_bars = 0; ph = pl = None; prev_ok = False; h1_rng = []; atr = None
    S = {}
    for j in range(len(o)):
        hs = hs_arr[j]; m = minute[j]
        if hs != cur_hs:
            if cur_hs is not None:
                h1_rng.append(ch_hi - ch_lo if ch_bars >= 30 else np.nan)
                h1_rng = h1_rng[-24:]
                vals = [x for x in h1_rng if not np.isnan(x)]
                atr = float(np.mean(vals)) if len(vals) >= 12 else None
                prev_ok = ch_bars >= 30 and cur_hs == hs - 3600000
                ph, pl = ch_hi, ch_lo
            cur_hs = hs; ch_hi, ch_lo, ch_bars = h[j], l[j], 0
            target = hour[j] in (3, 9) and dow[j] in (1, 2, 3)
            scope = target and prev_ok and atr is not None and pl <= o[j] <= ph
            S = dict(scope=scope, sw_lo=None, lo=None, sw_hi=None, hi=None, cisd_b=None, cisd_s=None,
                     buy_done=False, sell_done=False, hour=hour[j], date=date[j], dow=dow[j], ph=ph, pl=pl, atr=atr)
        ch_bars += 1; ch_hi = max(ch_hi, h[j]); ch_lo = min(ch_lo, l[j])
        if not S["scope"]: continue
        sweep_now_lo = sweep_now_hi = newlo = newhi = False
        if S["sw_lo"] is None:
            if m <= sweep_max and l[j] < pl: S["sw_lo"], S["lo"], sweep_now_lo = m, j, True
        elif not S["buy_done"] and S["cisd_b"] is None and l[j] < l[S["lo"]]:
            S["lo"], newlo = j, True
        if S["sw_hi"] is None:
            if m <= sweep_max and h[j] > ph: S["sw_hi"], S["hi"], sweep_now_hi = m, j, True
        elif not S["sell_done"] and S["cisd_s"] is None and h[j] > h[S["hi"]]:
            S["hi"], newhi = j, True
        if S["sw_lo"] is not None and S["sw_hi"] is not None:
            S["buy_done"] = S["sell_done"] = True   # pending v1.1 entries die here, as in the indicator
        for bull in (True, False):
            sw, ext, cisd, done, now, new = (("sw_lo", "lo", "cisd_b", "buy_done", sweep_now_lo, newlo) if bull
                                             else ("sw_hi", "hi", "cisd_s", "sell_done", sweep_now_hi, newhi))
            if S[sw] is None or S[done]: continue
            base = dict(pair=pair, date=S["date"], dow=S["dow"], hour=S["hour"], side=1 if bull else -1,
                        atr=S["atr"], pip=pip, ext=l[S[ext]] if bull else h[S[ext]], ph=S["ph"], pl=S["pl"],
                        sweep_min=S[sw])
            if S[cisd] is None:
                if m > cisd_max:
                    S[done] = True
                elif not now and not new:
                    k = j - S[ext]
                    ok = c[j] > cisd_lvl(o, c, j, k, True) if bull else c[j] < cisd_lvl(o, c, j, k, False)
                    if ok:
                        d = (pl - l[S[ext]]) / atr if bull else (h[S[ext]] - ph) / atr
                        if d >= depth_max:
                            S[done] = True
                        else:
                            S[cisd] = j
                            out.append(dict(base, rule="v1.0", j=j, cisd_min=m, depth=d))
                            f = first_fvg(h, l, j, k, bull, min_gap)
                            if f:
                                S[done] = True
                                out.append(dict(base, rule="v1.1", j=j, cisd_min=m, depth=d, fvg_pip=(f[2] - f[1]) / pip))
            else:
                b, t = (h[j - 2], l[j]) if bull else (h[j], l[j - 2])
                S[done] = True
                if t - b >= min_gap and t > b:
                    out.append(dict(base, rule="v1.1", j=j, cisd_min=minute[S[cisd]], depth=S["atr"] and
                                    ((pl - base["ext"]) / atr if bull else (base["ext"] - ph) / atr), fvg_pip=(t - b) / pip))
    return out, (o, h, l, c, minute, hs_arr)


def path_stats(tr, arrays, buf, horizon, mirror=False):
    """Walk forward from the entry bar. Returns entry, risk, and per-bar arrays in R for the window."""
    o, h, l, c, minute, hs_arr = arrays
    j = tr["j"]; side = tr["side"] * (-1 if mirror else 1)
    entry = c[j]
    risk = abs(entry - tr["ext"]) + buf * tr["atr"]
    if risk <= 0: return None
    if horizon == "h55":
        end = j + 1
        while end < len(c) and hs_arr[end] == hs_arr[j] and minute[end] <= 54: end += 1
    else:
        end = min(j + 1 + HOLD_H4, len(c))
    if end <= j + 1: return None
    hi, lo, cl = h[j + 1:end], l[j + 1:end], c[j + 1:end]
    fav = ((hi - entry) if side > 0 else (entry - lo)) / risk     # favourable excursion per bar (R)
    adv = ((entry - lo) if side > 0 else (hi - entry)) / risk     # adverse excursion per bar (R)
    last = ((cl[-1] - entry) if side > 0 else (entry - cl[-1])) / risk
    return dict(risk=risk, fav=fav, adv=adv, last=last)


def outcome(p, k):
    """R result before cost for TP = k R (k=None: no TP, only SL / time). SL wins ties within a bar."""
    sl_hit = np.flatnonzero(p["adv"] >= 1.0)
    tp_hit = np.flatnonzero(p["fav"] >= k) if k is not None else np.array([], int)
    s = sl_hit[0] if len(sl_hit) else 10**9; t = tp_hit[0] if len(tp_hit) else 10**9
    if s == 10**9 and t == 10**9: return p["last"], "time"
    return (-1.0, "SL") if s <= t else (float(k), "TP")


def mfe_before_sl(p):
    sl_hit = np.flatnonzero(p["adv"] >= 1.0)
    upto = sl_hit[0] if len(sl_hit) else len(p["fav"])
    # bar that hits SL may also print its high first; conservative: exclude that bar's favourable excursion
    return float(p["fav"][:upto].max()) if upto > 0 else 0.0, len(sl_hit) > 0


def boot_ci(x, n=2000, seed=7):
    x = np.asarray(x); rng = np.random.default_rng(seed)
    if len(x) < 10: return (np.nan, np.nan)
    m = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; cen = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return cen - half, cen + half


def pct(x): return f"{100 * x:.0f}%"
def r2(x): return f"{x:+.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="EURUSD,GBPUSD"); ap.add_argument("--src", default="histdata")
    ap.add_argument("--out", default=os.path.join(HERE, "cisd-rr-winrate.md"))
    a = ap.parse_args()
    rows = []
    for pair in a.pairs.split(","):
        df = load(pair, a.src)
        trades, arrays = find_trades(df, pair)
        for tr in trades:
            rec = {k: v for k, v in tr.items()}
            rec["ts"] = df["ts_utc"].iloc[tr["j"]]
            for buf in SL_BUF:
                for hz in ("h55", "h4"):
                    for mir in (False, True):
                        p = path_stats(tr, arrays, buf, hz, mir)
                        if p is None: continue
                        mfe, slhit = mfe_before_sl(p)
                        r = dict(rec, buf=buf, hz=hz, mirror=mir, risk_pip=p["risk"] / tr["pip"],
                                 risk_atr=p["risk"] / tr["atr"], mfe=mfe, sl_hit=slhit, last=p["last"])
                        for k in TP_R + [None]:
                            res, lab = outcome(p, k)
                            key = "notp" if k is None else f"{k:g}"
                            r[f"r_{key}"] = res; r[f"o_{key}"] = lab
                        rows.append(r)
        print(pair, len(trades), "entries", file=sys.stderr)
    R = pd.DataFrame(rows)
    R.drop(columns=["ts"]).to_csv(os.path.join(HERE, "cisd-rr-winrate_trades.csv"), index=False)
    write_report(R, a)


def exp_table(g, cost_pip):
    """Rows per TP: n, P(TP), P(SL), P(time), win rate needed, E before cost, E after cost [CI]."""
    lines = []
    cost_r = cost_pip / g["risk_pip"]
    for k in TP_R + [None]:
        key = "notp" if k is None else f"{k:g}"
        res = g[f"r_{key}"].values; lab = g[f"o_{key}"].values; n = len(res)
        ptp = (lab == "TP").mean(); psl = (lab == "SL").mean(); pti = (lab == "time").mean()
        net = res - cost_r.values
        lo, hi = boot_ci(net)
        wl, wh = wilson((lab == "TP").sum(), n)
        be = (1 + cost_r.mean()) / (k + 1) if k else np.nan
        lines.append(f"| {('không TP' if k is None else f'{k:g}R')} | {n} | {pct(ptp)} ({pct(wl)}–{pct(wh)}) | {pct(psl)} | {pct(pti)} | "
                     f"{'—' if k is None else pct(be)} | {r2(res.mean())} | {r2(net.mean())} [{r2(lo)}; {r2(hi)}] |")
    return lines


def write_report(R, a):
    L = []
    L.append("# Win rate theo R:R — vào lệnh tại giá đóng nến CISD (03:00 và 09:00 NY, thứ Ba–Năm)\n")
    L.append(f"Sinh bởi `po3_cisd_rr_winrate.py --pairs {a.pairs} --src {a.src}`. Phát hiện setup bằng đúng máy trạng thái của "
             "`verify_indicator.py` (không nhìn trước). Quy ước: SL và TP cùng chạm trong một nến M1 tính là SL. "
             "Mỗi cột E là kỳ vọng mỗi lệnh tính bằng R; khoảng trong ngoặc vuông là khoảng tin cậy 95% bootstrap. "
             "'Win rate cần' = tỷ lệ chạm TP tối thiểu để hòa vốn sau phí, nếu mọi lệnh kết thúc bằng TP hoặc SL. "
             "'Đối xứng' = cùng nến vào, cùng khoảng SL, đi ngược hướng: nếu setup không có lợi thế, hai bên cho cùng kỳ vọng trước phí.\n")
    base = R[(~R.mirror)]
    for rule in ("v1.0", "v1.1"):
        g0 = base[(base.rule == rule) & (base.buf == 0.0) & (base.hz == "h55")]
        L.append(f"- {rule}: {len(g0)} lệnh; theo cặp " + ", ".join(f"{p} {n}" for p, n in g0.pair.value_counts().items()) +
                 f"; giai đoạn {g0.date.min()} → {g0.date.max()}; rủi ro trung vị {g0.risk_pip.median():.1f} pip "
                 f"({g0.risk_atr.median():.2f} ATR) với SL đúng cực trị.")
    L.append("")

    # 1. MFE distribution
    L.append("## 1. Giá đi được bao nhiêu R trước khi chạm SL (MFE trước SL)\n")
    L.append("Đây là xác suất 'chạm k R trước SL', không có thoát theo giờ ở cột giữ 4 giờ. Cột đối xứng là nền ngẫu nhiên.\n")
    L.append("| Quy tắc | SL | Giữ | n | P(chạm SL) | ≥1R | ≥1,5R | ≥2R | ≥3R | ≥5R | Đối xứng ≥1R | Đối xứng ≥2R |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for rule in ("v1.0", "v1.1"):
        for buf in SL_BUF:
            for hz in ("h55", "h4"):
                g = R[(R.rule == rule) & (R.buf == buf) & (R.hz == hz)]
                s, m = g[~g.mirror], g[g.mirror]
                if s.empty: continue
                f = lambda d, k: pct((d.mfe >= k).mean())
                L.append(f"| {rule} | +{buf:g} ATR | {'tới phút 55' if hz == 'h55' else '4 giờ'} | {len(s)} | {pct(s.sl_hit.mean())} | "
                         f"{f(s,1)} | {f(s,1.5)} | {f(s,2)} | {f(s,3)} | {f(s,5)} | {f(m,1)} | {f(m,2)} |")
    L.append("")

    # 2. Expectancy tables
    L.append("## 2. Win rate và kỳ vọng theo TP\n")
    for rule in ("v1.0", "v1.1"):
        for buf in SL_BUF:
            for hz in ("h55", "h4"):
                g = base[(base.rule == rule) & (base.buf == buf) & (base.hz == hz)]
                if g.empty: continue
                L.append(f"### {rule}, SL = cực trị + {buf:g} ATR, thoát {'phút 55' if hz == 'h55' else 'sau 4 giờ'}\n")
                L.append("Phí 1 pip khứ hồi. P(TP) kèm khoảng tin cậy Wilson 95%.\n")
                L.append("| TP | n | P(TP) | P(SL) | P(hết giờ) | Win rate cần | E trước phí | E sau 1 pip |")
                L.append("|---|---|---|---|---|---|---|---|")
                L += exp_table(g, 1.0)
                L.append("")

    # 3. Setup vs mirror and cost sensitivity, rule SL
    L.append("## 3. Setup so với đối xứng, và độ nhạy theo phí (SL = cực trị + 0,25 ATR, thoát phút 55)\n")
    L.append("| Quy tắc | TP | E setup trước phí | E đối xứng trước phí | Chênh [CI 95%] | E sau 0,5 pip | E sau 1 pip |")
    L.append("|---|---|---|---|---|---|---|")
    for rule in ("v1.0", "v1.1"):
        g = R[(R.rule == rule) & (R.buf == 0.25) & (R.hz == "h55")]
        s, m = g[~g.mirror].reset_index(drop=True), g[g.mirror].reset_index(drop=True)
        for k in [1.0, 1.5, 2.0, 3.0]:
            key = f"{k:g}"
            d = s[f"r_{key}"].values - m[f"r_{key}"].values
            lo, hi = boot_ci(d)
            e05 = (s[f"r_{key}"] - 0.5 / s.risk_pip).mean(); e1 = (s[f"r_{key}"] - 1.0 / s.risk_pip).mean()
            L.append(f"| {rule} | {k:g}R | {r2(s[f'r_{key}'].mean())} | {r2(m[f'r_{key}'].mean())} | {r2(d.mean())} [{r2(lo)}; {r2(hi)}] | {r2(e05)} | {r2(e1)} |")
    L.append("")

    # 4. Breakdown for the rule configuration
    L.append("## 4. Chia nhỏ (v1.1, SL = cực trị + 0,25 ATR, TP 2R, thoát phút 55, phí 1 pip)\n")
    g = base[(base.rule == "v1.1") & (base.buf == 0.25) & (base.hz == "h55")].copy()
    g["year"] = pd.to_datetime(g.date).dt.year
    L.append("| Nhóm | n | P(TP) | P(SL) | E trước phí | E sau phí [CI] |")
    L.append("|---|---|---|---|---|---|")
    for col, name in (("pair", "Cặp"), ("hour", "Giờ NY"), ("dow", "Thứ"), ("side", "Hướng"), ("year", "Năm")):
        for v, gg in g.groupby(col):
            net = gg["r_2"] - 1.0 / gg.risk_pip; lo, hi = boot_ci(net)
            lab = {1: "mua", -1: "bán"}.get(v, v) if col == "side" else ({1: "Ba", 2: "Tư", 3: "Năm"}.get(v, v) if col == "dow" else v)
            L.append(f"| {name} {lab} | {len(gg)} | {pct((gg['o_2'] == 'TP').mean())} | {pct((gg['o_2'] == 'SL').mean())} | "
                     f"{r2(gg['r_2'].mean())} | {r2(net.mean())} [{r2(lo)}; {r2(hi)}] |")
    L.append("")

    # 5. Streaks
    L.append("## 5. Chuỗi thua (v1.1, SL = cực trị + 0,25 ATR, TP 2R, thoát phút 55)\n")
    s = g.sort_values(["date", "hour", "pair"])
    loss = (s["r_2"] - 1.0 / s.risk_pip).values < 0
    run = best = 0
    for x in loss:
        run = run + 1 if x else 0; best = max(best, run)
    p_loss = loss.mean()
    sims = np.random.default_rng(1).random((5000, 100)) < p_loss
    def longest(row):
        r = b = 0
        for x in row:
            r = r + 1 if x else 0; b = max(b, r)
        return b
    ls = np.array([longest(x) for x in sims])
    L.append(f"Tỷ lệ lệnh lỗ (R sau phí < 0): {pct(p_loss)}. Chuỗi lỗ dài nhất trong mẫu thật: {best} lệnh. "
             f"Mô phỏng 100 lệnh độc lập với cùng tỷ lệ lỗ: chuỗi lỗ dài nhất trung vị {int(np.median(ls))}, "
             f"90% số lần ≤ {int(np.percentile(ls, 90))}, P(chuỗi ≥ 8) = {pct((ls >= 8).mean())}.\n")
    open(a.out, "w").write("\n".join(L) + "\n")
    print("wrote", a.out, file=sys.stderr)


if __name__ == "__main__":
    main()
