#!/usr/bin/env python3
"""Risk/reward, SL/TP simulation and session-direction statistics for the London (02-04 NY) and NY AM
(08-10 NY) killzones on Tue/Wed/Thu. Reuses primitives from po3_amd_killzone.py.

Usage: python3 po3_rr_session.py EURUSD,GBPUSD,USDJPY out.md

Trade model (bullish wording, bearish mirrored by negation):
  setup   real-time: hour opens inside previous hour's range, sweeps its low within 30 min, then CISD / MSS within 60 bars
  entry   close of the confirming M1 bar; SL variants below; TP variants below; time exit at market after 60 bars
  cost    1 pip round trip (0.0001, or 0.01 for JPY pairs)
  SL-first rule: if SL and TP are both touched in the same bar, count it as SL (conservative)
"""
import sys, math
import numpy as np, pandas as pd
sys.path.insert(0, __import__("os").path.dirname(__file__))
from po3_amd_killzone import (Series, load_m1, random_walk_m1, swing_high_level, cisd_level, first_close_above,
                              wilson, pct, md, KZ, WDS, SWEEP_MAX_MIN, WIN, R_DIR, WICK_MIN)

PIP = {"USDJPY": 0.01}
HOURS = (3, 9)
COST_PIPS = 1.0
SL_VARIANTS = {"cực trị": 0.0, "cực trị + 0,1 ATR": 0.1, "cực trị + 0,25 ATR": 0.25}
TP_R = [1.0, 1.5, 2.0, 3.0]

def h1_rr(S, i, sign, pair):
    """Directional H1 candle (lookahead): distance conf->extreme and conf->H1 high."""
    o, h, l, c = S.view(sign); s, e = S.s[i], S.e[i]
    O, H, L, C = o[s], h[s:e].max(), l[s:e].min(), c[e - 1]
    rng = H - L
    if rng <= 0 or C <= O or (C - O) / rng < R_DIR or (O - L) / rng < WICK_MIN: return None
    idx_m = s + int(np.argmin(l[s:e]))
    if idx_m == s: return None
    out = dict(pair=pair, kz=S.kz[i], wd=S.wdn[i], atr=S.atr[i], pip=PIP.get(pair, 1e-4))
    lvl = swing_high_level(h, idx_m, s); idx_mss = first_close_above(c, lvl, idx_m + 1, e) if lvl is not None else None
    idx_cisd = first_close_above(c, cisd_level(o, c, idx_m, s), idx_m + 1, e)
    for name, idx in (("cisd", idx_cisd), ("mss", idx_mss)):
        if idx is None: out[f"{name}_risk"] = np.nan; continue
        entry = c[idx]; risk = entry - L
        out[f"{name}_risk"] = risk; out[f"{name}_reward"] = H - entry; out[f"{name}_min"] = S.minute[idx]
        out[f"{name}_risk_atr"] = risk / S.atr[i]; out[f"{name}_rr"] = (H - entry) / risk if risk > 0 else np.nan
        out[f"{name}_risk_pips"] = risk / out["pip"]
    return out

def rt_setups(S, i, sign, pair):
    """Real-time sweep -> confirmation. Returns dict with prices for simulation, or None."""
    if not S.prev_ok[i]: return None
    o, h, l, c = S.view(sign); s, e = S.s[i], S.e[i]; N = len(o)
    ps, pe = S.s[i - 1], S.e[i - 1]
    PL = l[ps:pe].min(); PH = h[ps:pe].max()
    if o[s] < PL: return None
    sweep = next((j for j in range(s, e) if S.minute[j] <= SWEEP_MAX_MIN and l[j] < PL), None)
    if sweep is None: return None
    rec = dict(pair=pair, kz=S.kz[i], wd=S.wdn[i], hour_ny=S.hour_ny[i], sign=sign, atr=S.atr[i], pip=PIP.get(pair, 1e-4),
               sweep_min=S.minute[sweep], PH=PH, PL=PL, e=e, cisd=None, mss=None, lo=None)
    lo = sweep; got = {}
    for j in range(sweep, min(sweep + WIN, N)):
        if l[j] < l[lo]: lo = j
        if j == lo: continue
        if "mss" not in got:
            lvl = swing_high_level(h, lo, max(lo - 60, 0))
            if lvl is not None and c[j] > lvl: got["mss"] = (j, lo)
        if "cisd" not in got:
            if c[j] > cisd_level(o, c, lo, max(lo - 60, 0)): got["cisd"] = (j, lo)
        if len(got) == 2: break
    if not got: return None
    rec["lo"] = lo; rec["low_px"] = l[lo]; rec["sweep_depth_atr"] = (PL - l[lo]) / S.atr[i]
    for k, (j, lo_k) in got.items():
        rec[k] = j; rec[f"{k}_min"] = S.minute[j]; rec[f"{k}_entry"] = c[j]; rec[f"{k}_lo"] = lo_k; rec[f"{k}_low_px"] = l[lo_k]
        rec[f"{k}_depth_atr"] = (PL - l[lo_k]) / S.atr[i]   # sweep depth KNOWN AT CONFIRMATION (no lookahead)
        rec[f"{k}_risk"] = c[j] - l[lo_k]; rec[f"{k}_risk_atr"] = rec[f"{k}_risk"] / S.atr[i]
        end = min(j + 1 + WIN, N)
        rec[f"{k}_mfe"] = h[j + 1:end].max() - c[j] if end > j + 1 else np.nan
        hit = next((x for x in range(j + 1, end) if l[x] < l[lo_k]), None)   # SL (extreme) touched?
        rec[f"{k}_sl_hit"] = hit is not None
        hit = end if hit is None else hit
        rec[f"{k}_mfe_pre_sl"] = h[j + 1:hit].max() - c[j] if hit > j + 1 else 0.0
    return rec

def simulate(S, rec, conf, sl_buf_atr, tp_kind, time_stop="60"):
    """One trade. Returns R multiple net of cost, and outcome label."""
    o, h, l, c = S.view(rec["sign"]); N = len(o)
    j = rec[conf]
    if j is None: return None
    entry = c[j]; sl = rec[f"{conf}_low_px"] - sl_buf_atr * rec["atr"]; risk = entry - sl
    if risk <= 0: return None
    cost = COST_PIPS * rec["pip"] / risk
    if isinstance(tp_kind, float): tp = entry + tp_kind * risk
    elif tp_kind == "PH": tp = rec["PH"]
    else: raise ValueError
    if tp <= entry: return None
    end = min(j + 1 + WIN, N) if time_stop == "60" else min(rec["e"], N)
    for x in range(j + 1, end):
        if l[x] <= sl: return -1.0 - cost, "SL", cost
        if h[x] >= tp: return (tp - entry) / risk - cost, "TP", cost
    if end <= j + 1: return None
    return (c[end - 1] - entry) / risk - cost, "time", cost

def sim_table(S_by_pair, recs, conf, label_rows):
    rows = []
    for label, sel in label_rows:
        ts = "hour" if "thoát cuối giờ" in label else "60"
        for sl_name, buf in SL_VARIANTS.items():
            for tp in TP_R + ["PH"]:
                res = [simulate(S_by_pair[r["pair"]], r, conf, buf, tp, ts) for r in sel]
                res = [x for x in res if x is not None]
                if not res: continue
                R = np.array([x[0] for x in res]); lab = np.array([x[1] for x in res]); n = len(R); cst = np.mean([x[2] for x in res])
                rows.append({"Tập": label, "SL": sl_name, "TP": (f"{tp:g}R" if isinstance(tp, float) else "đỉnh giờ trước"), "n": n,
                             "P(TP)": f"{100*(lab=='TP').mean():.1f}%", "P(SL)": f"{100*(lab=='SL').mean():.1f}%", "P(thoát giờ)": f"{100*(lab=='time').mean():.1f}%",
                             "R TB thoát giờ": f"{R[lab=='time'].mean():+.2f}" if (lab == 'time').any() else "", "Kỳ vọng trước phí (R)": f"{R.mean()+cst:+.3f}", "phí TB (R)": f"{cst:.2f}", "Kỳ vọng (R)": f"{R.mean():+.3f}",
                             "Kỳ vọng [CI95]": f"[{R.mean()-1.96*R.std()/math.sqrt(n):+.3f}, {R.mean()+1.96*R.std()/math.sqrt(n):+.3f}]"})
    return pd.DataFrame(rows).set_index("Tập")

# ---------------------------------------------------------------- bias of the 03:00 / 09:00 candle
def predictors(S, i):
    """Signed predictors (+1 up / -1 down / 0 none) known at the open of hour i, and the target = candle direction."""
    if not S.prev_ok[i]: return None
    O, C = S.H1o[i], S.H1c[i]; rng = S.H1h[i] - S.H1l[i]
    if rng <= 0 or C == O: return None
    hr = S.hour_ny[i]
    # previous hour (must be adjacent & valid)
    p1 = i - 1
    # session block: hours 19..01 (Asia) for 03:00; hours 02..07 for 09:00 -> collect valid hours of the same trading day before hour i
    blk = list(range(19, 24)) + [0, 1] if hr == 3 else list(range(2, 8))
    js = []
    for j in range(i - 1, max(i - 12, -1), -1):
        if S.hour_ny[j] in blk and S.valid[j]: js.append(j)
        elif S.hour_ny[j] not in blk and S.hour_ny[j] != (hr - 1 if hr == 9 else 2): break
    js = sorted(js)
    if hr == 3: js = [j for j in js if S.hour_ny[j] != 2]
    if len(js) < 4: return None
    so, sc, sh, sl = S.H1o[js[0]], S.H1c[js[-1]], S.H1h[js].max(), S.H1l[js].min()
    # ICT day open: 17:00 of the day that started this trading day; midnight open
    day_open = None; mid_open = None
    for j in range(i - 1, max(i - 30, -1), -1):
        if S.hour_ny[j] == 0 and mid_open is None: mid_open = S.H1o[j]
        if S.hour_ny[j] == 17: day_open = S.H1o[j]; break
    # previous ICT day: from hour 17 (two evenings ago) to hour 16 (previous evening)
    prev_day = None
    if day_open is not None:
        k17 = next((j for j in range(i - 1, max(i - 30, -1), -1) if S.hour_ny[j] == 17), None)
        if k17 is not None:
            k17b = next((j for j in range(k17 - 1, max(k17 - 30, -1), -1) if S.hour_ny[j] == 17), None)
            if k17b is not None: prev_day = np.sign(S.H1c[k17 - 1] - S.H1o[k17b])
    ph_dir = np.sign(S.H1c[p1] - S.H1o[p1]); p2 = np.sign(S.H1c[p1] - S.H1o[p1 - 1]) if S.prev_ok[p1] else 0
    sess_dir = np.sign(sc - so)
    swept_lo = S.H1l[p1] < sl; swept_hi = S.H1h[p1] > sh
    nxt_ok = i + 1 < len(S.hours) and S.valid[i + 1] and (S.hours[i + 1] - S.hours[i]) == pd.Timedelta("1h")
    rec = dict(hour=hr, wd=S.wdn[i], target=np.sign(C - O), directional=abs(C - O) / rng >= R_DIR, body_atr=abs(C - O) / S.atr[i],
               target_2h=(np.sign(S.H1c[i + 1] - O) if nxt_ok else 0),
               prev_hour=ph_dir, prev_2h=p2, prev_session=sess_dir, prev_day=prev_day if prev_day is not None else 0,
               prev_hour_body_atr=abs(S.H1c[p1] - S.H1o[p1]) / S.atr[i],
               prev_hour_swept=(1 if swept_lo and not swept_hi else -1 if swept_hi and not swept_lo else 0),
               open_vs_day_open=(0 if day_open is None else np.sign(day_open - O)),   # +1 = open below day open (discount) -> predict up
               open_vs_midnight=(0 if mid_open is None else np.sign(mid_open - O)),
               open_vs_session_mid=np.sign((sh + sl) / 2 - O),
               agree_hour_session=(ph_dir if ph_dir == sess_dir and ph_dir != 0 else 0),
               prev_hour_closed_outside=(1 if S.H1c[p1] > sh else -1 if S.H1c[p1] < sl else 0))
    return rec

PRED_LABELS = [("prev_hour", "Giờ liền trước (02:00 / 08:00): nến kế tiếp cùng chiều"),
               ("prev_2h", "Hai giờ liền trước (net): cùng chiều"),
               ("prev_session", "Phiên liền trước (Á 19–01 cho 03:00; London 02–07 cho 09:00): cùng chiều"),
               ("prev_day", "Ngày ICT liền trước (17:00→17:00): cùng chiều"),
               ("agree_hour_session", "Giờ trước VÀ phiên trước cùng chiều: nến theo chiều đó"),
               ("prev_hour_closed_outside", "Giờ trước ĐÓNG CỬA ngoài biên phiên trước: nến theo chiều phá vỡ"),
               ("prev_hour_swept", "Giờ trước quét một phía biên phiên trước: nến đi NGƯỢC lại (quét đáy → tăng)"),
               ("open_vs_session_mid", "Mở cửa dưới điểm giữa biên phiên trước → tăng (hồi về giữa)"),
               ("open_vs_midnight", "Mở cửa dưới giá mở 00:00 → tăng (discount so với midnight open)"),
               ("open_vs_day_open", "Mở cửa dưới giá mở ngày 17:00 → tăng (discount so với daily open)")]

def bias_rows(P, P0):
    rows = []
    for hr in HOURS:
        for key, label in PRED_LABELS:
            row = {"Yếu tố": label, "giờ": f"{hr:02d}:00"}
            for tag, D in (("FX", P), ("RW", P0)):
                d = D[(D["hour"] == hr) & (D[key] != 0)]; n = len(d)
                if n == 0: row[f"{tag} n"] = 0; continue
                same = d["target"] == d[key]
                row[f"{tag} n"] = n; row[f"{tag} P(cùng chiều dự báo)"] = pct(int(same.sum()), n)
                if tag == "FX":
                    dd = d[d["directional"]]
                    row["FX P(dự báo đúng | nến định hướng)"] = pct(int((dd["target"] == dd[key]).sum()), len(dd)) if len(dd) else ""
                    row["FX thân/ATR khi đúng vs sai"] = f"{d.loc[same, 'body_atr'].mean():.2f} / {d.loc[~same, 'body_atr'].mean():.2f}"
                    d2 = d[d["target_2h"] != 0]
                    row["FX P(cùng chiều | khối 2 giờ 03–04 / 09–10)"] = pct(int((d2["target_2h"] == d2[key]).sum()), len(d2)) if len(d2) else ""
            rows.append(row)
    return pd.DataFrame(rows).set_index("Yếu tố")

def main():
    pairs = sys.argv[1].split(","); outp = sys.argv[2]
    S_by = {}; H1 = []; RT = []; SESS = []
    for p in pairs:
        S = Series(load_m1(f"data/m1/{p}_M1_UTC.csv")); S_by[p] = S
        for i in range(len(S.hours)):
            if not (S.valid[i] and S.in_scope[i] and S.hour_ny[i] in HOURS) or not np.isfinite(S.atr[i]) or S.atr[i] <= 0: continue
            for sign in (1, -1):
                r = h1_rr(S, i, sign, p)
                if r: H1.append(r)
                r = rt_setups(S, i, sign, p)
                if r: RT.append(r)
        print(p, len(H1), len(RT), flush=True)
    S0 = Series(random_walk_m1(30000), scope=False); S_by["RW"] = S0
    RT0 = []; H10 = []
    for i in range(len(S0.hours)):
        if not (S0.valid[i] and S0.hour_ny[i] in HOURS) or not np.isfinite(S0.atr[i]) or S0.atr[i] <= 0: continue
        for sign in (1, -1):
            r = h1_rr(S0, i, sign, "RW"); H10.append(r) if r else None
            r = rt_setups(S0, i, sign, "RW"); RT0.append(r) if r else None
    print("RW", len(H10), len(RT0), flush=True)
    H1 = pd.DataFrame(H1); H10 = pd.DataFrame(H10)
    RTd = pd.DataFrame(RT); RT0d = pd.DataFrame(RT0)

    out = [f"# Rủi ro/lợi nhuận sau CISD và MSS, SL/TP, và bias của nến 03:00 và 09:00 — thứ Ba/Tư/Năm (FX)\n",
           f"Cặp: {', '.join(pairs)}, M1 histdata. Phạm vi: CHỈ nến H1 03:00 và 09:00 giờ New York, thứ Ba/Tư/Năm. Nền: bước ngẫu nhiên 30.000 giờ cùng pipeline, cũng chỉ lấy giờ 03 và 09. "
           f"Phí giả định {COST_PIPS:g} pip mỗi lệnh (khứ hồi). Quy ước: nếu SL và TP cùng bị chạm trong một nến M1 thì tính là SL.\n"]

    # ---------------- 1. RR
    out.append("## 1. Khoảng cách từ CISD/MSS đến cực trị thao túng và đến đỉnh\n")
    out.append("### 1a. Nến H1 định hướng đã biết (có nhìn trước)\n")
    out.append("Vào lệnh tại giá đóng nến M1 xác nhận. Rủi ro = vào lệnh trừ cực trị thao túng. Lợi nhuận = đỉnh H1 trừ vào lệnh. R = lợi nhuận / rủi ro.\n")
    rows = []
    def rr_row(g, label, k):
        g = g[g[f"{k}_risk"].notna() & (g[f"{k}_risk"] > 0)]; n = len(g)
        if n == 0: return None
        rr = g[f"{k}_rr"]
        return pd.Series({"xác nhận": k.upper(), "n": n, "phút xác nhận (trung vị)": g[f"{k}_min"].median(),
                          "rủi ro / ATR (trung vị)": f"{g[f'{k}_risk_atr'].median():.2f}", "rủi ro / ATR (p25–p75)": f"{g[f'{k}_risk_atr'].quantile(.25):.2f}–{g[f'{k}_risk_atr'].quantile(.75):.2f}",
                          "rủi ro pip (trung vị)": f"{g[f'{k}_risk_pips'].median():.1f}" if label not in ("Bước ngẫu nhiên",) else "",
                          "R đến đỉnh (trung vị)": f"{rr.median():.2f}", "R (p25–p75)": f"{rr.quantile(.25):.2f}–{rr.quantile(.75):.2f}",
                          "P(R ≥ 1)": f"{100*(rr>=1).mean():.0f}%", "P(R ≥ 2)": f"{100*(rr>=2).mean():.0f}%", "P(R ≥ 3)": f"{100*(rr>=3).mean():.0f}%"}, name=label)
    grp = [("Tất cả", H1), ("03:00", H1[H1["kz"] == "London"]), ("09:00", H1[H1["kz"] == "NY_AM"])] + [(p, H1[H1["pair"] == p]) for p in pairs] + [("Bước ngẫu nhiên", H10)]
    for k in ("cisd", "mss"):
        for label, g in grp:
            r = rr_row(g, label, k)
            if r is not None: rows.append(r)
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))

    out.append("\n### 1b. Thiết lập thời gian thực (không nhìn trước)\n")
    out.append("Mẫu như mục 3b của báo cáo trước. MFE = mức đi có lợi tối đa trong 60 nến M1 sau xác nhận. \"MFE trước SL\" = MFE tính đến lúc giá phá cực trị thao túng (0 nếu phá ngay).\n")
    rows = []
    def rt_row(g, label, k):
        g = g[g[k].notna() & (g[f"{k}_risk"] > 0)]; n = len(g)
        if n == 0: return None
        R = g[f"{k}_mfe_pre_sl"] / g[f"{k}_risk"]
        return pd.Series({"xác nhận": k.upper(), "n": n, "phút xác nhận (trung vị)": g[f"{k}_min"].median(),
                          "rủi ro / ATR (trung vị)": f"{g[f'{k}_risk_atr'].median():.2f}", "rủi ro / ATR (p25–p75)": f"{g[f'{k}_risk_atr'].quantile(.25):.2f}–{g[f'{k}_risk_atr'].quantile(.75):.2f}",
                          "rủi ro pip (trung vị)": f"{(g[f'{k}_risk']/g['pip']).median():.1f}" if label != "Bước ngẫu nhiên" else "",
                          "MFE trước SL, R (trung vị)": f"{R.median():.2f}", "P(MFE ≥ 1R trước SL)": f"{100*(R>=1).mean():.0f}%",
                          "P(≥ 1,5R)": f"{100*(R>=1.5).mean():.0f}%", "P(≥ 2R)": f"{100*(R>=2).mean():.0f}%", "P(≥ 3R)": f"{100*(R>=3).mean():.0f}%",
                          "P(phá cực trị trong 60 phút)": f"{100*g[f'{k}_sl_hit'].mean():.0f}%"}, name=label)
    for k in ("cisd", "mss"):
        dk = f"{k}_depth_atr"
        grp_rt = [("Tất cả", RTd), ("03:00", RTd[RTd["kz"] == "London"]), ("09:00", RTd[RTd["kz"] == "NY_AM"]),
                  ("Quét nông < 0,25 ATR (đo lúc xác nhận)", RTd[RTd[dk] < 0.25]), ("Quét sâu ≥ 0,5 ATR (đo lúc xác nhận)", RTd[RTd[dk] >= 0.5]),
                  ("Quét nông theo đáy cuối (CÓ nhìn trước, chỉ để đối chiếu)", RTd[RTd["sweep_depth_atr"] < 0.25]), ("Bước ngẫu nhiên", RT0d)]
        for label, g in grp_rt:
            r = rt_row(g, label, k)
            if r is not None: rows.append(r)
    t = pd.DataFrame(rows); t.index.name = "Tập"; out.append(md(t))

    # ---------------- 2. SL/TP simulation
    out.append("\n## 2. Mô phỏng SL/TP trên thiết lập thời gian thực\n")
    out.append("Vào lệnh tại giá đóng nến xác nhận. SL: dưới cực trị thao túng, có hoặc không có đệm theo ATR. TP: bội số R của rủi ro thực tế, hoặc đỉnh giờ trước. "
               "Không chạm gì trong 60 nến M1 thì thoát tại giá đóng (\"thoát giờ\"). Kỳ vọng tính bằng R đã trừ phí. Khoảng tin cậy 95% theo sai số chuẩn.\n")
    for conf in ("cisd", "mss"):
        dk = f"{conf}_depth_atr"
        sel_rows = [("Tất cả", RT), ("03:00", [r for r in RT if r["kz"] == "London"]), ("09:00", [r for r in RT if r["kz"] == "NY_AM"]),
                    ("Quét nông < 0,25 ATR", [r for r in RT if r.get(dk, 9) < 0.25]),
                    ("Quét nông, xác nhận ≤ phút 30", [r for r in RT if r.get(dk, 9) < 0.25]),
                    ("Quét nông, xác nhận ≤ phút 30, thoát cuối giờ", [r for r in RT if r.get(dk, 9) < 0.25]),
                    ("Quét nông theo đáy cuối (CÓ nhìn trước), ≤ phút 30, thoát cuối giờ", [r for r in RT if r["sweep_depth_atr"] < 0.25]),
                    ("Bước ngẫu nhiên", RT0)]
        out.append(f"\n### 2{'a' if conf=='cisd' else 'b'}. Xác nhận bằng {conf.upper()}\n")
        rows_sel = []
        for label, sel in sel_rows:
            sel = [r for r in sel if r[conf] is not None]
            if "≤ phút 30" in label: sel = [r for r in sel if r[f"{conf}_min"] <= 30]
            rows_sel.append((label, sel))
        out.append(md(sim_table(S_by, RT, conf, rows_sel)))

    # ---------------- 3. bias of the 03:00 / 09:00 candle
    out.append("\n## 3. Nến 03:00 và 09:00 có bias theo thông tin nào trước đó?\n")
    out.append("Mỗi dòng là một yếu tố biết được TẠI LÚC MỞ nến. \"Cùng chiều dự báo\" = hướng đóng cửa của nến trùng với hướng yếu tố gợi ý. "
               "Nền bước ngẫu nhiên phải cho 50%; mọi yếu tố dưới đây cũng được tính trên nền để loại ảo giác do cấu trúc (ví dụ quét đáy rồi tăng là cơ học một phần). "
               "Cột cuối: thân/ATR trung bình của nến khi dự báo đúng so với khi sai, để biết bias có đi kèm nến lớn không.\n")
    P = []; P0 = []
    for p, S in S_by.items():
        for i in range(len(S.hours)):
            if not (S.valid[i] and S.hour_ny[i] in HOURS) or not np.isfinite(S.atr[i]) or S.atr[i] <= 0: continue
            if p != "RW" and not S.in_scope[i]: continue
            r = predictors(S, i)
            if r: r["pair"] = p; (P0 if p == "RW" else P).append(r)
    P = pd.DataFrame(P); P0 = pd.DataFrame(P0)
    out.append(md(bias_rows(P, P0)))
    out.append("\nTheo ngày trong tuần, ba yếu tố chính (FX, P(cùng chiều dự báo)):\n")
    rows = []
    for hr in HOURS:
        for wd in ("Tue", "Wed", "Thu"):
            d = P[(P["hour"] == hr) & (P["wd"] == wd)]; row = {"giờ": f"{hr:02d}:00", "ngày": wd, "n": len(d)}
            for key, label in PRED_LABELS[:1] + PRED_LABELS[2:3] + PRED_LABELS[6:7]:
                dd = d[d[key] != 0]; row[label.split(":")[0][:40]] = pct(int((dd["target"] == dd[key]).sum()), len(dd)) if len(dd) else ""
            rows.append(row)
    out.append(md(pd.DataFrame(rows).set_index("giờ")))
    out.append("\nGiờ liền trước theo độ lớn thân (thân/ATR chia ba phần): nến 03:00/09:00 có tiếp diễn hay đảo chiều?\n")
    rows = []
    for hr in HOURS:
        d = P[(P["hour"] == hr) & (P["prev_hour"] != 0)].copy(); d["ter"] = pd.qcut(d["prev_hour_body_atr"], 3, labels=["nhỏ", "vừa", "lớn"])
        for t, g in d.groupby("ter", observed=True):
            rows.append({"giờ": f"{hr:02d}:00", "thân giờ trước": f"{t} (≤{g['prev_hour_body_atr'].max():.2f} ATR)", "n": len(g),
                         "P(cùng chiều giờ trước)": pct(int((g["target"] == g["prev_hour"]).sum()), len(g)),
                         "P(cùng chiều | nến định hướng)": pct(int((g[g["directional"]]["target"] == g[g["directional"]]["prev_hour"]).sum()), int(g["directional"].sum()))})
    out.append(md(pd.DataFrame(rows).set_index("giờ")))
    P.to_csv(outp.replace(".md", "_bias.csv"), index=False)
    open(outp, "w").write("\n".join(out)); print("written", outp)

if __name__ == "__main__":
    main()
