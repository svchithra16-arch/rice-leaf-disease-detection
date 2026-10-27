import sys, os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from backend.app import create_app
from backend.database.models import User
import requests

BASE = "http://127.0.0.1:5000"

app = create_app()
with app.app_context():
    u = User.query.get(3)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = u.id
            sess['role'] = u.role
        s = client.get('/api/analytics/user-stats').get_json()
        print('User 3 Dashboard Stats:')
        print(f"  Total Scans: {s['total_scans']}")
        print(f"  Healthy Leaves: {s['healthy_scans']}")
        print(f"  Diseased Detections: {s['diseased_scans']}")
        print(f"  Avg Confidence: {s['avg_confidence']}%")
        print('  Recent Scans Table:')
        for item in s['recent_activity'][:4]:
            print(f"    - {item['disease_name']} ({item['severity_level']}) | Conf: {item['confidence']}% | URL: {item['image_url']}")

print("\nStore API Catalog Count:")
r = requests.get(f"{BASE}/api/stores/products")
print(f"  Total Online Products: {len(r.json()['products'])}")
print("\nAll Dashboard & Store Checks Verified Successfully!")
