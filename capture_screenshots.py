import subprocess
import os
import time

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"C:\Users\mithra\.gemini\antigravity\scratch\screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

targets = [
    # Mobile viewports (360px)
    ("dashboard_mobile_360px.png", "http://127.0.0.1:5000/?zone=CBE_ZN_01", 360, 800),
    ("admin_mobile_360px.png", "http://127.0.0.1:5000/admin", 360, 800),
    
    # Tablet viewports (768px)
    ("dashboard_tablet_768px.png", "http://127.0.0.1:5000/?zone=CBE_ZN_01", 768, 1024),
    ("admin_tablet_768px.png", "http://127.0.0.1:5000/admin", 768, 1024),
    
    # Desktop viewports (1280px)
    ("dashboard_desktop_1280px.png", "http://127.0.0.1:5000/?zone=CBE_ZN_01", 1280, 900),
    ("admin_desktop_1280px.png", "http://127.0.0.1:5000/admin", 1280, 900),
    ("situation_report_desktop_1280px.png", "http://127.0.0.1:5000/admin/report", 1280, 1100),
    ("tamilnadu_surveillance_1280px.png", "http://127.0.0.1:5000/#tn-section", 1280, 900)
]

for filename, url, width, height in targets:
    out_path = os.path.join(OUT_DIR, filename)
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out_path}",
        "--virtual-time-budget=4000",
        url
    ]
    print(f"Capturing {filename} at {width}x{height}...")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if os.path.exists(out_path):
        size_kb = os.path.getsize(out_path) / 1024.0
        print(f"  [OK] Saved {filename} ({size_kb:.1f} KB)")
    else:
        print(f"  [FAIL] Failed to save {filename}: {proc.stderr}")

print("\nAll responsive screenshots captured successfully.")
