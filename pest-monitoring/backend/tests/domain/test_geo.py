"""Unit tests for domain.geo (US-04 / US-05 map data)."""
import unittest

from domain.geo import heat_weight, parse_bbox, to_feature_collection


class BoundingBoxTests(unittest.TestCase):
    def test_parse_valid(self):
        box = parse_bbox("-9.8,52.2,-9.6,52.4")
        self.assertTrue(box.contains(-9.70, 52.27))
        self.assertFalse(box.contains(-8.47, 51.89))

    def test_wrong_number_of_values(self):
        with self.assertRaises(ValueError):
            parse_bbox("1,2,3")

    def test_reversed_box_rejected(self):
        with self.assertRaises(ValueError):
            parse_bbox("10,10,5,5")

    def test_not_numbers_rejected(self):
        with self.assertRaises(ValueError):
            parse_bbox("a,b,c,d")


class GeoJsonTests(unittest.TestCase):
    def test_heat_weights(self):
        self.assertEqual([heat_weight("High"), heat_weight("Medium"), heat_weight("Low"), heat_weight(None)],
                         [3, 2, 1, 1])

    def test_feature_collection(self):
        fc = to_feature_collection([{"id": 7, "latitude": 52.27, "longitude": -9.70, "priority": "High"}])
        feature = fc["features"][0]
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(feature["geometry"]["coordinates"], [-9.70, 52.27])  # GeoJSON is lon, lat
        self.assertEqual(feature["properties"], {"id": 7, "priority": "High", "heat_weight": 3})


if __name__ == "__main__":
    unittest.main()
