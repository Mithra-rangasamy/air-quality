-- ==============================================================================
-- CIT 21MDS56: Air Quality & Public Health Early-Warning System
-- hive/queries.hql - Analytical Trend & Comparison Queries for Lab Record
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: 7-Day Moving Average AQI per City
-- Demonstrates window functions in HiveQL over partitioned time-series
-- ------------------------------------------------------------------------------
SELECT 
    city,
    `date`,
    ROUND(AVG(daily_avg_aqi) OVER (
        PARTITION BY city 
        ORDER BY `date` 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS aqi_7day_moving_avg
FROM (
    SELECT city, `date`, AVG(aqi) as daily_avg_aqi
    FROM aqi_readings
    GROUP BY city, `date`
) daily_city
ORDER BY city, `date` DESC
LIMIT 20;

-- ------------------------------------------------------------------------------
-- QUERY 2: Worst Pollution Zones This Month
-- Identifies persistent hot-spots across all metropolitan zones
-- ------------------------------------------------------------------------------
SELECT 
    city,
    zone_id,
    zone_name,
    ROUND(AVG(aqi), 1) AS monthly_avg_aqi,
    MAX(aqi) AS peak_aqi,
    ROUND(AVG(pm25), 1) AS avg_pm25,
    ROUND(AVG(pm10), 1) AS avg_pm10
FROM aqi_readings
GROUP BY city, zone_id, zone_name
ORDER BY monthly_avg_aqi DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- QUERY 3: Hour-of-Day Pollution Pattern
-- Uncovers diurnal peaks linked to rush-hour vehicular emission spikes
-- ------------------------------------------------------------------------------
SELECT 
    SUBSTR(ts, 12, 2) AS hour_of_day,
    ROUND(AVG(aqi), 1) AS avg_aqi,
    ROUND(AVG(pm25), 1) AS avg_pm25,
    ROUND(AVG(no2), 1) AS avg_no2
FROM aqi_readings
GROUP BY SUBSTR(ts, 12, 2)
ORDER BY CAST(hour_of_day AS INT) ASC;

-- ------------------------------------------------------------------------------
-- QUERY 4: City-to-City Air Quality Comparison
-- Comprehensive benchmark across Coimbatore, Chennai, Bengaluru, Delhi, Mumbai
-- ------------------------------------------------------------------------------
SELECT 
    city,
    COUNT(DISTINCT zone_id) AS total_monitored_zones,
    ROUND(AVG(aqi), 1) AS avg_city_aqi,
    MIN(aqi) AS cleanest_hour_aqi,
    MAX(aqi) AS worst_hour_aqi,
    ROUND(AVG(pm25), 1) AS avg_pm25,
    ROUND(AVG(pm10), 1) AS avg_pm10
FROM aqi_readings
GROUP BY city
ORDER BY avg_city_aqi DESC;
