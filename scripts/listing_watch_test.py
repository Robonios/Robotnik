#!/usr/bin/env python3
"""
Unit tests for the E11 listing watch in scripts/check_entity_lifecycle.py.
==========================================================================
Synthetic fixtures only (no network). Covers the four cases the watch must tell apart:

  1. Private name matching an SEC registrant: flagged at once (Agility, AGLT).
  2. Pre-IPO filer whose proposed ticker is in the SEC list but whose offering has not
     reached the market: not flagged (Nscale, NSCL, on an unpriced S-1/A).
  3. The same filer once a listing or withdrawal form is filed since its filing date:
     flagged, naming the form and date.
  4. A filer whose EDGAR filings cannot be read: flagged, so a failed read never hides
     a listing. The age signal still flags a stale filing.

Run:  python3 scripts/listing_watch_test.py      (verbose: add -v)
Stdlib unittest only, matching the repo's no-build-tools constraint.
"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_entity_lifecycle as lc  # noqa: E402

TODAY = date(2026, 11, 23)
TITLES = {"nscale": ["NSCL"], "agility robotics": ["AGLT"]}
CIKS = {"NSCL": "0002110365", "AGLT": "0000000001"}
NSCALE_FILINGS = [("S-1/A", "2026-11-12"), ("S-1", "2026-09-18"), ("DRS", "2026-02-17")]


def registry(**nscale):
    rec = {"name": "Nscale", "type": "private", "aliases": ["Nscale"],
           "lifecycle_status": "pre_ipo_filed", "valuation_as_of": "2026-11-12"}
    rec.update(nscale)
    return {"nscale": rec,
            "agility-robotics": {"name": "Agility Robotics", "type": "private",
                                 "lifecycle_status": "private"}}


def filings_from(rows):
    def read(cik):
        return rows if cik == CIKS["NSCL"] else []
    return read


def failing(cik):
    raise OSError("EDGAR unreachable")


def run(reg, filings, titles=TITLES):
    return {f["entity"]: f for f in lc.check_listings(reg, titles, today=TODAY,
                                                      ciks=CIKS, filings=filings)}


class ListingWatchTest(unittest.TestCase):
    def test_private_match_is_flagged(self):
        found = run(registry(), filings_from(NSCALE_FILINGS))
        self.assertEqual(found["agility-robotics"]["signal"], "sec")
        self.assertEqual(found["agility-robotics"]["tickers"], ["AGLT"])

    def test_unpriced_filer_is_not_flagged(self):
        found = run(registry(), filings_from(NSCALE_FILINGS))
        self.assertNotIn("nscale", found)

    def test_listing_form_flags_the_filer(self):
        rows = [("424B4", "2026-12-04"), ("EFFECT", "2026-12-02"), ("8-A12B", "2026-12-01")]
        found = run(registry(), filings_from(rows + NSCALE_FILINGS))
        f = found["nscale"]
        self.assertEqual(f["signal"], "sec-filing")
        self.assertIn("SEC registrant NSCL filed 8-A12B on 2026-12-01", f["detail"])
        self.assertIn("424B4 on 2026-12-04", f["detail"])

    def test_withdrawal_flags_the_filer(self):
        found = run(registry(), filings_from([("RW", "2026-12-10")] + NSCALE_FILINGS))
        self.assertIn("filed RW on 2026-12-10", found["nscale"]["detail"])

    def test_forms_before_the_filing_date_are_ignored(self):
        found = run(registry(), filings_from([("EFFECT", "2026-11-01")] + NSCALE_FILINGS))
        self.assertNotIn("nscale", found)

    def test_unreadable_filings_flag_the_filer(self):
        found = run(registry(), failing)
        self.assertIn("could not be read", found["nscale"]["detail"])

    def test_age_signal_still_flags_a_stale_filing(self):
        found = run(registry(valuation_as_of="2026-09-18"), filings_from(NSCALE_FILINGS))
        self.assertEqual(found["nscale"]["signal"], "age")

    def test_without_the_sec_list_only_age_runs(self):
        found = run(registry(), failing, titles=None)
        self.assertEqual(set(found), set())

    def test_excluded_names_are_skipped(self):
        reg = registry()
        reg["agility-robotics"]["status"] = "excluded"
        self.assertNotIn("agility-robotics", run(reg, filings_from(NSCALE_FILINGS)))


if __name__ == "__main__":
    unittest.main()
