---

## Phase 8 & 9: Enterprise Features A through O Verification

```bash
$ ~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests/test_api.py
============================= test session starts ==============================
collected 14 items

tests/test_api.py::test_health PASSED                                    [  7%]
tests/test_api.py::test_zones_risk PASSED                                [ 14%]
tests/test_api.py::test_pollutants_feature_a PASSED                      [ 21%]
tests/test_api.py::test_vulnerable_group_advisories_feature_b_k PASSED   [ 28%]
tests/test_api.py::test_sensor_freshness_feature_f PASSED                [ 35%]
tests/test_api.py::test_anomalies_feature_c PASSED                       [ 42%]
tests/test_api.py::test_lag_correlation_feature_d PASSED                 [ 50%]
tests/test_api.py::test_complaint_quality_filter_feature_e PASSED        [ 57%]
tests/test_api.py::test_pipeline_status_feature_g PASSED                 [ 64%]
tests/test_api.py::test_forecast_feature_h PASSED                        [ 71%]
tests/test_api.py::test_alerts_history_feature_i PASSED                  [ 78%]
tests/test_api.py::test_nearby_facilities_feature_j PASSED               [ 85%]
tests/test_api.py::test_csv_export_feature_l PASSED                      [ 92%]
tests/test_api.py::test_html_pages_feature_m_g_i_o PASSED                [100%]

============================= 14 passed in 12.35s ==============================
```

---

## Phase 10 & 11: Citizen-Facing, Admin & Mobile-First Feature Test Suite

```bash
$ ~/air-quality-ews/venv/bin/pytest -v ~/air-quality-ews/tests/
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1 -- /home/mithra/air-quality-ews/venv/bin/python3
rootdir: /home/mithra/air-quality-ews
collected 25 items

tests/test_api.py::test_health PASSED                                    [  4%]
tests/test_api.py::test_zones_risk PASSED                                [  8%]
tests/test_api.py::test_pollutants_feature_a PASSED                      [ 12%]
tests/test_api.py::test_vulnerable_group_advisories_feature_b_k PASSED   [ 16%]
tests/test_api.py::test_sensor_freshness_feature_f PASSED                [ 20%]
tests/test_api.py::test_anomalies_feature_c PASSED                       [ 24%]
tests/test_api.py::test_lag_correlation_feature_d PASSED                 [ 28%]
tests/test_api.py::test_complaint_quality_filter_feature_e PASSED        [ 32%]
tests/test_api.py::test_pipeline_status_feature_g PASSED                 [ 36%]
tests/test_api.py::test_forecast_feature_h PASSED                        [ 40%]
tests/test_api.py::test_alerts_history_feature_i PASSED                  [ 44%]
tests/test_api.py::test_nearby_facilities_feature_j PASSED               [ 48%]
tests/test_api.py::test_csv_export_feature_l PASSED                      [ 52%]
tests/test_api.py::test_html_pages_feature_m_g_i_o PASSED                [ 56%]
tests/test_new_features.py::test_config_endpoints PASSED                 [ 60%]
tests/test_new_features.py::test_nearest_zone_geolocation PASSED         [ 64%]
tests/test_new_features.py::test_admin_summary PASSED                    [ 68%]
tests/test_new_features.py::test_admin_alerts_and_patch PASSED           [ 72%]
tests/test_new_features.py::test_admin_report PASSED                     [ 76%]
tests/test_new_features.py::test_complaint_submission_with_symptoms_chips PASSED [ 80%]
tests/test_services.py::test_mongodb PASSED                              [ 84%]
tests/test_services.py::test_hiveserver2 PASSED                          [ 88%]
tests/test_services.py::test_hdfs PASSED                                 [ 92%]
tests/test_services.py::test_pig PASSED                                  [ 96%]
tests/test_tn_api.py::test_tamilnadu_districts PASSED                    [100%]

============================= 25 passed in 32.58s ==============================
```
