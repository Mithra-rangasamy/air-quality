with open("/home/mithra/air-quality-ews/backend/mongo_client.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'self.alert_actions = self.db["alert_actions"]' in line:
        continue
    if '# Feature 9: Alert Action Tracker' in line:
        skip = True
    if skip and 'def count_complaints_for_date' in line:
        skip = False
    if not skip:
        new_lines.append(line)

with open("/home/mithra/air-quality-ews/backend/mongo_client.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("SUCCESS: mongo_client.py cleaned")
