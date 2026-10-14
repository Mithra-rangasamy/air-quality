with open("/home/mithra/air-quality-ews/prev_working_tn_index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Add the 3 buttons into the nav-actions right before btn-trigger-pipeline
buttons = '''
            <button id="btn-use-location" class="btn btn-secondary" title="Auto-detect nearest zone via GPS">
                📍 My Location
            </button>

            <button id="btn-share" class="btn btn-secondary" title="Share current zone air quality advisory">
                📤 Share
            </button>

            <button id="btn-start-tour" class="btn btn-secondary" style="border-color:#38bdf8; color:#38bdf8;" title="Take a 4-step interactive guided tour">
                🧭 Take Tour
            </button>
'''

target_btn = '<button id="btn-trigger-pipeline"'
if target_btn in content:
    content = content.replace(target_btn, buttons + '\n            ' + target_btn)

# Add Tour Popover and Toast Notice before </body>
extra_elements = '''
    <!-- Guided Tour Popover -->
    <div id="tour-popover" class="tour-popover" style="display:none; position:absolute; z-index:9999; background:#1e293b; border:2px solid #38bdf8; border-radius:8px; padding:16px; width:300px; box-shadow:0 10px 25px rgba(0,0,0,0.6); color:#f8fafc;">
        <div class="tour-step-counter" id="tour-step" style="font-size:10px; font-weight:800; color:#38bdf8; text-transform:uppercase; margin-bottom:4px;">Step 1 of 4</div>
        <div class="tour-popover-title" id="tour-title" style="font-size:14px; font-weight:700; color:#fff; margin-bottom:6px;">Geographic Surveillance Map</div>
        <div class="tour-popover-body" id="tour-body" style="font-size:12px; color:#cbd5e1; line-height:1.5; margin-bottom:12px;">
            Interactive Leaflet map displaying 25 monitored urban zones and Tamil Nadu 30-district choropleth with real-time risk tiers.
        </div>
        <div class="tour-popover-actions" style="display:flex; justify-content:space-between; align-items:center;">
            <button id="tour-btn-skip" class="btn btn-sm btn-outline" style="font-size:11px; padding:3px 8px;">Skip</button>
            <div style="display:flex; gap:6px;">
                <button id="tour-btn-back" class="btn btn-sm btn-secondary" style="display:none; font-size:11px; padding:3px 8px;">Back</button>
                <button id="tour-btn-next" class="btn btn-sm btn-primary" style="font-size:11px; padding:3px 8px;">Next</button>
            </div>
        </div>
    </div>

    <!-- Small Toast Notification -->
    <div id="toast-notice" class="toast-notice" style="display:none; position:fixed; bottom:24px; right:24px; z-index:99999; background:#0284c7; color:#fff; padding:10px 18px; border-radius:6px; font-size:13px; font-weight:600; box-shadow:0 8px 20px rgba(0,0,0,0.5);">
        Notice
    </div>
'''

content = content.replace('</body>', extra_elements + '\n</body>')

with open("/home/mithra/air-quality-ews/frontend/templates/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: index.html generated from prev_working_tn_index.html with location, share, and tour")
