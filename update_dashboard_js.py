with open("/home/mithra/air-quality-ews/frontend/static/js/dashboard.js", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update TOUR_STEPS
old_tour_steps = """const TOUR_STEPS = [
    {
        target: "traffic-light-banner",
        stepText: "Step 1 of 4",
        title: "Plain Traffic-Light Banner",
        body: "Get an immediate traffic-light risk rating, plain-language advice sentence, and tap 'Use My Location' to auto-detect your neighborhood."
    },
    {
        target: "map",
        stepText: "Step 2 of 4",
        title: "Surveillance Map & TN Choropleth",
        body: "Explore real-time monitoring stations and all 30 Tamil Nadu districts. Click any district or station marker to inspect 30-day trends."
    },
    {
        target: "btn-report-symptom",
        stepText: "Step 3 of 4",
        title: "Citizen Symptom Checklist",
        body: "Tap symptom chips (cough, breathlessness, eye irritation) to alert public health officials. Submissions update the risk score directly!"
    },
    {
        target: "btn-open-explainer",
        stepText: "Step 4 of 4",
        title: "Everyday Language Guide",
        body: "Wondering how PM2.5 differs from PM10, or what a Compound Alert means? Click 'What Does This Mean?' anytime for clear explanations."
    }
];"""

new_tour_steps = """const TOUR_STEPS = [
    {
        target: "map",
        stepText: "Step 1 of 4",
        title: "🗺️ Surveillance Map & TN Choropleth",
        body: "Explore real-time monitoring stations and all 30 Tamil Nadu districts. Click any district or station marker to inspect 30-day trends and clinical directives."
    },
    {
        target: "btn-use-location",
        stepText: "Step 2 of 4",
        title: "📍 Location Auto-Detection",
        body: "Click 'My Location' anytime to calculate your distance to all monitoring stations and automatically focus on your nearest zone within 50 km."
    },
    {
        target: "btn-report-symptom",
        stepText: "Step 3 of 4",
        title: "📢 Citizen Health Reporting",
        body: "Report symptoms (persistent cough, breathlessness, eye burning) directly into MongoDB to drive the Big Data fusion risk calculation."
    },
    {
        target: "btn-share",
        stepText: "Step 4 of 4",
        title: "📤 Share Air Quality Advisory",
        body: "Share the live health risk advisory with family and neighbors on WhatsApp or copy deep-links with one tap."
    }
];"""

if old_tour_steps in code:
    code = code.replace(old_tour_steps, new_tour_steps)
    print("Updated TOUR_STEPS")

# 2. In detectUserLocation, remove updateTrafficLightBanner call
code = code.replace("updateTrafficLightBanner(nearest, minDist);", "// banner removed")
code = code.replace("updateTrafficLightBanner(match);", "// banner removed")
code = code.replace("updateTrafficLightBanner(z);", "// banner removed")
code = code.replace("updateTrafficLightBanner(zone);", "// banner removed")

# 3. Simplify updateTrafficLightBanner to a no-op
old_banner_fn = """function updateTrafficLightBanner(zone, distanceInfo = null) {"""
if old_banner_fn in code:
    # replace the entire function with a safe stub
    idx = code.find(old_banner_fn)
    end_idx = code.find("function detectUserLocation", idx)
    if idx != -1 and end_idx != -1:
        code = code[:idx] + "function updateTrafficLightBanner(zone, distanceInfo = null) { return; }\n\n" + code[end_idx:]
        print("Stubbed updateTrafficLightBanner")

# 4. Remove explainer modal functions
old_explainer = """async function loadExplainerConfig() {"""
if old_explainer in code:
    idx = code.find(old_explainer)
    end_idx = code.find("function shareCurrentZone", idx)
    if idx != -1 and end_idx != -1:
        code = code[:idx] + "function openExplainerModal(section = null) { return; }\n\n" + code[end_idx:]
        print("Removed explainer functions")

# 5. Fix share button listener
code = code.replace('const btnShare = document.getElementById("btn-share-banner");', 'const btnShare = document.getElementById("btn-share") || document.getElementById("btn-share-banner");')

# 6. Revert submitCitizenComplaint to read standard checkboxes and alert instead of confirmation modal
old_submit_start = code.find("async function submitCitizenComplaint() {")
old_confirm_end = code.find("// =============================================================================", old_submit_start + 100)

if old_submit_start != -1 and old_confirm_end != -1:
    new_submit_fn = """async function submitCitizenComplaint() {
    const zid = document.getElementById("report-zone-select").value;
    const name = (document.getElementById("report-citizen-name") ? document.getElementById("report-citizen-name").value.trim() : "");
    const desc = (document.getElementById("report-desc") ? document.getElementById("report-desc").value.trim() : "");
    const age = (document.getElementById("report-age-group") ? document.getElementById("report-age-group").value : "adult");
    const sevRadio = document.querySelector('input[name="severity"]:checked');
    const sev = sevRadio ? sevRadio.value : "moderate";

    const checkedBoxes = Array.from(document.querySelectorAll('input[name="symptoms"]:checked')).map(cb => cb.value);
    const symptoms = checkedBoxes.length > 0 ? checkedBoxes : ["cough"];

    if (!zid) {
        alert("Please select a monitored zone.");
        return;
    }
    if (!desc || desc.length < 4) {
        alert("Please provide at least 4 characters of description.");
        return;
    }

    const payload = {
        zone_id: zid,
        citizen_name: name || "Anonymous Citizen",
        symptoms: symptoms,
        severity: sev,
        age_group: age,
        description: desc
    };

    try {
        const res = await fetch("/api/complaints", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (res.status === 201) {
            alert(`Report Registered: ${json.report_id}\\n\\nYour complaint has been verified and registered with the Early-Warning Network!`);
            document.getElementById("modal-complaint").classList.remove("active");
            document.getElementById("complaint-form").reset();
            loadComplaintsSummary();
        } else {
            alert("Quality Gate Intercepted: " + (json.rejection_reason || json.message));
        }
    } catch (err) {
        alert("Connection error while submitting report: " + err);
    }
}
"""
    code = code[:old_submit_start] + new_submit_fn + "\n" + code[old_confirm_end:]
    print("Reverted submitCitizenComplaint to standard checkboxes and alert")

with open("/home/mithra/air-quality-ews/frontend/static/js/dashboard.js", "w", encoding="utf-8") as f:
    f.write(code)

print("SUCCESS: dashboard.js updated")
