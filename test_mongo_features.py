from pymongo import MongoClient
import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["air_quality_ews"]

# Test rejected reports collection
rejected = db["rejected_reports"]
alert_hist = db["alert_history"]
pipeline_runs = db["pipeline_runs"]

print("Collections in air_quality_ews:", db.list_collection_names())
print("Total complaints in symptom_reports:", db["symptom_reports"].count_documents({}))
