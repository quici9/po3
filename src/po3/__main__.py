"""CLI.

  python -m po3 update  --month YYYY-MM [--pairs A,B] [--force]   fetch M1, rebuild facts for that month
  python -m po3 monthly --month YYYY-MM [--notify]                 monthly report (+ Telegram)
  python -m po3 annual  --year YYYY [--notify]                     annual report (+ Telegram)
  python -m po3 probe   --month YYYY-MM [--notify]                 test both data sources, no data written
  python -m po3 bootstrap --m1-dir DIR                             build facts from local <PAIR>_M1_UTC.csv files
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

import pandas as pd

from . import config, features, fetch, notify, report

log = logging.getLogger("po3")


def _pairs(arg: str | None) -> list[str]:
    return [p.strip().upper() for p in arg.split(",")] if arg else config.load()["pairs"]


def _ym(s: str) -> tuple[int, int]:
    y, m = s.split("-")
    return int(y), int(m)


def cmd_update(a) -> int:
    y, m = _ym(a.month)
    sources, failures = {}, []
    for pair in _pairs(a.pairs):
        existing = features.load_facts(pair)
        have = ((existing["ts_utc"].dt.year == y) & (existing["ts_utc"].dt.month == m)).sum() if not existing.empty else 0
        if have and not a.force:
            log.info("%s %s already has %d H1 rows; skip (use --force to refetch)", pair, a.month, have)
            continue
        try:
            m1, src = fetch.fetch_month(pair, y, m)
        except fetch.FetchError as e:
            failures.append(f"{pair}: {e}")
            continue
        facts = features.facts_from_m1(m1, src)
        features.upsert_month(pair, facts, y, m)
        sources[pair] = src
        log.info("%s %s: %d H1 rows written", pair, a.month, len(facts))
    with open(os.path.join(config.ROOT, "data", "last_update.json"), "w") as f:
        json.dump({"month": a.month, "sources": sources, "failures": failures}, f, indent=1)
    if failures:
        log.error("update failures: %s", failures)
        if a.notify:
            notify.send_message(f"<b>PO3 {notify.esc(a.month)}: tải dữ liệu thất bại</b>\n" + "\n".join(notify.esc(x) for x in failures))
        return 1
    return 0


def cmd_monthly(a) -> int:
    y, m = _ym(a.month)
    src = {}
    lu = os.path.join(config.ROOT, "data", "last_update.json")
    if os.path.exists(lu):
        with open(lu) as f:
            j = json.load(f)
        if j.get("month") == a.month:
            src = j.get("sources", {})
    md, tg = report.monthly(y, m, _pairs(a.pairs), src)
    path = report.write_report("monthly", a.month, md)
    print(path)
    if a.notify:
        notify.send_message(tg)
        notify.send_document(path, caption=f"PO3 báo cáo tháng {a.month}")
    return 0


def cmd_annual(a) -> int:
    md, tg = report.annual(a.year, _pairs(a.pairs))
    path = report.write_report("annual", str(a.year), md)
    print(path)
    if a.notify:
        notify.send_message(tg)
        notify.send_document(path, caption=f"PO3 báo cáo năm {a.year}")
    return 0


def cmd_probe(a) -> int:
    y, m = _ym(a.month)
    lines = [f"<b>PO3 probe {notify.esc(a.month)}</b>"]
    ok_any = False
    for pair in _pairs(a.pairs)[:1]:
        for name, fn in fetch.SOURCES.items():
            t0 = time.time()
            try:
                df = fn(pair, y, m)
                ok_any = True
                lines.append(f"{name} {pair}: OK {len(df)} M1 rows, {df['ts_utc'].min():%m-%d} → {df['ts_utc'].max():%m-%d}, {time.time()-t0:.0f}s")
            except Exception as e:  # noqa: BLE001
                lines.append(f"{name} {pair}: FAIL {notify.esc(str(e)[:200])} ({time.time()-t0:.0f}s)")
    print("\n".join(lines))
    if a.notify:
        notify.send_message("\n".join(lines))
    return 0 if ok_any else 1


def cmd_bootstrap(a) -> int:
    for pair in _pairs(a.pairs):
        p = os.path.join(a.m1_dir, f"{pair}_M1_UTC.csv")
        if not os.path.exists(p):
            log.warning("missing %s", p)
            continue
        m1 = pd.read_csv(p)
        m1["ts_utc"] = pd.to_datetime(m1["ts_utc"], utc=True)
        if a.until:
            m1 = m1[m1["ts_utc"] < pd.Timestamp(a.until, tz="UTC")]
        facts = features.facts_from_m1(m1, a.source)
        features.save_facts(pair, facts)
        log.info("%s: %d H1 rows (%s → %s)", pair, len(facts), facts["ts_utc"].min(), facts["ts_utc"].max())
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="po3")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("update"); s.add_argument("--month", required=True); s.add_argument("--pairs"); s.add_argument("--force", action="store_true"); s.add_argument("--notify", action="store_true"); s.set_defaults(fn=cmd_update)
    s = sub.add_parser("monthly"); s.add_argument("--month", required=True); s.add_argument("--pairs"); s.add_argument("--notify", action="store_true"); s.set_defaults(fn=cmd_monthly)
    s = sub.add_parser("annual"); s.add_argument("--year", type=int, required=True); s.add_argument("--pairs"); s.add_argument("--notify", action="store_true"); s.set_defaults(fn=cmd_annual)
    s = sub.add_parser("probe"); s.add_argument("--month", required=True); s.add_argument("--pairs"); s.add_argument("--notify", action="store_true"); s.set_defaults(fn=cmd_probe)
    s = sub.add_parser("bootstrap"); s.add_argument("--m1-dir", required=True); s.add_argument("--pairs"); s.add_argument("--source", default="histdata"); s.add_argument("--until"); s.set_defaults(fn=cmd_bootstrap)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
