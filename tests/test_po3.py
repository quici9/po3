"""Regression tests on a fixed month (EURUSD 2026-08, histdata zip). If a definition changes, these
numbers change: that is the point. Update them only together with a version bump in config/definitions.toml.
"""
import os

import pytest

from po3 import config, features, fetch, stats

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "EURUSD_202608.zip")


@pytest.fixture(scope="module")
def derived():
    m1 = fetch.parse_histdata_zip(open(FIX, "rb").read())
    facts = features.facts_from_m1(m1, "fixture")
    return m1, facts, features.derive(facts)


def test_config_version_present():
    cfg = config.load()
    assert cfg["version"] == "1.0"
    assert cfg["candle"]["directional_body_ratio"] == 0.5


def test_parse_histdata(derived):
    m1, _, _ = derived
    assert len(m1) == 30496
    assert str(m1["ts_utc"].min()) == "2026-08-02 22:00:00+00:00"  # Sunday 17:00 EST -> 22:00 UTC
    assert (m1["high"] >= m1["low"]).all()


def test_facts_and_coverage(derived):
    _, facts, _ = derived
    assert len(facts) == 511
    assert set(features.FACT_COLS) == set(facts.columns)
    assert facts["min_low"].between(0, 59).all() and facts["min_high"].between(0, 59).all()
    cov = stats.coverage(facts, 2026, 8)
    assert cov["expected"] == 504 and cov["present"] == 496 and cov["flag"] is False


def test_minute_distribution_reference(derived):
    _, _, d = derived
    s = stats.minute_summary(stats.manip_set(d)["min_manip"])
    assert s["n"] == 156
    assert s["00-10"] == pytest.approx(0.6859, abs=1e-4)
    assert s["11-25"] == pytest.approx(0.1923, abs=1e-4)
    assert s["le25"] == pytest.approx(0.8782, abs=1e-4)
    assert s["median"] == 5.0
    assert s["min0"] == pytest.approx(0.2115, abs=1e-4)


def test_profiles_reference(derived):
    _, _, d = derived
    counts = d["profile"].value_counts().to_dict()
    assert counts == {"Other": 227, "ConsolRev": 173, "Seek&Destroy": 38, "TrendRunaway": 34, "ClassicExp": 27, "News/Outlier": 12}


def test_sequence_and_sessions(derived):
    _, _, d = derived
    assert d["seq_ok"][d["directional"]].mean() > 0.9
    assert set(d["session"].unique()) <= {"Asia", "London", "NY_AM", "NY_PM", "other"}
    assert d.loc[d["hour_ny"] == 3, "session"].eq("London").all()


def test_wilson_and_z():
    p, lo, hi = stats.wilson(50, 100)
    assert p == 0.5 and lo < 0.5 < hi
    assert stats.zscore(0.5, 0.5, 100) == 0.0
    assert abs(stats.zscore(0.6, 0.5, 100)) == pytest.approx(2.0, abs=1e-9)


def test_random_walk_baseline_shape():
    rw = stats.random_walk_minutes(n_sim=20_000)
    k = next(iter(rw))
    assert 0.5 < rw[k]["00-10"] < 0.65   # arcsine-law front loading, well below the real ~0.69
