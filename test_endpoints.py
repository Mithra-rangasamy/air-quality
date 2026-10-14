import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200
    data = res.json()
    print("1. Health Endpoint:", data)
    assert data["status"] == "healthy"
    assert data["services"]["mongodb"] == "UP"
    assert "UP" in data["services"]["hiveserver2"]
    assert data["services"]["hadoop_hdfs"] == "UP"

def test_zones_risk():
    res = requests.get(f"{BASE_URL}/api/zones/risk")
    assert res.status_code == 200
    data = res.json()
    print(f"2. Zones Risk: {data['total_zones']} zones loaded on date {data['date']}")
    assert data["total_zones"] == 25
    top = data["data"][0]
    print(f"   Top Risk Zone: {top['zone_name']} ({top['city']}) - Risk: {top['risk_score']}, Level: {top['risk_level']}, Compound Alert: {top['compound_alert']}")
    # Verify outbreak zone is top
    assert top["risk_level"] in ["RED", "ORANGE"]
    # Check false alarm zone BOM_ZN_01
    bom = next(z for z in data["data"] if z["zone_id"] == "BOM_ZN_01")
    print(f"   False Alarm Zone: {bom['zone_name']} - AQI: {bom['avg_aqi']}, Risk: {bom['risk_score']}, Level: {bom['risk_level']}, Compound Alert: {bom['compound_alert']}")
    assert bom["compound_alert"] is False

def test_zone_trend():
    res = requests.get(f"{BASE_URL}/api/zones/CBE_ZN_01/trend")
    assert res.status_code == 200
    data = res.json()
    print(f"3. Zone Trend CBE_ZN_01: {len(data['trend'])} days of trend data")
    assert len(data["trend"]) == 31

def test_complaints_summary():
    res = requests.get(f"{BASE_URL}/api/complaints/summary")
    assert res.status_code == 200
    data = res.json()["data"]
    print(f"4. Complaints Summary: {data['total_reports']} total reports in MongoDB. Top symptoms: {[s['symptom'] for s in data['symptoms'][:3]]}")
    assert data["total_reports"] > 0

def test_admin_ranking():
    res = requests.get(f"{BASE_URL}/api/admin/ranking")
    assert res.status_code == 200
    data = res.json()
    print(f"5. Admin Rankings: {len(data['cities'])} cities ranked. Top city: {data['cities'][0]['city']} (Red zones: {data['cities'][0]['red_zones']}, Compound alerts: {data['cities'][0]['compound_alerts']})")
    assert len(data["cities"]) == 5

def test_complaint_submission():
    payload = {
        "zone_id": "CBE_ZN_01",
        "citizen_name": "CIT Lab Tester",
        "symptoms": ["cough", "shortness_of_breath"],
        "severity": "severe",
        "age_group": "adult",
        "description": "Automated verification test report"
    }
    res = requests.post(f"{BASE_URL}/api/complaints", json=payload)
    assert res.status_code == 201
    data = res.json()
    print("6. Citizen Complaint Submission:", data)
    assert data["status"] == "success"
    assert "report_id" in data
    
    # Clean up test complaint to maintain clean database state
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/")
        client["air_quality_ews"]["symptom_reports"].delete_one({"report_id": data["report_id"]})
        client.close()
    except Exception as e:
        print("Note on cleanup:", e)

def test_tamilnadu_districts():
    res = requests.get(f"{BASE_URL}/api/tamilnadu/districts")
    assert res.status_code == 200
    data = res.json()
    print(f"7. Tamil Nadu Districts Surveillance: {data['total_districts']} districts loaded for state")
    assert data["status"] == "success"
    assert data["total_districts"] == 30
    cbe = next(d for d in data["districts"] if d["district_name"] == "Coimbatore")
    assert cbe["risk_level"] == "RED"
    assert cbe["compound_alert"] is True

if __name__ == "__main__":
    print("=== RUNNING FLASK REST API VERIFICATION ===")
    test_health()
    test_zones_risk()
    test_zone_trend()
    test_complaints_summary()
    test_admin_ranking()
    test_complaint_submission()
    test_tamilnadu_districts()
    print("=== ALL 7 API TEST SUITES PASSED CLEANLY! ===")
