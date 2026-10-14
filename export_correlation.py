import os
import subprocess
import numpy as np

if "JAVA_HOME" not in os.environ:
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
if "/opt/hadoop/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"/opt/hadoop/bin:/opt/hadoop/sbin:/opt/hive/bin:{os.environ.get('PATH', '')}"

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

rows = []
# Overall correlation first
all_aqi = []
all_comp = []
for zid, data in zone_daily.items():
    all_aqi.extend(data["aqi"])
    all_comp.extend(data["complaints"])

lags_overall = []
for lag in [0, 1, 2, 3]:
    la, lc = [], []
    for zid, data in zone_daily.items():
        if lag == 0:
            la.extend(data["aqi"])
            lc.extend(data["complaints"])
        else:
            la.extend(data["aqi"][:-lag])
            lc.extend(data["complaints"][lag:])
    r = np.corrcoef(la, lc)[0, 1] if len(la) > 2 else 0.0
    lags_overall.append(round(float(r), 4))

opt_lag = int(np.argmax(lags_overall))
max_r = max(lags_overall)
rows.append(f"ALL\tAll System Zones\tNational Aggregate\t{lags_overall[0]}\t{lags_overall[1]}\t{lags_overall[2]}\t{lags_overall[3]}\t{opt_lag}\t{max_r}")

for zid, data in sorted(zone_daily.items()):
    aqis = data["aqi"]
    comps = data["complaints"]
    zone_lags = []
    for lag in [0, 1, 2, 3]:
        if lag == 0:
            la, lc = aqis, comps
        else:
            la, lc = aqis[:-lag], comps[lag:]
        if len(la) > 2 and np.std(la) > 0 and np.std(lc) > 0:
            r = np.corrcoef(la, lc)[0, 1]
            if np.isnan(r): r = 0.0
        else:
            r = 0.0
        zone_lags.append(round(float(r), 4))
    opt_lag = int(np.argmax(zone_lags))
    max_r = max(zone_lags)
    rows.append(f"{zid}\t{data['zone_name']}\t{data['city']}\t{zone_lags[0]}\t{zone_lags[1]}\t{zone_lags[2]}\t{zone_lags[3]}\t{opt_lag}\t{max_r}")

out_tsv = "\n".join(rows) + "\n"

# Write to temp file then put into HDFS
tmp_path = "/tmp/aqi_complaint_correlation.tsv"
with open(tmp_path, "w") as f:
    f.write(out_tsv)

subprocess.run(["hdfs", "dfs", "-mkdir", "-p", "/data/processed/aqi_complaint_correlation"], check=True)
subprocess.run(["hdfs", "dfs", "-rm", "-r", "-f", "/data/processed/aqi_complaint_correlation/*"], check=False)
subprocess.run(["hdfs", "dfs", "-put", tmp_path, "/data/processed/aqi_complaint_correlation/"], check=True)
print(f"Exported {len(rows)} correlation rows to HDFS /data/processed/aqi_complaint_correlation")
