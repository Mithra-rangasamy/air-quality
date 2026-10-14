import subprocess
import shutil
from pymongo import MongoClient

# 1. Clean Mongo test documents
client = MongoClient("mongodb://localhost:27017/")
db = client["air_quality_ews"]
res1 = db["symptom_reports"].delete_many({"description": "Automated verification test report"})
res2 = db["symptom_reports"].delete_many({"zone_name": "Local Zone"})
print(f"Cleaned MongoDB test complaints: {res1.deleted_count + res2.deleted_count} removed.")

# 2. Run MongoDB export
proc1 = subprocess.run(["/home/mithra/air-quality-ews/venv/bin/python3", "/home/mithra/air-quality-ews/mongo/export_aggregation.py"], check=True)
print("MongoDB export completed.")

# 3. Run Pig fusion
proc2 = subprocess.run(["pig", "-x", "mapreduce", "/home/mithra/air-quality-ews/pig/fusion.pig"], check=True)
print("Pig fusion completed.")

# 4. Restart dashboard
subprocess.run(["bash", "/home/mithra/air-quality-ews/scripts/stop_dashboard.sh"], check=True)
subprocess.run(["bash", "/home/mithra/air-quality-ews/scripts/start_dashboard.sh"], check=True)
print("Dashboard restarted successfully.")
