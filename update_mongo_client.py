with open("/home/mithra/air-quality-ews/backend/mongo_client.py", "r") as f:
    code = f.read()

target = """        # 3. Deduplication: identical text + zone within 1 hour
        one_hour_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        duplicate = self.complaints.find_one({
            "zone_id": zid,
            "description": desc,
            "reported_at": {"$gte": one_hour_ago}
        })
        if duplicate:
            return False, "DUPLICATE_REPORT_WITHIN_1HR: Identical symptom report already received for this zone within the last hour." """

replacement = """        # 3. Deduplication: identical text + zone within 1 hour
        one_hour_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        dedup_filter = {
            "zone_id": zid,
            "description": desc,
            "reported_at": {"$gte": one_hour_ago}
        }
        if reporter and reporter != "Anonymous":
            dedup_filter["citizen_name"] = reporter

        duplicate = self.complaints.find_one(dedup_filter)
        if duplicate:
            return False, "DUPLICATE_REPORT_WITHIN_1HR: Identical symptom report already received for this zone within the last hour." """

if target.strip() in code:
    code = code.replace(target.strip(), replacement.strip())
    with open("/home/mithra/air-quality-ews/backend/mongo_client.py", "w") as f:
        f.write(code)
    print("SUCCESS: mongo_client.py updated")
else:
    print("TARGET NOT FOUND")
