"""Render monthly and annual reports (Markdown) and the short Telegram summary (HTML)."""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd

from . import config, features, stats
from .notify import esc

VN_SESSION = {"Asia": "Á", "London": "London", "NY_AM": "NY AM", "NY_PM": "NY PM", "other": "khác", "ALL": "Tất cả"}


def pc(x: float, d: int = 1) -> str:
    return "—" if pd.isna(x) else f"{100 * x:.{d}f}%"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(r) + " |" for r in rows])


def _minute_rows(t: pd.DataFrame) -> list[list[str]]:
    cfg = config.load()
    keys = [f"{a:02d}-{b:02d}" for a, b in cfg["bins"]["minute_bins"]]
    return [[VN_SESSION.get(i, i), str(int(r["n"]))] + [pc(r[k]) for k in keys] + [pc(r["le25"]), f"{r['median']:.0f}" if not pd.isna(r["median"]) else "—", pc(r["min0"])]
            for i, r in t.iterrows()]


MINUTE_HDR = ["Phiên", "n", "00–10", "11–25", "26–40", "41–59", "≤25", "trung vị", "phút 0"]


# ----------------------------------------------------------------------------- monthly
def monthly(year: int, month: int, pairs: list[str] | None = None, fetch_sources: dict | None = None) -> tuple[str, str]:
    """Return (markdown_report, telegram_html). fetch_sources: pair -> source name used this month."""
    cfg = config.load()
    pairs = pairs or cfg["pairs"]
    tag = f"{year}-{month:02d}"
    win = cfg["monitor"]["rolling_months"]
    period = pd.Period(tag, "M")
    md = [f"# PO3 H1 — Báo cáo tháng {tag}", "",
          f"Định nghĩa phiên bản {cfg['version']}. Sinh lúc {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. "
          f"Nền = toàn bộ lịch sử trừ tháng này. Cửa sổ trượt = {win} tháng gần nhất (kể cả tháng này).", ""]
    tg = [f"<b>PO3 tháng {tag}</b> · định nghĩa v{cfg['version']}"]
    any_alert = False
    for pair in pairs:
        facts = features.load_facts(pair)
        d = features.derive(facts)
        in_month = (d.index.year == year) & (d.index.month == month)
        dm, db = d[in_month], d[~in_month & (d.index < period.start_time.tz_localize("UTC"))]
        cov = stats.coverage(facts, year, month)
        cmp_ = stats.compare_to_baseline(dm, db)
        any_alert |= cmp_["any_alert"] or cov["flag"]
        src = (fetch_sources or {}).get(pair, "")
        # --- markdown
        md += [f"## {pair}", "",
               f"Nến H1 trong tháng: {int(in_month.sum())}; nến định hướng có râu thao túng: {cmp_['n_month']} (nền {cmp_['n_base']}). "
               f"Độ phủ giờ ngày thường: {pc(cov['coverage'])} ({cov['present']}/{cov['expected']})"
               + (" ⚠ thiếu dữ liệu" if cov["flag"] else "") + (f". Nguồn: {src}" if src else "") + ".", ""]
        rows = []
        for k, v in cmp_["metrics"].items():
            rows.append([k, pc(v["month"]), pc(v["base"]), f"{v['z']:+.1f}" if not pd.isna(v["z"]) else "—", "⚠" if v["alert"] else ""])
        md += ["### Phân bố phút tạo cực trị thao túng: tháng so với nền", "",
               md_table(["Chỉ số", "Tháng", "Nền", "z", "Cảnh báo"], rows), "",
               f"Trung vị phút: tháng {cmp_['median_month']:.0f}, nền {cmp_['median_base']:.0f}.", ""]
        # rolling window tables
        start = (period - (win - 1)).start_time.tz_localize("UTC")
        dw = d[(d.index >= start) & (d.index < (period + 1).start_time.tz_localize("UTC"))]
        tsess = stats.minute_by_group(dw, "session")
        md += [f"### Theo phiên (cửa sổ {win} tháng)", "", md_table(MINUTE_HDR, _minute_rows(tsess)), ""]
        ht = stats.hour_table(dw).sort_values("body_atr", ascending=False)
        top = ht.head(5)
        md += [f"### Giờ động lượng (cửa sổ {win} tháng, giờ New York, xếp theo thân/ATR)", "",
               md_table(["Giờ NY", "n", "thân/ATR", "biên độ/ATR", "P(mở rộng)", "tỷ lệ nến tin", "phiên"],
                        [[f"{h:02d}:00", str(int(r['n'])), f"{r['body_atr']:.2f}", f"{r['range_atr']:.2f}", pc(r['p_exp']), pc(r['p_news']), r['session']] for h, r in top.iterrows()]), ""]
        prof = stats.profile_by_session(dw)
        md += [f"### Profile theo phiên (cửa sổ {win} tháng)", "",
               md_table(["Phiên", "n"] + [c for c in prof.columns if c != "n"],
                        [[VN_SESSION.get(i, i), str(int(r["n"]))] + [pc(r[c]) for c in prof.columns if c != "n"] for i, r in prof.iterrows()]), ""]
        # --- telegram line
        m = cmp_["metrics"]
        flag = " ⚠" if cmp_["any_alert"] else ""
        covflag = " ⚠dữ liệu" if cov["flag"] else ""
        tg.append(f"<b>{pair}</b> n={cmp_['n_month']}{flag}{covflag}\n"
                  f"  00–10: {pc(m['00-10']['month'], 0)} (nền {pc(m['00-10']['base'], 0)}) · ≤25: {pc(m['le25']['month'], 0)} (nền {pc(m['le25']['base'], 0)}) · phút0: {pc(m['min0']['month'], 0)}\n"
                  f"  giờ mạnh ({win}th): " + ", ".join(f"{h:02d}:00" for h in top.index[:3]) + " NY")
    tg.append(("Có cảnh báo: xem báo cáo đính kèm." if any_alert else "Không có bất thường.") + " Định nghĩa: 00–10 = tỷ lệ cực trị thao túng trong 10 phút đầu; ≤25 = trong 25 phút đầu; phút0 = ngay phút mở cửa.")
    return "\n".join(md), "\n".join(tg)


# ----------------------------------------------------------------------------- annual
def annual(year: int, pairs: list[str] | None = None) -> tuple[str, str]:
    cfg = config.load()
    pairs = pairs or cfg["pairs"]
    md = [f"# PO3 H1 — Báo cáo năm {year}", "",
          f"Định nghĩa phiên bản {cfg['version']}. Sinh lúc {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. "
          "Mỗi bảng có hai phần: năm {year} và tích lũy toàn bộ lịch sử. Ngày trong tuần chỉ dùng số tích lũy.".replace("{year}", str(year)), ""]
    rw = stats.random_walk_minutes()
    rw_w = stats.random_walk_weekdays()
    tg = [f"<b>PO3 báo cáo năm {year}</b> · định nghĩa v{cfg['version']}"]
    for pair in pairs:
        d = features.derive(features.load_facts(pair))
        dy = d[d.index.year == year]
        md += [f"## {pair}", "", f"Nến H1: năm {len(dy)}, tích lũy {len(d)} ({d.index.min():%Y-%m-%d} → {d.index.max():%Y-%m-%d}).", ""]
        for label, dd in (("Năm", dy), ("Tích lũy", d)):
            t = stats.minute_by_group(dd, "session")
            md += [f"### Phút tạo cực trị thao túng — {label} (râu ≥ {int(cfg['candle']['manipulation_wick_min']*100)}%)", "", md_table(MINUTE_HDR, _minute_rows(t)), ""]
        rwk = f"wick>={int(cfg['candle']['manipulation_wick_min']*100)}%"
        r0 = rw[rwk]
        md += ["Mốc bước ngẫu nhiên (cùng bộ lọc): " + ", ".join(f"{k}: {pc(v)}" for k, v in r0.items() if k not in ("n", "median")) + f", trung vị {r0['median']:.0f}.", ""]
        ts = stats.minute_by_group(d, "session", cfg["candle"]["manipulation_wick_strict"])
        md += [f"### Ngưỡng râu nghiêm ≥ {int(cfg['candle']['manipulation_wick_strict']*100)}% — tích lũy", "", md_table(MINUTE_HDR, _minute_rows(ts)), ""]
        c = stats.cdf_by_session(d)
        md += ["### CDF theo phiên — tích lũy", "", md_table(["Phiên"] + [f"≤{k}" for k in c.columns], [[VN_SESSION.get(i, i)] + [pc(v, 0) for v in r] for i, r in c.iterrows()]), ""]
        d = d.assign(year=d.index.year.astype(str))
        by_year = stats.minute_by_group(d, "year") if len(d) else pd.DataFrame()
        if len(by_year):
            md += ["### Ổn định theo năm (tất cả phiên)", "", md_table(MINUTE_HDR, _minute_rows(by_year.drop(index="ALL"))), ""]
        st = stats.session_table(d)
        md += ["### Đặc trưng theo phiên — tích lũy", "",
               md_table(["Phiên", "n", "thân TB r", "thân/ATR", "biên độ/ATR", "P(mở rộng)", "nến tin", "trung vị phút thao túng", "thao túng ≤10'"],
                        [[VN_SESSION.get(i, i), str(int(r['n'])), f"{r['mean_r']:.2f}", f"{r['body_atr']:.2f}", f"{r['range_atr']:.2f}", pc(r['p_exp']), pc(r['p_news']), f"{r['manip_median']:.0f}", pc(r['manip_le10'], 0)] for i, r in st.iterrows()]), ""]
        for label, dd in (("Năm", dy), ("Tích lũy", d)):
            ht = stats.hour_table(dd)
            md += [f"### Giờ trong ngày (giờ New York) — {label}", "",
                   md_table(["Giờ", "n", "thân/ATR", "biên độ/ATR", "P(mở rộng)", "P(Classic)", "nến tin", "phiên"],
                            [[f"{h:02d}:00", str(int(r['n'])), f"{r['body_atr']:.2f}", f"{r['range_atr']:.2f}", pc(r['p_exp']), pc(r['p_classic']), pc(r['p_news']), r['session']] for h, r in ht.iterrows()]), ""]
            top = ht.sort_values("body_atr", ascending=False).head(5)
            md += ["Xếp hạng thân/ATR: " + ", ".join(f"{h:02d}:00 ({r['body_atr']:.2f})" for h, r in top.iterrows()), ""]
        prof = stats.profile_by_session(d)
        md += ["### Profile theo phiên — tích lũy", "",
               md_table(["Phiên", "n"] + [c_ for c_ in prof.columns if c_ != "n"],
                        [[VN_SESSION.get(i, i), str(int(r["n"]))] + [pc(r[c_]) for c_ in prof.columns if c_ != "n"] for i, r in prof.iterrows()]), ""]
        wt, nweeks = stats.weekday_table(d)
        wy, nwy = stats.weekday_table(dy)
        md += [f"### Ngày trong tuần — tích lũy {nweeks} tuần (năm {year}: {nwy} tuần, chỉ để tham khảo)", "",
               md_table(["Thứ", "thao túng (tích lũy)", "kết thúc phân phối (tích lũy)", "phân phối chính (tích lũy) [CI95]", f"phân phối chính (năm {year})", "biên độ ngày/TB", "ngẫu nhiên: thao túng / kết thúc / chính"],
                        [[i, pc(r["manip"]), pc(r["with"]), f"{pc(r['dist'])} [{pc(r['dist_ci'][0])}–{pc(r['dist_ci'][1])}]", pc(wy.loc[i, "dist"]), f"{r['range_rel']:.2f}",
                          f"{pc(rw_w.loc[i, 'manip'])} / {pc(rw_w.loc[i, 'with'])} / {pc(rw_w.loc[i, 'dist'])}"] for i, r in wt.iterrows()]), ""]
        tall = stats.minute_summary(stats.manip_set(d)["min_manip"])
        ty = stats.minute_summary(stats.manip_set(dy)["min_manip"])
        top_h = stats.hour_table(d).sort_values("body_atr", ascending=False).head(3)
        best_wd = wt["dist"].idxmax()
        tg.append(f"<b>{pair}</b> năm n={ty['n']} · 00–10: {pc(ty['00-10'], 0)} (tích lũy {pc(tall['00-10'], 0)}) · ≤25: {pc(ty['le25'], 0)} (tích lũy {pc(tall['le25'], 0)})\n"
                  f"  giờ mạnh: " + ", ".join(f"{h:02d}:00" for h in top_h.index) + f" NY · ngày phân phối chính: {best_wd} {pc(wt.loc[best_wd, 'dist'], 0)} ({nweeks} tuần)")
    md += ["## Ghi chú phương pháp", "",
           "Nến định hướng: thân ≥ 50% biên độ. Cực trị thao túng: đáy của nến tăng / đỉnh của nến giảm; phút = nến M1 đầu tiên chạm mức đó. "
           "Bước ngẫu nhiên: 200.000 nến giả lập 60 bước Gaussian với cùng bộ lọc; tuần giả lập 5 ngày × 24 bước. Khoảng tin cậy Wilson 95%. "
           "Ngưỡng và giờ phiên: `config/definitions.toml`. Đây là kỳ duy nhất được phép rà soát và đổi phiên bản định nghĩa.", ""]
    tg.append("Báo cáo chi tiết đính kèm. Đây là kỳ rà soát định nghĩa: đổi ngưỡng chỉ tại đây, kèm tăng version.")
    return "\n".join(md), "\n".join(tg)


def write_report(kind: str, tag: str, text: str) -> str:
    path = os.path.join(config.REPORTS_DIR, kind, tag, "report.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path
