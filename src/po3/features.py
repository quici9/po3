"""H1 facts (definition-independent) and derived features (definition-dependent).

facts: one row per H1 candle built from M1: ts_utc, open, high, low, close, volume, n_m1,
       min_low (minute of first touch of the hour's low), min_high, source.
derive(): adds NY-time fields, body/wick ratios, ATR-relative sizes, session, direction flags,
       manipulation-extreme minute and profile classification, all from config/definitions.toml.
"""
from __future__ import annotations

import gzip
import os

import numpy as np
import pandas as pd

from . import config

FACT_COLS = ["ts_utc", "open", "high", "low", "close", "volume", "n_m1", "min_low", "min_high", "source"]


def facts_from_m1(m1: pd.DataFrame, source: str) -> pd.DataFrame:
    if m1.empty:
        return pd.DataFrame(columns=FACT_COLS)
    m1 = m1.set_index("ts_utc").sort_index()
    hk = m1.index.floor("1h")
    g = m1.groupby(hk)
    h1 = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
               close=("close", "last"), volume=("volume", "sum"), n_m1=("open", "size"))
    h1["min_low"] = g["low"].idxmin().dt.minute.values
    h1["min_high"] = g["high"].idxmax().dt.minute.values
    h1["source"] = source
    h1 = h1.reset_index().rename(columns={"index": "ts_utc", "ts_utc": "ts_utc"})
    h1.columns = ["ts_utc"] + list(h1.columns[1:])
    return h1[FACT_COLS]


def facts_path(pair: str) -> str:
    return os.path.join(config.DATA_DIR, f"{pair}.csv.gz")


def load_facts(pair: str) -> pd.DataFrame:
    p = facts_path(pair)
    if not os.path.exists(p):
        return pd.DataFrame(columns=FACT_COLS)
    df = pd.read_csv(p, compression="gzip")
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def save_facts(pair: str, df: pd.DataFrame) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    df = df.drop_duplicates("ts_utc").sort_values("ts_utc")
    out = df.copy()
    out["ts_utc"] = out["ts_utc"].dt.strftime("%Y-%m-%d %H:%M:%S")
    with gzip.open(facts_path(pair), "wt", newline="") as f:
        out.to_csv(f, index=False)


def upsert_month(pair: str, month_facts: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """Replace all rows of (year, month) in the pair's facts with month_facts and save."""
    old = load_facts(pair)
    if not old.empty:
        keep = ~((old["ts_utc"].dt.year == year) & (old["ts_utc"].dt.month == month))
        old = old[keep]
    new = pd.concat([old, month_facts], ignore_index=True)
    save_facts(pair, new)
    return new


def derive(facts: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or config.load()
    c, p = cfg["candle"], cfg["profile"]
    d = facts.copy()
    d = d[d["n_m1"] >= c["min_m1_per_hour"]].set_index("ts_utc").sort_index()
    ny = d.index.tz_convert(cfg["timezone"])
    d["hour_ny"] = ny.hour
    d["wd"] = ny.weekday
    d["date_ny"] = ny.date
    d["session"] = d["hour_ny"].map(cfg["_session_of_hour"]).fillna("other")
    d["range"] = d["high"] - d["low"]
    d = d[d["range"] > 0]
    d["bull"] = d["close"] > d["open"]
    d["bear"] = d["close"] < d["open"]
    d["body"] = (d["close"] - d["open"]).abs()
    d["r"] = d["body"] / d["range"]
    d["wick_open"] = np.where(d["bull"], d["open"] - d["low"], d["high"] - d["open"]) / d["range"]
    d["wick_close"] = np.where(d["bull"], d["high"] - d["close"], d["close"] - d["low"]) / d["range"]
    d["atr"] = d["range"].rolling(c["atr_window"], min_periods=c["atr_window"] // 2).mean().shift(1)
    d["range_atr"] = d["range"] / d["atr"]
    d["body_atr"] = d["body"] / d["atr"]
    d["directional"] = d["r"] >= c["directional_body_ratio"]
    d["manip"] = d["wick_open"] >= c["manipulation_wick_min"]
    d["min_manip"] = np.where(d["bull"], d["min_low"], d["min_high"]).astype(float)
    d["min_with"] = np.where(d["bull"], d["min_high"], d["min_low"]).astype(float)
    d["seq_ok"] = d["min_manip"] < d["min_with"]
    prof = np.full(len(d), "Other", dtype=object)
    assigned = pd.Series(False, index=d.index)
    rules = [
        ("News/Outlier", d["range_atr"] >= p["news_range_atr"]),
        ("TrendRunaway", (d["r"] >= p["runaway_body"]) & (d["wick_open"] < p["runaway_wick_open_max"])),
        ("ClassicExp", (d["range_atr"] >= p["classic_range_atr_min"]) & (d["r"] >= p["classic_body_min"])
         & d["wick_open"].between(*p["classic_wick_open"]) & (d["wick_close"] <= p["classic_wick_close_max"]) & d["seq_ok"]),
        ("ConsolRev", (d["r"] < p["consol_body_max"]) & ((d["wick_open"] >= p["consol_wick_min"]) | (d["wick_close"] >= p["consol_wick_min"]))),
        ("Seek&Destroy", (d["r"] < p["sd_body_max"]) & (d["wick_open"] >= p["sd_wick_min"]) & (d["wick_close"] >= p["sd_wick_min"])),
    ]
    for name, cond in rules:
        cond = cond.fillna(False) & ~assigned
        prof[cond.values] = name
        assigned |= cond
    d["profile"] = prof
    return d
