import re

with open("/home/mithra/air-quality-ews/frontend/static/js/dashboard.js") as f:
    js_content = f.read()

with open("/home/mithra/air-quality-ews/frontend/templates/index.html") as f:
    html_content = f.read()

ids_in_js = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js_content))
missing = [elem_id for elem_id in sorted(ids_in_js) if f'id="{elem_id}"' not in html_content and f"id='{elem_id}'" not in html_content]

print(f"Total IDs in JS: {len(ids_in_js)}")
print(f"Missing IDs in HTML: {missing}")
