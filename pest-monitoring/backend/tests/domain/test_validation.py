"""Unit tests for domain.validation (US-02 acceptance criteria)."""
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from domain.validation import SightingInput, parse_count_range, validate_sighting

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)

VALID = SightingInput(
    species_id=1, count_min=2, count_max=5,
    description="Several rats near the bins behind the community centre.",
    latitude=52.2713, longitude=-9.7026,
    street_or_landmark="Bins behind Riverside Community Centre",
    suburb_or_postcode="Riverside, 3021",
    observed_at=NOW - timedelta(hours=2),
    reporter_confirmed=True, is_anonymous=False,
)


def fields(errors):
    return {e.field for e in errors}


class ValidateSightingTests(unittest.TestCase):
    def test_valid_report_has_no_errors(self):
        self.assertEqual(validate_sighting(VALID, NOW), [])

    def test_species_is_required(self):
        self.assertIn("species_id", fields(validate_sighting(replace(VALID, species_id=None), NOW)))

    def test_description_is_required(self):
        self.assertIn("description", fields(validate_sighting(replace(VALID, description="   "), NOW)))

    def test_description_length_limit(self):
        errors = validate_sighting(replace(VALID, description="x" * 1001), NOW)
        self.assertIn("description", fields(errors))

    def test_location_is_required(self):
        errors = validate_sighting(replace(VALID, latitude=None), NOW)
        self.assertIn("location", fields(errors))

    def test_latitude_out_of_range(self):
        self.assertIn("latitude", fields(validate_sighting(replace(VALID, latitude=91), NOW)))

    def test_longitude_out_of_range(self):
        self.assertIn("longitude", fields(validate_sighting(replace(VALID, longitude=-181), NOW)))

    def test_count_must_be_at_least_one(self):
        self.assertIn("count", fields(validate_sighting(replace(VALID, count_min=0), NOW)))

    def test_count_max_not_below_min(self):
        self.assertIn("count", fields(validate_sighting(replace(VALID, count_min=5, count_max=2), NOW)))

    def test_future_sighting_rejected(self):
        future = replace(VALID, observed_at=NOW + timedelta(hours=1))
        self.assertIn("observed_at", fields(validate_sighting(future, NOW)))

    def test_small_clock_difference_allowed(self):
        nearly_now = replace(VALID, observed_at=NOW + timedelta(minutes=2))
        self.assertEqual(validate_sighting(nearly_now, NOW), [])

    def test_missing_time_is_allowed_server_uses_now(self):
        self.assertEqual(validate_sighting(replace(VALID, observed_at=None), NOW), [])

    def test_confirmation_required(self):
        errors = validate_sighting(replace(VALID, reporter_confirmed=False), NOW)
        self.assertIn("reporter_confirmed", fields(errors))

    def test_anonymous_needs_contact_email(self):
        errors = validate_sighting(replace(VALID, is_anonymous=True), NOW)
        self.assertIn("contact_email", fields(errors))

    def test_anonymous_rejects_bad_email(self):
        errors = validate_sighting(replace(VALID, is_anonymous=True, contact_email="not-an-email"), NOW)
        self.assertIn("contact_email", fields(errors))

    def test_anonymous_with_email_is_valid(self):
        ok = replace(VALID, is_anonymous=True, contact_email="aisha@example.com")
        self.assertEqual(validate_sighting(ok, NOW), [])

    def test_all_errors_reported_together(self):
        empty = SightingInput(None, None, None, "", None, None, "", "", None, False, False)
        self.assertGreaterEqual(len(validate_sighting(empty, NOW)), 6)


class ParseCountRangeTests(unittest.TestCase):
    def test_single_number(self):
        self.assertEqual(parse_count_range("1"), (1, 1))

    def test_range(self):
        self.assertEqual(parse_count_range("2-5"), (2, 5))

    def test_range_with_spaces(self):
        self.assertEqual(parse_count_range(" 6 - 10 "), (6, 10))

    def test_plus(self):
        self.assertEqual(parse_count_range("10+"), (10, 10))

    def test_rubbish_raises(self):
        with self.assertRaises(ValueError):
            parse_count_range("lots")


if __name__ == "__main__":
    unittest.main()
