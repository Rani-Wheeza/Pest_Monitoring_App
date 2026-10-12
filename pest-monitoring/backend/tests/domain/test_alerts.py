"""Unit tests for domain.alerts (US-06 acceptance criteria)."""
import unittest
from datetime import date

from domain.alerts import ActivitySummary, AlertType, Severity, evaluate_activity, in_peak_season


def summary(**overrides):
    base = dict(district_id=1, species_id=1, sighting_count=0, last_seen=date(2026, 10, 1),
                is_invasive=False, peak_season_start=None, peak_season_end=None)
    base.update(overrides)
    return ActivitySummary(**base)


def types(decisions):
    return {d.alert_type for d in decisions}


class PeakSeasonTests(unittest.TestCase):
    def test_no_season_means_always_in_season(self):
        self.assertTrue(in_peak_season(7, None, None))

    def test_simple_season(self):
        self.assertTrue(in_peak_season(6, 4, 8))
        self.assertFalse(in_peak_season(10, 4, 8))

    def test_season_wrapping_new_year(self):
        # Rats: September to March
        self.assertTrue(in_peak_season(12, 9, 3))
        self.assertTrue(in_peak_season(2, 9, 3))
        self.assertFalse(in_peak_season(6, 9, 3))

    def test_season_edges_included(self):
        self.assertTrue(in_peak_season(9, 9, 3))
        self.assertTrue(in_peak_season(3, 9, 3))


class EvaluateActivityTests(unittest.TestCase):
    def test_below_threshold_no_alert(self):
        self.assertEqual(evaluate_activity(summary(sighting_count=9), threshold=10), [])

    def test_at_threshold_is_medium(self):
        decisions = evaluate_activity(summary(sighting_count=10), threshold=10)
        self.assertEqual([(d.alert_type, d.severity) for d in decisions],
                         [(AlertType.HIGH_ACTIVITY, Severity.MEDIUM)])

    def test_double_threshold_is_high(self):
        decisions = evaluate_activity(summary(sighting_count=20), threshold=10)
        self.assertEqual(decisions[0].severity, Severity.HIGH)

    def test_unseasonal_sighting(self):
        s = summary(sighting_count=1, last_seen=date(2026, 6, 15), peak_season_start=9, peak_season_end=3)
        self.assertEqual(types(evaluate_activity(s, threshold=10)), {AlertType.UNSEASONAL})

    def test_in_season_sighting_no_unseasonal_alert(self):
        s = summary(sighting_count=1, last_seen=date(2026, 11, 2), peak_season_start=9, peak_season_end=3)
        self.assertEqual(evaluate_activity(s, threshold=10), [])

    def test_invasive_species_always_alerts(self):
        decisions = evaluate_activity(summary(sighting_count=1, is_invasive=True), threshold=10)
        self.assertEqual(types(decisions), {AlertType.INVASIVE_SPECIES})
        self.assertEqual(decisions[0].severity, Severity.HIGH)

    def test_several_conditions_at_once(self):
        s = summary(sighting_count=25, is_invasive=True, last_seen=date(2026, 6, 1),
                    peak_season_start=9, peak_season_end=3)
        self.assertEqual(types(evaluate_activity(s, threshold=10)),
                         {AlertType.HIGH_ACTIVITY, AlertType.UNSEASONAL, AlertType.INVASIVE_SPECIES})

    def test_no_sightings_no_alerts_even_if_invasive(self):
        self.assertEqual(evaluate_activity(summary(sighting_count=0, is_invasive=True), threshold=10), [])

    def test_threshold_must_be_positive(self):
        with self.assertRaises(ValueError):
            evaluate_activity(summary(), threshold=0)


if __name__ == "__main__":
    unittest.main()
