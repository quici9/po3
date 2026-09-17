"""Fetch one calendar month of M1 candles for one pair.

Sources (tried in order): histdata.com (monthly ASCII zip, fixed EST -> UTC), Dukascopy datafeed
(daily bi5 files, UTC). Both return a DataFrame with columns ts_utc (tz-aware UTC), open, high, low,
close, volume, sorted and de-duplicated. Data from the internet is treated as untrusted: parsed
strictly, bounded in size, never executed.
"""
from __future__ import annotations

import calendar
import datetime as dt
import http.cookiejar
import io
import logging
import lzma
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

log = logging.getLogger("po3.fetch")
UA = {"User-Agent": "Mozilla/5.0 (po3-stats; +https://github.com/quici9/po3)"}
MAX_BYTES = 64 * 1024 * 1024
COLS = ["ts_utc", "open", "high", "low", "close", "volume"]


class FetchError(RuntimeError):
    pass


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLS)


def _finish(rows: list[tuple]) -> pd.DataFrame:
    if not rows:
        return _empty()
    df = pd.DataFrame(rows, columns=COLS)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.drop_duplicates("ts_utc").sort_values("ts_utc").reset_index(drop=True)
    for c in COLS[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


# ----------------------------------------------------------------------------- histdata.com
_LINE = re.compile(r"^(\d{8}) (\d{6});([0-9.]+);([0-9.]+);([0-9.]+);([0-9.]+);(\d+)$")


def histdata_month(pair: str, year: int, month: int, timeout: int = 600) -> pd.DataFrame:
    page = (f"https://www.histdata.com/download-free-forex-historical-data/"
            f"?/ascii/1-minute-bar-quotes/{pair.lower()}/{year}/{month}")
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    html = op.open(urllib.request.Request(page, headers=UA), timeout=120).read(MAX_BYTES).decode("utf-8", "ignore")
    m = re.search(r'id="tk" value="([0-9a-f]{16,64})"', html)
    if not m:
        raise FetchError("histdata: form token not found (page changed or blocked)")
    form = {"tk": m.group(1), "date": str(year), "datemonth": f"{year}{month:02d}",
            "platform": "ASCII", "timeframe": "M1", "fxpair": pair.upper()}
    req = urllib.request.Request("https://www.histdata.com/get.php",
                                 data=urllib.parse.urlencode(form).encode(), headers={**UA, "Referer": page})
    blob = op.open(req, timeout=timeout).read(MAX_BYTES)
    return parse_histdata_zip(blob)


def parse_histdata_zip(blob: bytes) -> pd.DataFrame:
    if not blob.startswith(b"PK"):
        raise FetchError(f"histdata: response is not a zip ({len(blob)} bytes)")
    rows = []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            for line in io.TextIOWrapper(z.open(name), encoding="utf-8", errors="ignore"):
                mm = _LINE.match(line.strip())
                if not mm:
                    continue
                t = dt.datetime.strptime(mm.group(1) + mm.group(2), "%Y%m%d%H%M%S") + dt.timedelta(hours=5)  # EST fixed -> UTC
                rows.append((t, mm.group(3), mm.group(4), mm.group(5), mm.group(6), mm.group(7)))
    df = _finish(rows)
    if df.empty:
        raise FetchError("histdata: zip contained no rows")
    return df


# ----------------------------------------------------------------------------- Dukascopy
_REC = struct.Struct(">5if")
_DUK_BASE = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m0:02d}/{d:02d}/BID_candles_min_1.bi5"


def dukascopy_scale(pair: str) -> float:
    return 1e3 if pair.upper().endswith("JPY") else 1e5


def _duk_day(pair: str, day: dt.date, retries: int = 6) -> bytes | None:
    url = _DUK_BASE.format(sym=pair.upper(), y=day.year, m0=day.month - 1, d=day.day)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read(MAX_BYTES)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def dukascopy_month(pair: str, year: int, month: int, workers: int = 6) -> pd.DataFrame:
    scale = dukascopy_scale(pair)
    days = [dt.date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1] + 1)]
    days = [d for d in days if d.weekday() != 5]  # Saturday closed; Sunday evening has candles
    with ThreadPoolExecutor(max_workers=workers) as ex:
        blobs = list(ex.map(lambda d: _duk_day(pair, d), days))
    rows, failed = [], []
    for day, raw in zip(days, blobs):
        if raw is None:
            failed.append(day)
            continue
        if not raw:
            continue
        data = lzma.decompress(raw)
        base = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
        for i in range(0, len(data) - _REC.size + 1, _REC.size):
            sec, o, c, l, h, v = _REC.unpack_from(data, i)
            if v == 0 and o == c == l == h:
                continue
            rows.append((base + dt.timedelta(seconds=sec), o / scale, h / scale, l / scale, c / scale, round(v, 2)))
    if failed:
        raise FetchError(f"dukascopy: {len(failed)} days failed after retries: {failed[:5]}")
    df = _finish(rows)
    if df.empty:
        raise FetchError("dukascopy: no rows")
    return df


# ----------------------------------------------------------------------------- orchestration
SOURCES = {"histdata": histdata_month, "dukascopy": dukascopy_month}


def fetch_month(pair: str, year: int, month: int, order=("histdata", "dukascopy")) -> tuple[pd.DataFrame, str]:
    """Try sources in order; return (dataframe, source_name). Raises FetchError if all fail."""
    errors = []
    for name in order:
        try:
            df = SOURCES[name](pair, year, month)
            log.info("%s %04d-%02d: %d M1 rows from %s", pair, year, month, len(df), name)
            return df, name
        except Exception as e:  # noqa: BLE001 - report every source failure
            log.warning("%s %04d-%02d: %s failed: %s", pair, year, month, name, e)
            errors.append(f"{name}: {e}")
    raise FetchError("; ".join(errors))
