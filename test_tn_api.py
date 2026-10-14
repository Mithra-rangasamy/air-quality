import requests

res = requests.get("http://localhost:5000/api/tamilnadu/districts")
assert res.status_code == 200
data = res.json()
print("Status:", data["status"])
print("State:", data["state"])
print("Total Districts:", data["total_districts"])
print("\nTop 5 Vulnerable Tamil Nadu Districts:")
for d in data["districts"][:5]:
    print(f"  {d['district_name']:<18} | Risk: {d['risk_score']:<5} | Level: {d['risk_level']:<6} | Alert: {str(d['compound_alert']):<5} | AQI: {d['avg_aqi']}")

print("\nSUCCESS: /api/tamilnadu/districts operational!")
