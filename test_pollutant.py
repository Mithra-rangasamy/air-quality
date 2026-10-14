import subprocess
import time

t0 = time.time()
cmd = ["hdfs", "dfs", "-cat", "/data/raw/aqi/city=Coimbatore/date=2026-10-13/*"]
res = subprocess.run(cmd, capture_output=True, text=True)
lines = [l for l in res.stdout.strip().split("\n") if "CBE_ZN_01" in l]
print(f"Found {len(lines)} lines for CBE_ZN_01 in {time.time()-t0:.2f}s")
if lines:
    print("Sample:", lines[0])
