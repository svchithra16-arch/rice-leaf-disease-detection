import io
import json
import unittest
from unittest.mock import patch

from backend.services import store_service


class OpenStreetMapStoreSearchTests(unittest.TestCase):
    def test_reverse_geocoder_returns_address_details_from_nominatim(self):
        payload = {
            "address": {
                "road": "Farm Road",
                "city": "Bengaluru",
                "state_district": "Bengaluru Urban",
                "state": "Karnataka",
                "postcode": "560001",
            }
        }
        response = io.BytesIO(json.dumps(payload).encode("utf-8"))
        cache_key = (12.3432, 77.4321)

        with patch.object(store_service, "urlopen", return_value=response) as urlopen:
            store_service.GEOCODE_ADDRESS_CACHE.pop(cache_key, None)
            location = store_service.get_live_location_address_details(
                12.3432, 77.4321
            )

        self.assertEqual(location["city"], "Bengaluru")
        self.assertEqual(location["address"], "Farm Road, Bengaluru")
        self.assertEqual(location["label"], "Bengaluru, Bengaluru Urban")
        urlopen.assert_called_once()

    def test_overpass_results_are_parsed_as_named_agricultural_shops(self):
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 321,
                    "lat": 12.9717,
                    "lon": 77.5947,
                    "tags": {
                        "name": "Local Seed Shop",
                        "shop": "seed",
                        "addr:street": "Market Road",
                        "addr:city": "Bengaluru",
                    },
                },
                {
                    "type": "node",
                    "id": 322,
                    "lat": 12.9718,
                    "lon": 77.5948,
                    "tags": {"shop": "agrarian"},
                },
            ]
        }
        response = io.BytesIO(json.dumps(payload).encode("utf-8"))
        cache_key = (12.9716, 77.5946, 20000)

        with patch.object(store_service, "urlopen", return_value=response) as urlopen:
            with store_service.OSM_CACHE_LOCK:
                store_service.OSM_AGRICULTURAL_STORES_CACHE.pop(cache_key, None)
            stores = store_service.get_openstreetmap_agricultural_stores(
                12.9716, 77.5946, 20000
            )

        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0]["store_name"], "Local Seed Shop")
        self.assertEqual(stores[0]["categories"], ["Seeds"])
        self.assertEqual(stores[0]["address"], "Market Road")
        self.assertEqual(stores[0]["source"], "OpenStreetMap")
        self.assertFalse(stores[0]["is_verified"])
        self.assertEqual(stores[0]["products"], [])
        urlopen.assert_called_once()

    def test_search_returns_real_listings_nearest_first_within_radius(self):
        stores = [
            {
                "id": "osm-node-far",
                "store_name": "Farmer Supply",
                "latitude": 12.99,
                "longitude": 77.59,
                "address": "Far Road",
                "city": "Town",
                "pincode": "",
                "categories": ["Agricultural Supplies"],
            },
            {
                "id": "osm-node-near",
                "store_name": "Seed Retailer",
                "latitude": 12.9717,
                "longitude": 77.5947,
                "address": "Market Road",
                "city": "Town",
                "pincode": "",
                "categories": ["Seeds"],
            },
            {
                "id": "osm-node-outside",
                "store_name": "Outside Radius",
                "latitude": 14.0,
                "longitude": 77.0,
                "address": "Far Away",
                "city": "Town",
                "pincode": "",
                "categories": ["Fertilizers"],
            },
        ]
        with patch.object(
            store_service,
            "get_live_location_address_details",
            return_value={"label": "Bengaluru, Karnataka"},
        ), patch.object(
            store_service,
            "get_openstreetmap_agricultural_stores",
            return_value=[dict(store) for store in stores],
        ):
            result = store_service.search_stores(
                user_lat=12.9716,
                user_lng=77.5946,
                is_gps=True,
                max_distance_km=20,
            )

        self.assertEqual(
            [store["id"] for store in result["stores"]],
            ["osm-node-near", "osm-node-far"],
        )
        distances = [store["distance_km"] for store in result["stores"]]
        self.assertEqual(distances, sorted(distances))
        self.assertEqual(result["source"], "OpenStreetMap")

    def test_search_requires_live_or_explicit_search_location(self):
        with self.assertRaisesRegex(ValueError, "live location or a town/PIN"):
            store_service.search_stores()


if __name__ == "__main__":
    unittest.main()
