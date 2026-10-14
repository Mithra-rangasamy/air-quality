from pyhive import hive

try:
    conn = hive.Connection(host='localhost', port=10000, username='mithra')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM zone_risk_score')
    res = cursor.fetchall()
    print("SUCCESS: PyHive fetched:", res)
except Exception as e:
    print("ERROR connecting to Hive:", e)
