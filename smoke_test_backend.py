import sys
sys.path.append('/home/mithra/air-quality-ews/backend')
from hive_client import HiveClient
from mongo_client import MongoEWSClient
from advisories import AdvisoryEngine

print("Initializing HiveClient...")
hc = HiveClient()
latest_date = hc.get_latest_date()
records = hc.get_zone_risks_for_date(latest_date)
print(f"HiveClient: Latest date = {latest_date}, Zone records count = {len(records)}")

print("Initializing MongoEWSClient...")
mc = MongoEWSClient()
cbe_sum = mc.get_complaints_summary('CBE_ZN_01')
print(f"MongoEWSClient: CBE_ZN_01 total complaints = {cbe_sum['total_reports']}, Top symptom = {cbe_sum['symptoms'][0] if cbe_sum['symptoms'] else 'None'}")

print("Initializing AdvisoryEngine...")
adv_engine = AdvisoryEngine()
outbreak_zone = next(r for r in records if r['zone_id'] == 'CBE_ZN_01')
adv = adv_engine.generate_advisory(outbreak_zone)
print(f"Advisory for {outbreak_zone['zone_name']}: Headline = {adv['headline']}, Compound Alert = {adv['compound_alert']}")
print("ALL BACKEND MODULES OPERATIONAL!")
