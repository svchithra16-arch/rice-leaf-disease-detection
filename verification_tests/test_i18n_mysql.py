import sys
import requests
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def test_mysql_health():
    print("Testing MySQL & App Health...")
    r = requests.get(f"{BASE_URL}/api/health")
    print(f"Health status: {r.status_code}, response: {r.text}")
    assert r.status_code == 200

def test_all_translations_endpoints():
    languages = ["en", "kn", "hi", "ta", "te", "mr", "ml", "bn"]
    print("\nTesting Translation Endpoints for all 8 languages...")
    for lang in languages:
        r = requests.get(f"{BASE_URL}/api/translations/{lang}")
        assert r.status_code == 200, f"Failed for {lang}"
        data = r.json()
        assert "nav" in data, f"Missing 'nav' in {lang}"
        assert "store" in data, f"Missing 'store' in {lang}"
        assert "camera" in data, f"Missing 'camera' in {lang}"
        assert "history" in data, f"Missing 'history' in {lang}"
        sample_title = data["store"].get("hero_title", "")
        sample_nav_dash = data["nav"].get("dashboard", "")
        print(f"  [OK] {lang:2s}: Nav Dash='{sample_nav_dash}' | Store Title='{sample_title}'")

def test_pages_accessible():
    pages = [
        "/index.html",
        "/dashboard.html",
        "/detect.html",
        "/camera.html",
        "/chat.html",
        "/stores.html",
        "/history.html",
        "/analytics.html",
        "/reports.html",
        "/profile.html",
        "/login.html",
        "/register.html"
    ]
    print("\nTesting Access to All Frontend HTML Pages...")
    for p in pages:
        r = requests.get(f"{BASE_URL}{p}")
        assert r.status_code == 200, f"Page {p} returned {r.status_code}"
        print(f"  [OK] {p} -> HTTP {r.status_code}")

def test_farms_redirection():
    print("\nTesting My Farms Removal / Redirection...")
    r = requests.get(f"{BASE_URL}/farms.html", allow_redirects=False)
    print(f"  Status: {r.status_code}, Location: {r.headers.get('Location')}")
    assert r.status_code in [302, 301]
    assert "/dashboard.html" in r.headers.get("Location", "")
    print("  [OK] /farms.html immediately redirects (HTTP 302) to /dashboard.html")

if __name__ == "__main__":
    test_mysql_health()
    test_all_translations_endpoints()
    test_pages_accessible()
    test_farms_redirection()
    print("\nAll integration & multilingual checks passed successfully!")
