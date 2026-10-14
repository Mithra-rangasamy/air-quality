# Multi-City Air Quality & Public Health Early-Warning System

**Course:** 21MDS56 – Big Data Computing Laboratory  
**Degree Program:** M.Sc Data Science  
**Institution:** Coimbatore Institute of Technology (CIT), Coimbatore  
**Author:** Mithra  
**Environment:** WSL2 Ubuntu 24.04 LTS (Hadoop 3.3.6, Hive 4.0.1, Pig 0.17.0, MongoDB 8.0.32, Python 3.12)  

---

## 1. Executive Summary

Urban air pollution monitoring has traditionally focused purely on physical air quality metrics (ambient AQI, $PM_{2.5}$, $PM_{10}$). However, physical metrics alone cannot detect clinical morbidity variations or distinguish between toxic biological threats and localized benign dust (such as construction debris). 

This project implements an end-to-end, multi-modal Big Data processing system that continuously ingests **structured air quality and meteorological telemetry** alongside **unstructured citizen health reports** across 5 major Indian metropolitan hubs (**Coimbatore, Chennai, Bengaluru, Delhi, Mumbai**; 25 distinct monitoring zones) and surveillance across **all 30 districts of Tamil Nadu**.

The system fuses both data modalities using **Apache Pig** on **Hadoop MapReduce**, computes a daily **Composite Health-Risk Score (0–100)**, classifies each zone into **Green / Yellow / Orange / Red** risk tiers, detects **Compound Outbreak Alerts**, and delivers actionable, plain-language clinical advisories via an interactive **Leaflet.js + Chart.js** dashboard accessible at `http://localhost:5000`.

---

## 2. Architecture & Technology Stack

| Component | Technology | Role & Implementation Details |
| :--- | :--- | :--- |
| **Distributed Storage** | **Apache Hadoop HDFS 3.3.6** | Dual-partitioned raw data lake (`/data/raw/aqi` and `/data/raw/weather`), partitioned by `date` and `city` (155 partitions each; 36,000 hourly records total). Processed datasets stored in `/data/processed/`. |
| **Structured Analytics** | **Apache Hive 4.0.1** | External tables with partition pruning. MapReduce analytical queries (7-day moving averages, diurnal traffic cycles, city-to-city benchmarks). Daily zone aggregates in `/data/processed/daily_aqi_agg` and `/data/processed/daily_pollutant_agg`. |
| **Unstructured Analytics**| **MongoDB 8.0.32** | Document store for citizen complaints and social telemetry. Aggregation pipeline to calculate complaint densities and weighted symptom severity scores into `/data/processed/complaint_agg`. Quality filter gate routing spam/duplicates to `rejected_reports`. |
| **Big Data Fusion Engine**| **Apache Pig 0.17.0** | Relational `LEFT OUTER JOIN` on `(zone_id, date)` over MapReduce. Computes weighted risk formula, handles data sparsity, and applies compound alert escalation into `/data/processed/zone_risk_score`. |
| **Serving & Dashboard** | **Flask + Leaflet.js + Chart.js** | Python 3.12 backend on `0.0.0.0:5000` with sub-millisecond in-memory caching. Tamil Nadu state GeoJSON choropleth, dark-mode map, color-coded risk markers, pulsing compound halos, 30-day multi-axis trend charts, and real-time citizen reporting portal. |

---

## 3. Core Enterprise Features Implemented (A through O)

The system fulfills all 15 advanced enterprise features in strict priority order:

| Feature | Code | Description & Implementation |
| :--- | :---: | :--- |
| **Pollutant Analytics** | `A` | 6-pollutant storage ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3$) in Hive; dominant pollutant calculation using CPCB standard break-point normalization; drill-down panel. |
| **Vulnerable-Group Advisories**| `B` | Demographic-specific advisories for Children, Elderly, Asthmatics, Pregnant Women, Outdoor Workers, and General Public stored in `config/advisories.json`. |
| **Sensor Freshness Monitor** | `F` | 24-hour reading count tracking; stale detection ($>3\text{h}$ missing); grey warning styling (`DATA UNAVAILABLE / SENSOR STALE`), never defaulted to Green. |
| **Statistical Anomaly Detection**| `C` | 30-day rolling Z-score calculation; flags $|z| > 2.0 / 2.5$ as industrial plumes or sensor glitches; highlighted on trend charts and admin view. |
| **Lag-Correlation Analysis** | `D` | Pearson correlation at lags $0, 1, 2, 3$ days between daily AQI and citizen complaints; stored in Hive table `aqi_complaint_correlation` ($r = 0.748$). |
| **Complaint Quality Gate** | `E` | Pre-aggregation validation in MongoDB; rejects spam ($<4$ chars), rate limits ($>5/\text{day}$), and duplicates ($<1\text{h}$); routed to `rejected_reports`. |
| **Pipeline Status Monitor** | `G` | Execution run tracking in MongoDB `pipeline_runs` (duration, records processed, status per stage); web dashboard at `/status`. |
| **Explainable AQI Forecast** | `H` | 24-hour hourly predictive model using diurnal atmospheric inversion cycles combined with 3-day trend momentum; documented in `docs/forecast.md`. |
| **Alert History & Cooldown** | `I` | Logs Red/Compound outbreak alerts in MongoDB `alert_history` enforcing a 6-hour cooldown per zone to prevent notification fatigue; web page at `/alerts`. |
| **Nearby Emergency Facilities**| `J` | Facilities registry (`config/facilities.json`); Haversine proximity search; hospital (🏥) and school (🏫) map markers within 3–8 km. |
| **Multilingual Advisories** | `K` | Full localized advisory rendering in **English**, **Tamil (தமிழ்)**, and **Hindi (हिंदी)** with dynamic instant switching. |
| **Map Enhancements & CSV Export**| `L` | Leaflet Heatmap layer toggle (`leaflet-heat.js`), 7-day interactive time-slider replay, and downloadable CSV export (`/api/export/ranking.csv`). |
| **Citizen Portal ("Check My Area")**| `M` | Clean, citizen-facing portal at `/check`; locality selector, demographic filter, language toggle, risk badge, and nearest emergency hospital. |
| **Performance Benchmark** | `N` | Partitioned vs non-partitioned Hive table analytical experiment; MapReduce splits and bytes scanned documented in `docs/benchmark.md`. |
| **Admin Authentication** | `O` | Session-based login protecting `/admin`, `/alerts`, and `/status` via `.env` credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`). |

---

## 4. Kept Citizen-Facing Enhancements

| Feature | Scope | Key Capabilities & Verification |
| :--- | :---: | :--- |
| **1. Current Location Auto-Detection** | Citizen | Geolocation API + `/api/zones/nearest` haversine proximity detection. Selects nearest zone ($\le 50$ km) with distance badge. Zero server-side coordinate storage. |
| **2. Share Option & Deep Linking** | Citizen | Web Share API (`navigator.share`), WhatsApp direct link, copy-to-clipboard toast confirmation, and deep-linking query parameter `?zone=<id>`. |
| **3. Guided Onboarding Tour** | Citizen | 4-step progressive onboarding walkthrough introducing the Map, Current Location button, Symptom Reporting, and Share Advisory with `localStorage` memory. |

---

## 5. Quick Start & Execution

```bash
# 1. Start all Big Data services (HDFS, YARN, HiveServer2, MongoDB)
make services

# 2. Check health status and active ports
make status

# 3. Generate synthetic data & ingest into HDFS / MongoDB
make ingest

# 4. Run Hive structured aggregations
make hive

# 5. Run MongoDB unstructured symptom aggregations
make mongo

# 6. Execute Apache Pig Multi-Modal Fusion Engine
make pig

# 7. Run the entire pipeline end-to-end
make pipeline

# 8. Launch the Flask Dashboard
make dashboard

# 9. Run automated test suite (22 unit, integration & end-to-end tests)
make test
```

### Accessing the Dashboard & Portals
Open your host browser and navigate to:
- **Main Surveillance Dashboard**: `http://localhost:5000/`
- **Citizen "Check My Area" Portal**: `http://localhost:5000/check`
- **Pipeline Execution Health Page**: `http://localhost:5000/status`
- **Outbreak Alerts History**: `http://localhost:5000/alerts`
- **Municipal Admin Console**: `http://localhost:5000/admin` (Default: `admin` / `admin123`)

---

## 6. Complete REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Cluster health check verifying HDFS, HiveServer2, and MongoDB. |
| `GET` | `/api/zones/nearest?lat=...&lon=...`| Haversine proximity resolver for nearest zone (up to 50 km). |
| `GET` | `/api/zones/risk?date=...` | Returns composite risk scores, dominant pollutants, and advisories for all 25 zones. |
| `GET` | `/api/zones/<id>/pollutants` | 6-pollutant breakdown ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3$), standards, and dominant ratio. |
| `GET` | `/api/advisory?zone=...&group=...&lang=...` | Tailored advisory by demographic group (`children`, `elderly`, etc.) and language (`en`, `ta`, `hi`). |
| `GET` | `/api/freshness` | Sensor freshness metrics and staleness status ($>3\text{h}$ check). |
| `GET` | `/api/anomalies` | Statistical anomaly spikes ($|z| > 2.0 / 2.5$) for plume detection. |
| `GET` | `/api/correlation` | Pearson cross-correlation between daily AQI and complaints at lags 0..3. |
| `POST`| `/api/complaints` | Citizen complaint ingestion with spam, rate limit, and dedup filtering. |
| `GET` | `/api/complaints/rejected` | Audit log of rejected complaints with rejection reasons. |
| `GET` | `/api/pipeline/status` | Recent pipeline execution runs and stage durations from MongoDB. |
| `GET` | `/api/forecast/<zone_id>` | 24-hour explainable hourly AQI forecast with 95% confidence bounds. |
| `GET` | `/api/alerts` | Historical logged Red/Compound outbreak alerts with 6-hour cooldown. |
| `GET` | `/api/facilities/nearby?zone=...` | Proximity locator for emergency hospitals and schools within radius. |
| `GET` | `/api/export/ranking.csv` | Downloadable CSV export of ranked zones, risk scores, and advisories. |
| `GET` | `/api/tamilnadu/districts` | Surveillance metrics across all 30 districts of Tamil Nadu. |

---

## 7. Verification & Automated Test Suite Results

Run the complete test suite:
```bash
~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests/
```

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /home/mithra/air-quality-ews/venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/mithra/air-quality-ews
collected 22 items

tests/test_api.py::test_health PASSED                                    [  4%]
tests/test_api.py::test_zones_risk PASSED                                [  9%]
tests/test_api.py::test_pollutants_feature_a PASSED                      [ 13%]
tests/test_api.py::test_vulnerable_group_advisories_feature_b_k PASSED   [ 18%]
tests/test_api.py::test_sensor_freshness_feature_f PASSED                [ 22%]
tests/test_api.py::test_anomalies_feature_c PASSED                       [ 27%]
tests/test_api.py::test_lag_correlation_feature_d PASSED                 [ 31%]
tests/test_api.py::test_complaint_quality_filter_feature_e PASSED        [ 36%]
tests/test_api.py::test_pipeline_status_feature_g PASSED                 [ 40%]
tests/test_api.py::test_forecast_feature_h PASSED                        [ 45%]
tests/test_api.py::test_alerts_history_feature_i PASSED                  [ 50%]
tests/test_api.py::test_nearby_facilities_feature_j PASSED               [ 54%]
tests/test_api.py::test_csv_export_feature_l PASSED                      [ 59%]
tests/test_api.py::test_html_pages_feature_m_g_i_o PASSED                [ 63%]
tests/test_new_features.py::test_nearest_zone_geolocation PASSED         [ 68%]
tests/test_new_features.py::test_share_deep_link PASSED                  [ 72%]
tests/test_new_features.py::test_guided_tour PASSED                      [ 77%]
tests/test_services.py::test_mongodb PASSED                              [ 81%]
tests/test_services.py::test_hiveserver2 PASSED                          [ 86%]
tests/test_services.py::test_hdfs PASSED                                 [ 90%]
tests/test_services.py::test_pig PASSED                                  [ 95%]
tests/test_tn_api.py::test_tamilnadu_districts PASSED                    [100%]

============================= 22 passed in 12.84s ==============================
```

**Result: 22 of 22 tests passing (100% SUCCESS)**
