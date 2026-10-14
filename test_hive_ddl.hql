DROP TABLE IF EXISTS test_aqi;

CREATE EXTERNAL TABLE test_aqi (
    record_id STRING,
    city_name STRING,
    zone_id STRING,
    zone_name STRING,
    ts STRING,
    aqi INT,
    pm25 DOUBLE,
    pm10 DOUBLE,
    no2 DOUBLE,
    so2 DOUBLE,
    co DOUBLE,
    o3 DOUBLE
)
PARTITIONED BY (city STRING, `date` STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/raw/aqi';

MSCK REPAIR TABLE test_aqi;

SELECT city, `date`, zone_id, aqi FROM test_aqi LIMIT 5;

SELECT count(*) FROM test_aqi;

DROP TABLE test_aqi;
