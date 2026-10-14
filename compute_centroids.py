import json

with open('/home/mithra/air-quality-ews/frontend/static/data/tamilnadu_districts.geojson') as f:
    d = json.load(f)

district_centroids = {}
for feat in d['features']:
    name = feat['properties']['NAME_2']
    # Calculate simple bounding box / average coords
    coords = feat['geometry']['coordinates']
    all_pts = []
    def extract_pts(c):
        if isinstance(c[0], (int, float)):
            all_pts.append(c)
        else:
            for sub in c:
                extract_pts(sub)
    extract_pts(coords)
    if all_pts:
        avg_lon = sum(p[0] for p in all_pts) / len(all_pts)
        avg_lat = sum(p[1] for p in all_pts) / len(all_pts)
        district_centroids[name] = [round(avg_lat, 4), round(avg_lon, 4)]

print("Computed centroids for", len(district_centroids), "districts:")
for k, v in sorted(district_centroids.items())[:10]:
    print(f"  {k}: {v}")

with open('/home/mithra/air-quality-ews/frontend/static/data/district_centroids.json', 'w') as f:
    json.dump(district_centroids, f, indent=2)
print("Saved to district_centroids.json")
