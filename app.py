"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/app.py - Main Flask Application Serving REST APIs and Multi-Modal Dashboard
Implements Features A through O + Citizen-Facing (1-6) & Admin-Facing (7-12) Enhancements
"""

import csv
import datetime
from functools import wraps
import io
import json
import logging
import math
import os
import subprocess
import sys
from typing import Dict, Any, Optional
from flask import Flask, jsonify, render_template, request, Response, session, redirect, url_for

# Ensure backend imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hive_client import HiveClient
from mongo_client import MongoEWSClient
from advisories import AdvisoryEngine
from tamilnadu_service import TamilNaduSurveillanceService
from forecast_service import ForecastEngine
from facilities_service import FacilitiesService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EWSApp")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "zones.json")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static")
)
app.secret_key = os.getenv("SECRET_KEY", "cit-bigdata-21mds56-secret-key-2026")

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

# Load zone geographic metadata
zones_metadata = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        zdata = json.load(f)
        city_list = zdata if isinstance(zdata, list) else zdata.get("cities", [])
        for city_info in city_list:
            city_name = city_info.get("city") or city_info.get("name", "Unknown")
            for z in city_info.get("zones", []):
                zones_metadata[z["zone_id"]] = {
                    "lat": z.get("latitude") or z.get("lat", 11.0168),
                    "lon": z.get("longitude") or z.get("lon", 76.9558),
                    "baseline_aqi": z.get("baseline_aqi", 100),
                    "scenario": z.get("scenario", "normal"),
                    "city": city_name,
                    "zone_name": z.get("zone_name", "Local Zone")
                }

# Initialize Big Data clients & analytical services
hive_client = HiveClient()
mongo_client = MongoEWSClient()
advisory_engine = AdvisoryEngine()
tn_service = TamilNaduSurveillanceService(hive_client=hive_client)
forecast_engine = ForecastEngine(hive_client=hive_client)
facilities_service = FacilitiesService()


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_hdr = request.headers.get("Authorization", "")
        admin_key = request.headers.get("X-Admin-Key", "")
        if session.get("logged_in") or admin_key == ADMIN_PASS or auth_hdr.endswith(ADMIN_PASS):
            return f(*args, **kwargs)
        if request.path.startswith("/api/admin"):
            return jsonify({"status": "error", "message": "Admin authentication required"}), 401
        return redirect(url_for("login_view", next=request.url))
    return decorated_function


# =============================================================================
# Web Page Views
# =============================================================================
@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/check")
def check_view():
    """Feature M: Citizen Portal 'Check My Area'."""
    return render_template("check.html")


@app.route("/status")
def status_view():
    """Feature G: Pipeline Execution Status Page."""
    return render_template("status.html")


@app.route("/alerts")
def alerts_view():
    """Feature I: Alert Notifications & Outbreak History Page."""
    return render_template("alerts.html")


@app.route("/admin")
@admin_required
def admin_view():
    """Feature O & Features 7-9: Administrative Management Console."""
    return render_template("admin.html")


@app.route("/admin/report")
@admin_required
def admin_report_view():
    """Feature 10: Printable Daily Situation Report Page."""
    return render_template("report.html")


@app.route("/login", methods=["GET", "POST"])
def login_view():
    """Feature O: Session Authentication Login."""
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            next_url = request.args.get("next") or url_for("admin_view")
            return redirect(next_url)
        else:
            error = "Invalid administrator credentials."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout_view():
    session.clear()
    return redirect(url_for("index"))


# =============================================================================
# Core Fusion & Risk Analytics APIs
# =============================================================================
@app.route("/api/zones/risk", methods=["GET"])
def get_zones_risk():
    """Returns composite health risk score, tier, and dominant pollutant per zone."""
    target_date = request.args.get("date")
    lang = request.args.get("lang", "en")
    group = request.args.get("group", "general_public")

    data = hive_client.get_zone_risks_for_date(target_date)

    # Attach coordinates and localized advisories
    for item in data:
        zid = item["zone_id"]
        if zid in zones_metadata:
            item["lat"] = zones_metadata[zid]["lat"]
            item["lon"] = zones_metadata[zid]["lon"]
            item["city"] = zones_metadata[zid]["city"]
            item["zone_name"] = zones_metadata[zid]["zone_name"]

        # Ensure dominant pollutant details are present
        pol_data = hive_client.get_zone_pollutants(zid, item.get("date"))
        if pol_data and pol_data.get("status") == "success":
            item["dominant_pollutant"] = pol_data.get("dominant_pollutant", "pm25")
            item["dominant_pollutant_name"] = pol_data.get("dominant_pollutant_name", "PM2.5")
            item["dominant_ratio"] = pol_data.get("dominant_ratio", 1.0)
            item["pollutants"] = pol_data.get("pollutants", {})
        else:
            item["dominant_pollutant"] = item.get("dominant_pollutant", "pm25")
            item["dominant_pollutant_name"] = item.get("dominant_pollutant_name", "PM2.5")

        # Multilingual advisory with demographic tailoring (Features B & K)
        adv = advisory_engine.generate_advisory(
            zone_record=item,
            group=group,
            lang=lang
        )
        item["advisory"] = adv

        # Auto-log compound/red outbreaks with 6h cooldown (Feature I)
        if item.get("compound_alert") or item.get("risk_level") == "RED":
            mongo_client.log_alert({
                "zone_id": zid,
                "zone_name": item.get("zone_name"),
                "city": item.get("city"),
                "severity": item.get("risk_level"),
                "compound_alert": item.get("compound_alert"),
                "avg_aqi": item.get("avg_aqi"),
                "complaint_count": item.get("complaint_count"),
                "headline": adv.get("headline"),
                "message": adv.get("summary"),
                "date": item.get("date")
            })

    return jsonify({
        "status": "success",
        "total_zones": len(data),
        "count": len(data),
        "date": target_date or hive_client.get_latest_date(),
        "data": data
    })


@app.route("/api/zones/<zone_id>/trend", methods=["GET"])
def get_zone_trend(zone_id):
    """Returns 30-day historical time series for AQI, complaints, and risk scores."""
    trend_data = hive_client.get_zone_trend(zone_id)
    if not trend_data:
        return jsonify({"status": "error", "message": f"No trend data found for zone {zone_id}"}), 404

    for item in trend_data:
        if zone_id in zones_metadata:
            item["lat"] = zones_metadata[zone_id]["lat"]
            item["lon"] = zones_metadata[zone_id]["lon"]
            item["city"] = zones_metadata[zone_id]["city"]
            item["zone_name"] = zones_metadata[zone_id]["zone_name"]

    return jsonify({"status": "success", "zone_id": zone_id, "data": trend_data})


@app.route("/api/zones/<zone_id>/pollutants", methods=["GET"])
def get_zone_pollutants(zone_id):
    """Feature A: Returns 6-criteria pollutant concentrations and dominant concern."""
    target_date = request.args.get("date")
    result = hive_client.get_zone_pollutants(zone_id, target_date)
    return jsonify(result)


@app.route("/api/advisory", methods=["GET"])
def get_advisory():
    """Features B & K: Tailored advisories across 6 demographic groups and 3 languages."""
    zone_id = request.args.get("zone")
    group = request.args.get("group", "general_public")
    lang = request.args.get("lang", "en")
    target_date = request.args.get("date")

    risk_level = "GREEN"
    dominant = "PM2.5"
    compound = False
    zone_record = {}

    if zone_id:
        risk_data = hive_client.get_zone_risks_for_date(target_date)
        match = next((z for z in risk_data if z["zone_id"] == zone_id), None)
        if match:
            zone_record = dict(match)
            risk_level = match.get("risk_level", "GREEN")
            dominant = match.get("dominant_pollutant_name", "PM2.5")
            compound = match.get("compound_alert", False)

    if not zone_record:
        zone_record = {
            "zone_id": zone_id or "ZN_01",
            "risk_level": risk_level,
            "dominant_pollutant": dominant,
            "compound_alert": compound
        }

    adv = advisory_engine.generate_advisory(
        zone_record=zone_record,
        risk_level=risk_level,
        dominant_pollutant=dominant,
        compound_alert=compound,
        group=group,
        lang=lang
    )
    return jsonify({
        "status": "success",
        "zone_id": zone_id,
        "group": group,
        "language": lang,
        "advisory": adv
    })


@app.route("/api/freshness", methods=["GET"])
def get_freshness():
    """Feature F: Evaluates hourly telemetry completeness; flags stale sensors (>3h offline)."""
    target_date = request.args.get("date")
    freshness = hive_client.get_sensor_freshness(target_date)
    return jsonify({
        "status": "success",
        "total_stations": len(freshness),
        "data": freshness
    })


@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    """Feature C: Z-score rolling statistical anomaly plume detection."""
    threshold = float(request.args.get("threshold", 2.0))
    anomalies = hive_client.get_anomalies()
    return jsonify({
        "status": "success",
        "threshold": threshold,
        "total_anomalies": len(anomalies),
        "data": anomalies
    })


@app.route("/api/correlation", methods=["GET"])
def get_correlation():
    """Feature D: Pearson cross-correlation between daily AQI and citizen complaints (lags 0 to 3)."""
    correlations = hive_client.get_lag_correlation()
    return jsonify(correlations)


# =============================================================================
# Feature E & Feature 3: Citizen Complaints with Quality Gate
# =============================================================================
@app.route("/api/complaints", methods=["POST"])
def submit_complaint():
    """Feature 3: Citizen complaint submission with chips, severity, and quality filtering."""
    data = request.get_json() or {}
    if not data.get("zone_id"):
        return jsonify({"status": "error", "message": "zone_id is required"}), 400

    zid = data["zone_id"]
    if zid in zones_metadata:
        data["city"] = zones_metadata[zid]["city"]
        data["zone_name"] = zones_metadata[zid]["zone_name"]

    res = mongo_client.submit_complaint(data)
    status_code = 201 if res.get("status") == "success" else 422
    return jsonify(res), status_code


@app.route("/api/complaints/rejected", methods=["GET"])
def get_rejected_complaints():
    """Feature E: Returns rejected reports with rejection reasons for audit."""
    limit = int(request.args.get("limit", 25))
    rejected = mongo_client.get_rejected_reports(limit=limit)
    return jsonify({"status": "success", "count": len(rejected), "data": rejected})


# =============================================================================
# Pipeline, Forecast & Emergency Services
# =============================================================================
@app.route("/api/status", methods=["GET"])
@app.route("/api/pipeline/status", methods=["GET"])
def get_pipeline_status():
    """Feature G: Returns recent pipeline run records, stage durations, and records processed."""
    limit = int(request.args.get("limit", 10))
    runs = mongo_client.get_recent_pipeline_runs(limit=limit)
    return jsonify({
        "status": "success",
        "total_runs": len(runs),
        "latest_run": runs[0] if runs else None,
        "runs": runs
    })


@app.route("/api/forecast/<zone_id>", methods=["GET"])
def get_forecast(zone_id):
    """Feature H: 24-hour diurnal harmonic forecasting model with confidence bounds."""
    target_date = request.args.get("date")
    result = forecast_engine.generate_24h_forecast(zone_id, base_date=target_date)
    return jsonify(result)


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Feature I: Returns history of logged alerts."""
    limit = int(request.args.get("limit", 50))
    zone_id = request.args.get("zone_id")
    history = mongo_client.get_alert_history(limit=limit, zone_id=zone_id)
    return jsonify({
        "status": "success",
        "total_alerts": len(history),
        "count": len(history),
        "data": history
    })


@app.route("/api/facilities/nearby", methods=["GET"])
def get_nearby_facilities():
    """Feature J: Haversine distance proximity locator for hospitals and schools."""
    zone_id = request.args.get("zone")
    if not zone_id or zone_id not in zones_metadata:
        return jsonify({"status": "error", "message": "Valid zone query parameter required"}), 400

    zinfo = zones_metadata[zone_id]
    facilities = facilities_service.get_facilities_for_zone(
        zone_id=zone_id,
        lat=zinfo["lat"],
        lon=zinfo["lon"],
        city=zinfo["city"]
    )
    return jsonify(facilities)


@app.route("/api/export/ranking.csv", methods=["GET"])
def export_ranking_csv():
    """Feature L: Downloadable CSV export of ranked zones, risk scores, and advisories."""
    target_date = request.args.get("date")
    zones = hive_client.get_zone_risks_for_date(target_date)
    sorted_zones = sorted(zones, key=lambda z: (z.get("compound_alert", False), z.get("risk_score", 0)), reverse=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Zone_ID", "Zone_Name", "City", "Date", "Ambient_AQI",
        "Composite_Risk_Score", "Risk_Level", "Compound_Alert", "Complaint_Count",
        "Dominant_Pollutant", "Advisory_Headline"
    ])

    for rank, z in enumerate(sorted_zones, start=1):
        adv = advisory_engine.generate_advisory(zone_record=z)
        writer.writerow([
            rank, z["zone_id"], z["zone_name"], z["city"], z["date"],
            f"{z['avg_aqi']:.1f}", f"{z['risk_score']:.1f}", z["risk_level"],
            "YES" if z.get("compound_alert") else "NO", z["complaint_count"],
            z.get("dominant_pollutant_name", "PM2.5").upper(), adv.get("headline", "")
        ])

    csv_data = output.getvalue()
    filename = f"aqi_health_ranking_{target_date or hive_client.get_latest_date()}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/tamilnadu/districts", methods=["GET"])
def get_tamilnadu_districts():
    """Tamil Nadu State-Wide Environmental & Public Health Surveillance (30 Districts)."""
    target_date = request.args.get("date")
    districts = tn_service.get_district_surveillance(target_date)
    return jsonify({
        "status": "success",
        "state": "Tamil Nadu",
        "total_districts": len(districts),
        "date": target_date or hive_client.get_latest_date(),
        "districts": districts
    })


@app.route("/api/admin/ranking", methods=["GET"])
def get_admin_ranking():
    """Returns city-level and zone-level risk vulnerability rankings for municipal response."""
    target_date = request.args.get("date")
    city_rankings = hive_client.get_city_rankings(target_date)
    all_zones = hive_client.get_zone_risks_for_date(target_date)
    top_vulnerable_zones = sorted(all_zones, key=lambda x: x["risk_score"], reverse=True)[:10]

    return jsonify({
        "status": "success",
        "date": target_date or hive_client.get_latest_date(),
        "cities": city_rankings,
        "top_vulnerable_zones": top_vulnerable_zones
    })


# =============================================================================
# New Citizen-Facing & Admin Endpoints (Features 1, 2, 5, 7, 8, 9, 10)
# =============================================================================
@app.route("/api/config/advice-simple", methods=["GET"])
def get_advice_simple():
    """Feature 1: Serves simple one-sentence advice config."""
    cfg_file = os.path.join(BASE_DIR, "config", "advice_simple.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route("/api/config/explainer", methods=["GET"])
def get_explainer():
    """Feature 5: Serves everyday language explainer content."""
    cfg_file = os.path.join(BASE_DIR, "config", "explainer.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route("/api/zones/nearest", methods=["GET"])
def get_nearest_zone():
    """Feature 2: Helper endpoint to detect nearest zone using haversine distance."""
    try:
        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("lon", 0))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Valid lat and lon float query parameters required"}), 400

    closest_zone = None
    min_dist = float("inf")

    for zid, zinfo in zones_metadata.items():
        dist = haversine_distance(lat, lon, zinfo["lat"], zinfo["lon"])
        if dist < min_dist:
            min_dist = dist
            closest_zone = {
                "zone_id": zid,
                "zone_name": zinfo["zone_name"],
                "city": zinfo["city"],
                "lat": zinfo["lat"],
                "lon": zinfo["lon"],
                "distance_km": dist
            }

    return jsonify({
        "status": "success",
        "nearest_zone": closest_zone,
        "is_within_50km": (min_dist <= 50.0) if min_dist != float("inf") else False
    })


@app.route("/api/admin/summary", methods=["GET"])
@admin_required
def get_admin_summary():
    """Feature 7: Admin top summary cards (Red, Orange, Complaints, Compound, Stale)."""
    target_date = request.args.get("date") or hive_client.get_latest_date()
    zones = hive_client.get_zone_risks_for_date(target_date)
    freshness = hive_client.get_sensor_freshness(target_date)
    red_count = sum(1 for z in zones if z.get("risk_level") == "RED")
    orange_count = sum(1 for z in zones if z.get("risk_level") == "ORANGE")
    compound_count = sum(1 for z in zones if z.get("compound_alert"))
    stale_count = sum(1 for item in freshness if item.get("is_stale"))
    complaints_today = mongo_client.count_complaints_for_date(target_date)

    return jsonify({
        "status": "success",
        "date": target_date,
        "summary": {
            "red_zones": red_count,
            "orange_zones": orange_count,
            "compound_alerts": compound_count,
            "complaints_today": complaints_today,
            "stale_stations": stale_count,
            "total_zones": len(zones)
        }
    })


@app.route("/api/admin/alerts", methods=["GET"])
@admin_required
def get_admin_alert_actions():
    """Feature 9: Alert Action Tracker list for Red/Orange/Compound zones."""
    target_date = request.args.get("date") or hive_client.get_latest_date()
    status_filter = request.args.get("status")

    actions = mongo_client.get_alert_actions(date=target_date, status=status_filter)

    # Auto-seed initial actions for all critical zones on this date if none registered yet
    if not actions:
        zones = hive_client.get_zone_risks_for_date(target_date)
        critical_zones = [z for z in zones if z.get("risk_level") in ["RED", "ORANGE"] or z.get("compound_alert")]
        for z in critical_zones:
            act_id = f"ACT-{z['zone_id']}-{target_date}"
            mongo_client.upsert_alert_action(
                action_id=act_id,
                zone_id=z["zone_id"],
                date=target_date,
                status="Open",
                notes="Automated trigger: Zone in alert status.",
                updated_by="system",
                defaults={
                    "zone_name": z["zone_name"],
                    "city": z["city"],
                    "risk_level": z["risk_level"],
                    "compound_alert": z.get("compound_alert", False),
                    "avg_aqi": z.get("avg_aqi", 0),
                    "complaints": z.get("complaint_count", 0)
                }
            )
        actions = mongo_client.get_alert_actions(date=target_date, status=status_filter)

    return jsonify({
        "status": "success",
        "date": target_date,
        "total": len(actions),
        "data": actions
    })


@app.route("/api/admin/alerts/<action_id>", methods=["PATCH"])
@admin_required
def update_admin_alert_action(action_id):
    """Feature 9: Update alert action status, notes, and log timeline history."""
    payload = request.get_json() or {}
    new_status = payload.get("status", "Acknowledged")
    notes = payload.get("notes", "Status updated by administrator.")
    updated_by = session.get("username") or payload.get("updated_by") or "admin"

    existing = mongo_client.get_alert_action_by_id(action_id)
    if not existing:
        return jsonify({"status": "error", "message": f"Alert action {action_id} not found"}), 404

    updated = mongo_client.upsert_alert_action(
        action_id=action_id,
        zone_id=existing["zone_id"],
        date=existing["date"],
        status=new_status,
        notes=notes,
        updated_by=updated_by,
        defaults=existing
    )
    return jsonify({"status": "success", "message": "Alert action updated successfully", "data": updated})


@app.route("/api/admin/report", methods=["GET"])
@admin_required
def get_admin_report_data():
    """Feature 10: Situational report structured data."""
    target_date = request.args.get("date") or hive_client.get_latest_date()
    zones = hive_client.get_zone_risks_for_date(target_date)
    sorted_zones = sorted(zones, key=lambda z: (z.get("compound_alert", False), z.get("risk_score", 0)), reverse=True)
    top_10 = sorted_zones[:10]

    red_count = sum(1 for z in zones if z.get("risk_level") == "RED")
    orange_count = sum(1 for z in zones if z.get("risk_level") == "ORANGE")
    compound_count = sum(1 for z in zones if z.get("compound_alert"))
    complaints_count = mongo_client.count_complaints_for_date(target_date)

    actions = mongo_client.get_alert_actions(date=target_date)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return jsonify({
        "status": "success",
        "date": target_date,
        "generated_at": now_str,
        "summary": {
            "total_zones": len(zones),
            "red_zones": red_count,
            "orange_zones": orange_count,
            "compound_alerts": compound_count,
            "complaints_count": complaints_count,
            "peak_aqi": max((z.get("avg_aqi", 0) for z in zones), default=0)
        },
        "top_zones": top_10,
        "active_compound_alerts": [z for z in zones if z.get("compound_alert")],
        "alert_actions": actions,
        "recommended_actions": {
            "RED": "Immediate mask mandate, suspension of outdoor schools/construction, activation of emergency hospital respiratory wards.",
            "ORANGE": "Advisory for sensitive groups, traffic rerouting away from high-density corridors.",
            "COMPOUND": "Critical emergency outbreak response: deploy mobile health clinics and distribute N95 respirators."
        }
    })


# =============================================================================
# Existing Helper Routes
# =============================================================================
@app.route("/api/social/feed", methods=["GET"])
def get_social_feed():
    city = request.args.get("city")
    feed = mongo_client.get_social_feed(city=city)
    return jsonify({"status": "success", "data": feed})


@app.route("/api/dates", methods=["GET"])
def get_dates():
    dates = hive_client.get_all_dates()
    return jsonify({"status": "success", "dates": dates, "latest": hive_client.get_latest_date()})


@app.route("/api/health", methods=["GET"])
def get_health():
    health_status = {
        "status": "healthy",
        "services": {
            "mongodb": "unknown",
            "hiveserver2": "unknown",
            "hadoop_hdfs": "unknown",
            "pig_fusion": "ready"
        }
    }

    try:
        mongo_client.client.admin.command("ping")
        health_status["services"]["mongodb"] = "UP"
    except Exception as e:
        health_status["services"]["mongodb"] = f"DOWN ({e})"

    try:
        test = hive_client.get_latest_date()
        health_status["services"]["hiveserver2"] = f"UP (Latest date: {test})"
    except Exception as e:
        health_status["services"]["hiveserver2"] = f"DOWN ({e})"

    try:
        proc = subprocess.run(["hdfs", "dfs", "-test", "-d", "/data/processed/zone_risk_score"], capture_output=True)
        health_status["services"]["hadoop_hdfs"] = "UP" if proc.returncode == 0 else "DEGRADED"
    except Exception as e:
        health_status["services"]["hadoop_hdfs"] = f"DOWN ({e})"

    return jsonify(health_status)


@app.route("/api/pipeline/trigger", methods=["POST"])
def trigger_pipeline():
    pipeline_script = os.path.join(BASE_DIR, "scheduler", "run_pipeline.sh")
    if os.path.exists(pipeline_script):
        try:
            subprocess.Popen(["bash", pipeline_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            hive_client.load_cache(force=True)
            hive_client.load_pollutants_cache(force=True)
            return jsonify({
                "status": "success",
                "message": "Pipeline recalculation initiated in background across Hive, Mongo, and Pig."
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        hive_client.load_cache(force=True)
        return jsonify({"status": "success", "message": "Cache refreshed successfully."})


if __name__ == "__main__":
    logger.info("Starting Multi-City Air Quality & Public Health Early-Warning System on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
