import json

with open('/home/mithra/air-quality-ews/frontend/static/data/tamilnadu_districts.geojson') as f:
    d = json.load(f)

print(f"Total Features: {len(d['features'])}")
for idx, feat in enumerate(d['features']):
    props = feat.get('properties', {})
    print(f"District {idx+1}: {props}")
