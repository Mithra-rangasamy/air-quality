import requests
import json
import time

payload = {
    'zone_id': 'CBE_ZN_01',
    'citizen_name': f'Lakshmi Narayanan {int(time.time() * 1000)}',
    'symptoms': ['breathing difficulty', 'cough', 'eye irritation'],
    'severity': 'severe',
    'age_group': 'senior',
    'description': ''
}
res = requests.post('http://localhost:5000/api/complaints', json=payload)
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")
