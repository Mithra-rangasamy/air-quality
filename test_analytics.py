import os
import subprocess
import numpy as np

if "JAVA_HOME" not in os.environ:
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
if "/opt/hadoop/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"/opt/hadoop/bin:/opt/hadoop/sbin:/opt/hive/bin:{os.environ.get('PATH', '')}"

# 1. Test Anomaly Detection
cmd = ["hdfs", "dfs", "-cat", "/data/processed/zone_risk_score/*"]
res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
zone_daily = {}
for line in res.stdout.strip().split("\n"):
    if not line.strip(): continue
    parts = line.strip().split("\t")
    if len(parts) >= 14:
        zid = parts[0]
        zname = parts[1]
        city = parts[2]
        dt = parts[3]
        aqi = float(parts[4])
        comp = int(parts[7])
        if zid not in zone_daily:
            zone_daily[zid] = {"zone_name": zname, "city": city, "dates": [], "aqi": [], "complaints": []}
        zone_daily[zid]["dates"].append(dt)
        zone_daily[zid]["aqi"].append(aqi)
        zone_daily[zid]["complaints"].append(comp)

print(f"Loaded {len(zone_daily)} zones for analysis.")

# Compute Anomalies (Z-score > 2.5)
anomalies = []
for zid, data in zone_daily.items():
    aqis = np.array(data["aqi"])
    mean_aqi = np.mean(aqis)
    std_aqi = np.std(aqis)
    if std_aqi > 0:
        z_scores = (aqis - mean_aqi) / std_aqi
        for i, z in enumerate(z_scores):
            if abs(z) >= 2.0:  # Spikes
                anomalies.append({
                    "zone_id": zid,
                    "zone_name": data["zone_name"],
                    "city": data["city"],
                    "date": data["dates"][i],
                    "aqi": round(float(aqis[i]), 1),
                    "mean_aqi": round(float(mean_aqi), 1),
                    "std_aqi": round(float(std_aqi), 1),
                    "z_score": round(float(z), 2),
                    "spike": True,
                    "type": "INDUSTRIAL_PLUME" if z > 0 else "SENSOR_DROP"
                })

print(f"Detected {len(anomalies)} statistical anomaly spikes.")
for a in anomalies[:5]:
    print(" ", a)

# Compute Lag Pearson Correlation (Lags 0, 1, 2, 3)
all_aqi = []
all_comp = []
for zid, data in zone_daily.items():
    all_aqi.extend(data["aqi"])
    all_comp.extend(data["complaints"])

correlations = {}
for lag in [0, 1, 2, 3]:
    lag_aqi = []
    lag_comp = []
    for zid, data in zone_daily.items():
        aqis = data["aqi"]
        comps = data["complaints"]
        if lag == 0:
            lag_aqi.extend(aqis)
            lag_comp.extend(comps)
        else:
            lag_aqi.extend(aqis[:-lag])
            lag_comp.extend(comps[lag:])
    if len(lag_aqi) > 2:
        r = np.corrcoef(lag_aqi, lag_comp)[0, 1]
        correlations[f"lag_{lag}"] = round(float(r), 4)

print("Overall Lag Correlations (AQI vs Complaints):", correlations)
