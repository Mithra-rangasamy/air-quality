import os
import subprocess
import time

if "JAVA_HOME" not in os.environ:
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
if "/opt/hadoop/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"/opt/hadoop/bin:/opt/hadoop/sbin:/opt/hive/bin:{os.environ.get('PATH', '')}"

STANDARDS = {
    "pm25": {"name": "PM2.5", "std": 60.0, "unit": "µg/m³"},
    "pm10": {"name": "PM10", "std": 100.0, "unit": "µg/m³"},
    "no2":  {"name": "NO2", "std": 80.0, "unit": "µg/m³"},
    "so2":  {"name": "SO2", "std": 80.0, "unit": "µg/m³"},
    "co":   {"name": "CO", "std": 2.0, "unit": "mg/m³"},
    "o3":   {"name": "O3", "std": 100.0, "unit": "µg/m³"}
}

cmd = ["hdfs", "dfs", "-cat", "/data/processed/daily_pollutant_agg/*"]
res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
records = {}
for line in res.stdout.strip().split("\n"):
    if not line.strip(): continue
    parts = line.strip().split("\t")
    if len(parts) >= 11:
        zid = parts[0]
        dt = parts[3]
        rec = {
            "zone_id": parts[0],
            "zone_name": parts[1],
            "city": parts[2],
            "date": parts[3],
            "avg_aqi": float(parts[4]),
            "pm25": float(parts[5]),
            "pm10": float(parts[6]),
            "no2": float(parts[7]),
            "so2": float(parts[8]),
            "co": float(parts[9]),
            "o3": float(parts[10])
        }
        # Compute ratios
        ratios = {p: rec[p] / STANDARDS[p]["std"] for p in STANDARDS}
        dom_p = max(ratios.keys(), key=lambda k: ratios[k])
        rec["dominant_pollutant"] = dom_p
        rec["dominant_ratio"] = round(ratios[dom_p], 2)
        rec["dominant_name"] = STANDARDS[dom_p]["name"]
        rec["ratios"] = {k: round(v, 2) for k, v in ratios.items()}
        records[(zid, dt)] = rec

print(f"Loaded {len(records)} daily pollutant records.")
sample_key = ("CBE_ZN_01", "2026-10-13")
if sample_key in records:
    print("CBE_ZN_01 dominant pollutant on 2026-10-13:", records[sample_key])
