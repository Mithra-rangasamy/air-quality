with open('/home/mithra/air-quality-ews/mongo/export_aggregation.py', 'r') as f:
    code = f.read()

old_group = '''            "$group": {
                "_id": {
                    "city": "$city",
                    "zone_id": "$zone_id",
                    "zone_name": "$zone_name",
                    "date": "$date_str"
                },'''

new_group = '''            "$group": {
                "_id": {
                    "zone_id": "$zone_id",
                    "date": "$date_str"
                },
                "city": {"$first": "$city"},
                "zone_name": {"$first": "$zone_name"},'''

code = code.replace(old_group, new_group)

old_loop = '''    for doc in cursor:
        info = doc["_id"]
        zone_id = info["zone_id"]
        zone_name = info["zone_name"]
        city = info["city"]
        date = info.get("date") or "2026-10-13"'''

new_loop = '''    for doc in cursor:
        info = doc["_id"]
        zone_id = info["zone_id"]
        date = info.get("date") or "2026-10-13"
        zone_name = doc.get("zone_name") or "Zone"
        city = doc.get("city") or "City"'''

code = code.replace(old_loop, new_loop)

with open('/home/mithra/air-quality-ews/mongo/export_aggregation.py', 'w') as f:
    f.write(code)

print("Export aggregation script updated for unique zone_id+date grouping.")
