with open('/home/mithra/air-quality-ews/mongo/export_aggregation.py', 'r') as f:
    content = f.read()

target1 = '"date_str": 1,'
replacement1 = '"date_str": {"$ifNull": ["$date_str", {"$ifNull": ["$date", "2026-10-13"]}]},'
content = content.replace(target1, replacement1)

target2 = 'date = info["date"]'
replacement2 = 'date = info.get("date") or "2026-10-13"'
content = content.replace(target2, replacement2)

with open('/home/mithra/air-quality-ews/mongo/export_aggregation.py', 'w') as f:
    f.write(content)

print("Successfully patched /home/mithra/air-quality-ews/mongo/export_aggregation.py")
