with open("/home/mithra/air-quality-ews/backend/app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Remove admin/report route
target_admin_report = """@app.route("/admin/report")
@admin_required
def admin_report_view():
    \"\"\"Feature 10: Printable Daily Situation Report Page.\"\"\"
    return render_template("report.html")"""

if target_admin_report in code:
    code = code.replace(target_admin_report, "")
    print("Removed /admin/report route")

# 2. Remove /api/config/advice-simple and /api/config/explainer
target_advice_simple = """@app.route("/api/config/advice-simple", methods=["GET"])
def get_advice_simple():
    \"\"\"Feature 1: Serves simple one-sentence advice config.\"\"\"
    cfg_file = os.path.join(BASE_DIR, "config", "advice_simple.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})"""

if target_advice_simple in code:
    code = code.replace(target_advice_simple, "")
    print("Removed /api/config/advice-simple route")

target_explainer = """@app.route("/api/config/explainer", methods=["GET"])
def get_explainer():
    \"\"\"Feature 5: Serves everyday language explainer content.\"\"\"
    cfg_file = os.path.join(BASE_DIR, "config", "explainer.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})"""

if target_explainer in code:
    code = code.replace(target_explainer, "")
    print("Removed /api/config/explainer route")

# 3. Remove /api/admin/summary, /api/admin/alerts, /api/admin/report
# Find from @app.route("/api/admin/summary" up to "# Existing Helper Routes"
summary_start = code.find('@app.route("/api/admin/summary"')
helper_start = code.find('# Existing Helper Routes')

if summary_start != -1 and helper_start != -1:
    code = code[:summary_start] + code[helper_start:]
    print("Removed admin summary, alerts actions, and report data routes")
else:
    print(f"Warning: summary_start={summary_start}, helper_start={helper_start}")

with open("/home/mithra/air-quality-ews/backend/app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("SUCCESS: app.py cleaned")
