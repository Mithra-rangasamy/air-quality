import json
import os

advisories_json_path = "/home/mithra/air-quality-ews/config/advisories.json"
with open(advisories_json_path, "r", encoding="utf-8") as f:
    adv_data = json.load(f)

def get_group_advisory(tier, group="general_public", lang="en", dominant_pollutant="pm25"):
    tier_info = adv_data.get("tiers", {}).get(tier, adv_data["tiers"]["GREEN"])
    headline = tier_info.get("headline", {}).get(lang, tier_info["headline"]["en"])
    group_advice = tier_info.get("groups", {}).get(group, {}).get(lang, "")
    
    pollutant_notice = ""
    if dominant_pollutant and dominant_pollutant in adv_data.get("dominant_pollutant_notices", {}):
        pollutant_notice = adv_data["dominant_pollutant_notices"][dominant_pollutant].get(lang, "")
        
    return {
        "tier": tier,
        "group": group,
        "lang": lang,
        "headline": headline,
        "advice": group_advice,
        "pollutant_notice": pollutant_notice
    }

print("Sample TA advisory for children in RED tier:")
res = get_group_advisory("RED", "children", "ta", "pm25")
print(res)
print("\nSample HI advisory for asthma_cardiac in COMPOUND_ALERT:")
res2 = get_group_advisory("COMPOUND_ALERT", "asthma_cardiac", "hi", "pm10")
print(res2)
