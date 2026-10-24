import cv2
import numpy as np
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.predict import predict_rice_disease

os.makedirs('verification_tests', exist_ok=True)

# TEST 1: Completely healthy green rice leaf
t1_img = np.ones((300, 300, 3), dtype=np.uint8) * 240
cv2.ellipse(t1_img, (150, 150), (60, 130), 0, 0, 360, (34, 139, 34), -1)
t1_path = 'verification_tests/test1_healthy.jpg'
cv2.imwrite(t1_path, t1_img)

# TEST 2: Rice leaf with multiple circular brown lesions
t2_img = t1_img.copy()
np.random.seed(42)
for _ in range(16):
    x = int(np.random.uniform(110, 190))
    y = int(np.random.uniform(50, 250))
    cv2.circle(t2_img, (x, y), 5, (20, 50, 100), -1)
    cv2.circle(t2_img, (x, y), 2, (40, 80, 140), -1)
t2_path = 'verification_tests/test2_brown_spot.jpg'
cv2.imwrite(t2_path, t2_img)

# TEST 3: Rice leaf with characteristic spindle/diamond blast lesions
t3_img = t1_img.copy()
for _ in range(5):
    x = int(np.random.uniform(120, 180))
    y = int(np.random.uniform(70, 230))
    pts = np.array([[x, y-15], [x+7, y], [x, y+15], [x-7, y]])
    cv2.fillPoly(t3_img, [pts], (20, 45, 100))
    inner_pts = np.array([[x, y-10], [x+4, y], [x, y+10], [x-4, y]])
    cv2.fillPoly(t3_img, [inner_pts], (180, 180, 180))
t3_path = 'verification_tests/test3_rice_blast.jpg'
cv2.imwrite(t3_path, t3_img)

# TEST 4: Rice leaf with bacterial blight symptoms (marginal wavy wilt)
t4_img = t1_img.copy()
pts_margin = np.array([[190, 50], [210, 150], [195, 250], [175, 250], [180, 150], [170, 50]])
cv2.fillPoly(t4_img, [pts_margin], (80, 180, 220))
t4_path = 'verification_tests/test4_bacterial_blight.jpg'
cv2.imwrite(t4_path, t4_img)

# TEST 5: Completely unrelated image (car on road with blue sky)
t5_img = np.zeros((300, 300, 3), dtype=np.uint8)
t5_img[:150, :] = [235, 206, 135] # Blue sky
t5_img[150:, :] = [80, 80, 80]    # Road
cv2.rectangle(t5_img, (100, 120), (200, 180), (0, 0, 200), -1) # Red box
t5_path = 'verification_tests/test5_unrelated_car.jpg'
cv2.imwrite(t5_path, t5_img)

# TEST 6A: Pitch dark image
t6_img = np.zeros((300, 300, 3), dtype=np.uint8)
t6_path = 'verification_tests/test6_dark_image.jpg'
cv2.imwrite(t6_path, t6_img)

# TEST 6B: Heavily blurred image
t6b_img = cv2.GaussianBlur(t1_img, (51, 51), 30.0)
t6b_path = 'verification_tests/test6b_blurry.jpg'
cv2.imwrite(t6b_path, t6b_img)

print('=' * 85)
print('AGRIVERSION 6-POINT MANDATORY VALIDATION TEST SUITE')
print('=' * 85)

tests = [
    ('TEST 1 (Healthy Green Leaf)', t1_path, 'Healthy Rice Leaf'),
    ('TEST 2 (Circular Brown Lesions)', t2_path, 'Brown Spot'),
    ('TEST 3 (Spindle Blast Lesions)', t3_path, 'Rice Blast'),
    ('TEST 4 (Marginal Bacterial Blight)', t4_path, 'Bacterial Leaf Blight'),
    ('TEST 5 (Unrelated Non-Rice Image)', t5_path, 'Invalid Image (Rejected)'),
    ('TEST 6A (Pitch Dark Image)', t6_path, 'Image Quality Insufficient (Rejected)'),
    ('TEST 6B (Heavily Blurry Image)', t6b_path, 'Image Quality Insufficient (Rejected)')
]

all_passed = True
for name, path, expected in tests:
    res = predict_rice_disease(path)
    if res.get('success'):
        d = res.get('primary_disease')
        c = res.get('confidence')
        cl = res.get('confidence_level')
        sev = res.get('severity', {}).get('severity_level')
        h_pct = res.get('severity', {}).get('healthy_area_pct')
        l_pct = res.get('severity', {}).get('affected_area_pct')
        l_cnt = res.get('severity', {}).get('lesion_count')
        symptom_snippet = (res.get('symptoms', '')[:90] + '...') if res.get('symptoms') else ''
        status = "PASS" if expected in d else "FAIL"
        if status == "FAIL": all_passed = False
        print(f"[{status}] {name:34} Expected: {expected:25} => Result: {d} ({c:.2f}%, Level: {cl})")
        print(f"      -> Severity: {sev} | Healthy: {h_pct}% | Lesion Area: {l_pct}% | Spots: {l_cnt}")
        print(f"      -> Dynamic Symptoms: \"{symptom_snippet}\"")
    else:
        err = res.get('error_type')
        msg = res.get('message')
        status = "PASS" if "Rejected" in expected else "FAIL"
        if status == "FAIL": all_passed = False
        print(f"[{status}] {name:34} Expected: {expected:25} => Rejected: [{err}] \"{msg}\"")

print('=' * 85)
print(f"FINAL SUITE STATUS: {'ALL 6 TEST CASES PASSED PERFECTLY!' if all_passed else 'SOME TESTS FAILED'}")
print('=' * 85)
