#!/usr/bin/env python3
"""Reference implementation of the CISD+FVG setup marker in ICT_Future_Killzones_With_Deadlines_v7.pine.

Prints one line per 03:00 / 09:00 NY hour (Tue-Thu) in the same format as the indicator's debug table
and Pine Logs, so the two can be compared line by line. Bar-by-bar state machine, no lookahead.

Usage: python3 verify_indicator.py EURUSD [--days 10] [--end 2026-09-11] [--min-fvg 0.5] [--csv path]
Default CSV: data/m1/<PAIR>_M1_UTC_dukascopy.csv (Dukascopy bid M1, closest free feed to OANDA).

Rule v1.1 (2026-09-24): sweep of previous hour's extreme by minute <= 30, running extreme, CISD bar
minute <= 29, sweep depth at CISD < 0.25 ATR24, other side not swept, first FVG >= min pip inside the
leg extreme -> CISD bar (+1). Both sides are tracked independently; a side that has not produced a
signal is dropped as soon as both sides have been swept.
"""
import argparse, os, sys
import numpy as np, pandas as pd

TZ = "America/New_York"
HERE = os.path.dirname(os.path.abspath(__file__))
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4, "USDJPY": 1e-2, "XAUUSD": 1e-2}

def pm(m): return f"p{m:02d}"

def cisd_lvl(o, c, j, k, bull):
    """Level for bar j with running-extreme bar at offset k (index j-k). bull=True: open of the last run of
    bearish bars into the low; bull=False: low-side symmetric (open of the last run of bullish bars into the high)."""
    bear = (lambda i: c[i] < o[i]) if bull else (lambda i: c[i] > o[i])
    kk = k
    if not bear(j - kk): kk += 1
    lvl = o[j - k]
    if kk <= k + 60 and j - kk >= 0 and bear(j - kk):
        while kk + 1 <= k + 60 and j - kk - 1 >= 0 and bear(j - kk - 1): kk += 1
        lvl = o[j - kk]
    return lvl

def first_fvg(h, l, j, k, bull, min_gap):
    """First gap >= min_gap with middle bar i in (j-k+1 .. j-1). Returns (idx_formed, bot, top) or None."""
    if k < 2: return None
    for oi in range(k - 1, 0, -1):
        if bull: b, t = h[j - oi - 1], l[j - oi + 1]
        else:    t, b = l[j - oi - 1], h[j - oi + 1]
        if t - b >= min_gap and t > b: return j - oi + 1, b, t
    return None

def run(df, pair, days, end, min_fvg_pip, sweep_max=30, cisd_max=29, depth_max=0.25):
    pip = PIP.get(pair, 1e-4); min_gap = min_fvg_pip * pip
    o, h, l, c = (df[x].values.astype(float) for x in ("open", "high", "low", "close"))
    ts = df["ts_utc"]; ny = ts.dt.tz_convert(TZ)
    EPOCH = pd.Timestamp(0, tz="UTC")
    hs_arr = ((ts.dt.floor("h") - EPOCH) // pd.Timedelta("1ms")).values.astype("int64")
    minute = ny.dt.minute.values; hour = ny.dt.hour.values; dow = ny.dt.weekday.values  # Mon=0
    end_ms = int((pd.Timestamp(end, tz=TZ) - EPOCH) // pd.Timedelta("1ms")) if end else int(hs_arr[-1])
    win_start = end_ms - days * 86400000
    rows = []
    cur_hs = None; ch_hi = ch_lo = None; ch_bars = 0; ph = pl = None; prev_ok = False; h1_rng = []; atr = None
    S = {}

    def side_prefix(sw_min, cisd_min, depth):
        s = f"sweep {pm(sw_min)}"
        if cisd_min is not None: s += f" CISD {pm(cisd_min)} depth {depth:.2f}"
        return s

    def hour_row():
        head = f"{pd.Timestamp(cur_hs, unit='ms', tz='UTC').tz_convert(TZ):%Y-%m-%d %a %H:00} | ATR {atr/pip:.1f}p | PH {ph:.5f} PL {pl:.5f}" if atr else \
               f"{pd.Timestamp(cur_hs, unit='ms', tz='UTC').tz_convert(TZ):%Y-%m-%d %a %H:00} | ATR —"
        body = f" | {S['skip']}" if S["skip"] else f" | L: {S['res_b']} | S: {S['res_s']}"
        return head + body

    def close_hour():
        if S.get("target") and S.get("window"):
            if S["scope"]:
                if not S["buy_done"]:
                    S["res_b"] = "no sweep" if S["sw_lo"] is None else side_prefix(S["sw_lo"], S["cisd_b_min"], S["depth_b"]) + " -> no CISD"
                if not S["sell_done"]:
                    S["res_s"] = "no sweep" if S["sw_hi"] is None else side_prefix(S["sw_hi"], S["cisd_s_min"], S["depth_s"]) + " -> no CISD"
            rows.append(hour_row())

    for j in range(len(o)):
        hs = hs_arr[j]; m = minute[j]
        if hs != cur_hs:
            if cur_hs is not None:
                h1_rng.append(ch_hi - ch_lo if ch_bars >= 30 else np.nan)
                h1_rng = h1_rng[-24:]
                vals = [x for x in h1_rng if not np.isnan(x)]
                atr = float(np.mean(vals)) if len(vals) >= 12 else None
                close_hour()
                prev_ok = ch_bars >= 30 and cur_hs == hs - 3600000
                ph, pl = ch_hi, ch_lo
            cur_hs = hs; ch_hi, ch_lo, ch_bars = h[j], l[j], 0
            target = hour[j] in (3, 9) and dow[j] in (1, 2, 3)
            open_in = prev_ok and pl <= o[j] <= ph
            skip = "" if not target else "SKIP no prev hour" if not prev_ok else "SKIP no ATR" if not atr else \
                   f"SKIP open OUT ({o[j]:.5f})" if not open_in else ""
            S = dict(target=target, window=hs >= win_start, skip=skip, scope=target and skip == "",
                     sw_lo=None, lo=None, sw_hi=None, hi=None, cisd_b=None, cisd_s=None, cisd_b_min=None, cisd_s_min=None,
                     depth_b=None, depth_s=None, buy_done=False, sell_done=False, res_b="", res_s="")
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
            if not S["buy_done"]:
                S["buy_done"] = True; S["res_b"] = side_prefix(S["sw_lo"], S["cisd_b_min"], S["depth_b"]) + " -> SKIP 2 sides"
            if not S["sell_done"]:
                S["sell_done"] = True; S["res_s"] = side_prefix(S["sw_hi"], S["cisd_s_min"], S["depth_s"]) + " -> SKIP 2 sides"

        for bull in (True, False):
            sw, ext, cisd, cmin, dep, done, res, now, new = (("sw_lo", "lo", "cisd_b", "cisd_b_min", "depth_b", "buy_done", "res_b", sweep_now_lo, newlo) if bull
                                                            else ("sw_hi", "hi", "cisd_s", "cisd_s_min", "depth_s", "sell_done", "res_s", sweep_now_hi, newhi))
            if S[sw] is None or S[done]: continue
            tag = "BUY" if bull else "SELL"
            if S[cisd] is None:
                if m > cisd_max:
                    S[done] = True; S[res] = side_prefix(S[sw], None, None) + " -> no CISD"
                elif not now and not new:
                    k = j - S[ext]
                    confirmed = c[j] > cisd_lvl(o, c, j, k, True) if bull else c[j] < cisd_lvl(o, c, j, k, False)
                    if confirmed:
                        d = (pl - l[S[ext]]) / atr if bull else (h[S[ext]] - ph) / atr
                        S[dep] = d
                        if d >= depth_max:
                            S[done] = True; S[res] = f"sweep {pm(S[sw])} CISD {pm(m)} depth {d:.2f} -> SKIP deep"
                        else:
                            S[cisd], S[cmin] = j, m
                            f = first_fvg(h, l, j, k, bull, min_gap)
                            if f:
                                S[done] = True
                                S[res] = f"sweep {pm(S[sw])} CISD {pm(m)} depth {d:.2f} FVG {(f[2]-f[1])/pip:.1f}p {pm(minute[f[0]])} -> SIGNAL {tag}"
            else:
                b, t = (h[j - 2], l[j]) if bull else (h[j], l[j - 2])
                S[done] = True
                if t - b >= min_gap and t > b:
                    S[res] = f"sweep {pm(S[sw])} CISD {pm(S[cmin])} depth {S[dep]:.2f} FVG {(t-b)/pip:.1f}p {pm(m)} -> SIGNAL {tag}"
                else:
                    S[res] = f"sweep {pm(S[sw])} CISD {pm(S[cmin])} depth {S[dep]:.2f} -> SKIP no FVG"
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pair"); ap.add_argument("--days", type=int, default=10); ap.add_argument("--end", default=None)
    ap.add_argument("--min-fvg", type=float, default=0.5); ap.add_argument("--csv", default=None)
    a = ap.parse_args()
    path = a.csv or os.path.join(HERE, "..", "..", "data", "m1", f"{a.pair}_M1_UTC_dukascopy.csv")
    df = pd.read_csv(path, parse_dates=["ts_utc"]); df["ts_utc"] = df["ts_utc"].dt.tz_localize("UTC")
    df = df.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)
    end = pd.Timestamp(a.end, tz=TZ) + pd.Timedelta(days=1) if a.end else None
    if end: df = df[df["ts_utc"] < end.tz_convert("UTC")]
    df = df.tail((a.days + 3) * 1440 + 26 * 60).reset_index(drop=True)   # window + ATR warm-up
    rows = run(df, a.pair, a.days, a.end, a.min_fvg)
    print(f"# {a.pair} | {os.path.basename(path)} | rule v1.1 | min FVG {a.min_fvg} pip | last {a.days} days | {len(rows)} hours")
    for r in reversed(rows): print(r)

if __name__ == "__main__":
    main()
