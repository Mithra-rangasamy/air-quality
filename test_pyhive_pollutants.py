import time
from pyhive import hive

t0 = time.time()
conn = hive.Connection(host="localhost", port=10000, username="mithra", database="default")
cursor = conn.cursor()
cursor.execute("SELECT ts, aqi, pm25, pm10, no2, so2, co, o3 FROM aqi_readings WHERE zone_id = 'CBE_ZN_01' AND `date` = '2026-10-13' ORDER BY ts")
rows = cursor.fetchall()
conn.close()
print(f"PyHive returned {len(rows)} rows in {time.time()-t0:.2f}s")
if rows:
    print("Sample row:", rows[0])
