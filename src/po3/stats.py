"""Statistics on derived H1 features. Every table is a plain pandas object or dict; rendering lives in report.py."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config

WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


def zscore(p_hat: float, p0: float, n: int) -> float:
    if n == 0 or p0 <= 0 or p0 >= 1:
        return float("nan")
    return (p_hat - p0) / math.sqrt(p0 * (1 - p0) / n)


# ----------------------------------------------------------------------------- selections
def manip_set(d: pd.DataFrame, wick_min: float | None = None) -> pd.DataFrame:
    cfg = config.load()
    w = cfg["candle"]["manipulation_wick_min"] if wick_min is None else wick_min
    return d[d["directional"] & (d["wick_open"] >= w) & d["min_manip"].notna()]


# ----------------------------------------------------------------------------- minute distribution
def minute_summary(m: pd.Series) -> dict:
    """Bins, <=25 share, median, minute-0 share for a Series of manipulation-extreme minutes."""
    cfg = config.load()
    n = int(len(m))
    out = {"n": n}
    for a, b in cfg["bins"]["minute_bins"]:
        out[f"{a:02d}-{b:02d}"] = float(((m >= a) & (m <= b)).mean()) if n else float("nan")
    out["le25"] = float((m <= 25).mean()) if n else float("nan")
    out["median"] = float(m.median()) if n else float("nan")
    out["min0"] = float((m == 0).mean()) if n else float("nan")
    return out


def cdf(m: pd.Series, minutes=None) -> dict[int, float]:
    minutes = minutes or config.load()["bins"]["cdf_minutes"]
    return {k: float((m <= k).mean()) if len(m) else float("nan") for k in minutes}


def minute_by_group(d: pd.DataFrame, key: str, wick_min: float | None = None) -> pd.DataFrame:
    x = manip_set(d, wick_min)
    rows = {"ALL": minute_summary(x["min_manip"])}
    for g, sub in x.groupby(key):
        rows[str(g)] = minute_summary(sub["min_manip"])
    return pd.DataFrame(rows).T


def cdf_by_session(d: pd.DataFrame, wick_min: float | None = None) -> pd.DataFrame:
    x = manip_set(d, wick_min)
    rows = {"ALL": cdf(x["min_manip"])}
    for s, sub in x.groupby("session"):
        rows[s] = cdf(sub["min_manip"])
    return pd.DataFrame(rows).T


# ----------------------------------------------------------------------------- monthly monitor
def compare_to_baseline(month: pd.DataFrame, base: pd.DataFrame) -> dict:
    """Month vs baseline for the key proportions; returns values, z-scores and alert flags."""
    cfg = config.load()
    z_alert = cfg["monitor"]["z_alert"]
    xm, xb = manip_set(month), manip_set(base)
    sm, sb = minute_summary(xm["min_manip"]), minute_summary(xb["min_manip"])
    keys = [k for k in sm if k not in ("n", "median")]
    res = {"n_month": sm["n"], "n_base": sb["n"], "median_month": sm["median"], "median_base": sb["median"], "metrics": {}}
    for k in keys:
        z = zscore(sm[k], sb[k], sm["n"])
        res["metrics"][k] = {"month": sm[k], "base": sb[k], "z": z, "alert": bool(abs(z) >= z_alert) if not math.isnan(z) else False}
    res["any_alert"] = any(v["alert"] for v in res["metrics"].values())
    return res


def coverage(facts: pd.DataFrame, year: int, month: int) -> dict:
    """Share of weekday hours (Mon-Fri, UTC) present with enough M1 bars."""
    cfg = config.load()
    idx = pd.date_range(f"{year}-{month:02d}-01", periods=pd.Period(f"{year}-{month:02d}").days_in_month * 24, freq="h", tz="UTC")
    expected = idx[idx.weekday < 5]
    have = facts[(facts["n_m1"] >= cfg["candle"]["min_m1_per_hour"])]["ts_utc"]
    ok = expected.isin(have)
    return {"expected": int(len(expected)), "present": int(ok.sum()), "coverage": float(ok.mean()) if len(expected) else float("nan"),
            "flag": bool(ok.mean() < cfg["monitor"]["min_coverage"]) if len(expected) else True}


# ----------------------------------------------------------------------------- tables
def hour_table(d: pd.DataFrame) -> pd.DataFrame:
    cfg = config.load()
    g = d.groupby("hour_ny")
    t = pd.DataFrame({
        "n": g.size(),
        "body_atr": g["body_atr"].mean(),
        "range_atr": g["range_atr"].mean(),
        "p_exp": g.apply(lambda z: ((z["r"] >= cfg["profile"]["classic_body_min"]) & (z["range_atr"] >= cfg["profile"]["classic_range_atr_min"])).mean()),
        "p_classic": g["profile"].apply(lambda s: (s == "ClassicExp").mean()),
        "p_news": g["profile"].apply(lambda s: (s == "News/Outlier").mean()),
    })
    t["session"] = [cfg["_session_of_hour"].get(h, "other") for h in t.index]
    return t


def profile_by_session(d: pd.DataFrame) -> pd.DataFrame:
    ct = pd.crosstab(d["session"], d["profile"], normalize="index")
    ct["n"] = d.groupby("session").size()
    order = list(config.load()["sessions"].keys()) + ["other"]
    return ct.reindex([o for o in order if o in ct.index])


def session_table(d: pd.DataFrame) -> pd.DataFrame:
    cfg = config.load()
    g = d.groupby("session")
    x = manip_set(d)
    t = pd.DataFrame({
        "n": g.size(),
        "mean_r": g["r"].mean(),
        "body_atr": g["body_atr"].mean(),
        "range_atr": g["range_atr"].mean(),
        "p_exp": g.apply(lambda z: ((z["r"] >= cfg["profile"]["classic_body_min"]) & (z["range_atr"] >= cfg["profile"]["classic_range_atr_min"])).mean()),
        "p_news": g["profile"].apply(lambda s: (s == "News/Outlier").mean()),
        "manip_median": x.groupby("session")["min_manip"].median(),
        "manip_le10": x.groupby("session")["min_manip"].apply(lambda m: (m <= 10).mean()),
    })
    order = list(cfg["sessions"].keys()) + ["other"]
    return t.reindex([o for o in order if o in t.index])


def weekday_table(d: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Weekly PO3: per weekday share of counter-extreme day, with-trend extreme day, largest with-trend body day."""
    day = d.groupby("date_ny").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    day.index = pd.to_datetime(day.index)
    day["wd"] = day.index.weekday
    day = day[day["wd"] <= 4]
    day["week"] = day.index.to_period("W-SAT")
    day["signed"] = day["close"] - day["open"]
    day["range"] = day["high"] - day["low"]
    rec = []
    for _, g in day.groupby("week"):
        if len(g) < 4:
            continue
        o, c = g["open"].iloc[0], g["close"].iloc[-1]
        if c == o:
            continue
        bull = c > o
        d_low, d_high = g["low"].idxmin().weekday(), g["high"].idxmax().weekday()
        sb = g["signed"] if bull else -g["signed"]
        rec.append((d_low if bull else d_high, d_high if bull else d_low, sb.idxmax().weekday()))
    r = pd.DataFrame(rec, columns=["manip", "with", "dist"])
    n = len(r)
    atr = day["range"].mean()
    rows = []
    for w in range(5):
        rows.append({"weekday": WD[w],
                     "manip": (r["manip"] == w).mean() if n else float("nan"),
                     "with": (r["with"] == w).mean() if n else float("nan"),
                     "dist": (r["dist"] == w).mean() if n else float("nan"),
                     "dist_ci": wilson(int((r["dist"] == w).sum()), n)[1:] if n else (float("nan"),) * 2,
                     "range_rel": day[day["wd"] == w]["range"].mean() / atr if atr else float("nan")})
    return pd.DataFrame(rows).set_index("weekday"), n


# ----------------------------------------------------------------------------- random-walk baselines
def random_walk_minutes(n_sim: int = 200_000, seed: int = 7) -> dict[str, dict]:
    cfg = config.load()
    rng = np.random.default_rng(seed)
    path = np.concatenate([np.zeros((n_sim, 1)), np.cumsum(rng.standard_normal((n_sim, 60)), axis=1)], axis=1)
    lo, hi, close = path.min(axis=1), path.max(axis=1), path[:, -1]
    rng_ = hi - lo
    r = np.abs(close) / rng_
    bull = close > 0
    wick_open = np.where(bull, -lo, hi) / rng_
    minute = np.clip(np.where(bull, path.argmin(axis=1), path.argmax(axis=1)) - 1, 0, 59)
    out = {}
    for w in (cfg["candle"]["manipulation_wick_min"], cfg["candle"]["manipulation_wick_strict"]):
        m = pd.Series(minute[(r >= cfg["candle"]["directional_body_ratio"]) & (wick_open >= w)])
        out[f"wick>={int(w*100)}%"] = minute_summary(m)
    return out


def random_walk_weekdays(n_sim: int = 200_000, seed: int = 11, steps: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    path = np.concatenate([np.zeros((n_sim, 1)), np.cumsum(rng.standard_normal((n_sim, 5 * steps)), axis=1)], axis=1)
    bull = path[:, -1] > 0
    days = path[:, 1:].reshape(n_sim, 5, steps)
    d_open = np.concatenate([np.zeros((n_sim, 1)), days[:, :-1, -1]], axis=1)
    d_close = days[:, :, -1]
    d_hi, d_lo = np.maximum(days.max(axis=2), d_open), np.minimum(days.min(axis=2), d_open)
    lo_day, hi_day = d_lo.argmin(axis=1), d_hi.argmax(axis=1)
    manip = np.where(bull, lo_day, hi_day)
    withd = np.where(bull, hi_day, lo_day)
    dist = ((d_close - d_open) * np.where(bull, 1, -1)[:, None]).argmax(axis=1)
    return pd.DataFrame({"manip": [np.mean(manip == w) for w in range(5)], "with": [np.mean(withd == w) for w in range(5)],
                         "dist": [np.mean(dist == w) for w in range(5)]}, index=WD[:5])
