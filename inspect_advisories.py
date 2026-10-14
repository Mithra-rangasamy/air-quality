import json

with open("/home/mithra/air-quality-ews/config/advisories.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("RED groups:", list(data["tiers"]["RED"]["groups"].keys()))
sample = data["tiers"]["RED"]["groups"]["children"]
print("RED -> children:", sample)
