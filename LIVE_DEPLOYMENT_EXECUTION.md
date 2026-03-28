# 🚀 Live Deployment Execution (DO + GitHub Pages)

**Status**: Backend & frontend ready to go live  
**Time to deployment**: ~20 minutes  
**Date**: 28 March 2026

---

## Phase 1: Deploy Backend on DigitalOcean (15 min)

### Step 1A: Via DigitalOcean UI (Recommended for First Time)

```
1. Open: https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Select GitHub → Authorize → element-xo/ltt-cloud → main
4. Wait for auto-detect... DigitalOcean should find .do/app.yaml
5. Click "Use detected config" or confirm:
   - Name: lca-backend
   - Region: fra (Frankfurt)
   - Run: uvicorn mock_api:app --host 0.0.0.0 --port $PORT
   - Build: pip install -r requirements.txt
6. Click "Create Resource"
7. Click "Deploy" and wait for status: Active ✅
8. Once active, click to open app
9. Copy the Live Domain (e.g., https://lca-backend-abc123.ondigitalocean.app)
```

**You will see**:
- Build running (~3-5 min on first deploy)
- Status: "In Progress" → "Active"
- Green checkmark when ready
- Live URL in the banner

**Proceed to Step 2 once status is Active**

---

### Step 1B: Via CLI (Alternative)

If you prefer terminal:

```bash
# One-time: authenticate with DO
doctl auth init
# Paste your DigitalOcean API token when prompted

# Deploy the app
cd /Users/sophiebeier/ltt-cloud
doctl apps create --spec .do/app.yaml

# Watch deploy progress
doctl apps logs <APP_ID> --type build --follow

# Get the Live URL
doctl apps get <APP_ID> --format LiveURL
# Output: https://lca-backend-xxxx.ondigitalocean.app
```

**Save the Live URL** — you'll need it in Step 2.

---

## Phase 2: Wire Frontend to DigitalOcean (5 min)

### Step 2: Update API_BASE_URL in app.js

Now that you have your DigitalOcean URL (from Step 1):

```bash
# Open the file
nano public/app.js

# Or use sed (replace xxxx with your actual App ID)
sed -i '' "s|lca-backend-xxxx|lca-backend-YOUR_APP_ID|g" public/app.js

# Example: if your DO URL is https://lca-backend-abc123.ondigitalocean.app
# Then: sed -i '' 's|lca-backend-xxxx|lca-backend-abc123|g' public/app.js
```

**What it looks like after update**:
```javascript
return 'https://lca-backend-abc123.ondigitalocean.app';  // Your actual URL
```

**Verify the change**:
```bash
head -15 public/app.js | grep "lca-backend"
# Should show: https://lca-backend-abc123.ondigitalocean.app
```

**Commit and push**:
```bash
cd /Users/sophiebeier/ltt-cloud
git add public/app.js
git commit -m "chore: wire frontend to DigitalOcean backend (https://lca-backend-abc123.ondigitalocean.app)"
git push origin main
```

**GitHub Pages rebuilds automatically** (takes ~30-60 seconds).

---

## Phase 3: Enable GitHub Pages (5 min)

### Step 3: Enable Pages for GitHub Repository

```
1. Open your GitHub repo: https://github.com/element-xo/ltt-cloud
   (or: https://github.com/omer3kale/ltt-cloud if that's your username)
2. Go to Settings (tab at top)
3. Left sidebar: Click "Pages"
4. Under "Source":
   - Select: "Deploy from a branch"
   - Branch: main
   - Folder: /public
5. Click "Save"
6. Wait 1-2 minutes for the build
```

**GitHub will show**:
- "Your site is being built from the main branch..."
- Once done: "Your site is live at https://[username].github.io/ltt-cloud/"

**Copy the exact URL** provided by GitHub.

---

## Phase 4: End-to-End Live Testing (5 min)

### Step 4: Open the Dashboard

```text
Open: https://omer3kale.github.io/ltt-cloud/
(or: https://element-xo.github.io/ltt-cloud/ if that's your GitHub Pages URL)
```

### Step 5: Run a Live Experiment

**Test case 1: DAC (simplest)**
```
Scenario: Select fields
- Functional Unit: 1 kg Direct Air Capture
- Tech: Today
- Sys: Current Policy
- Electricity: Renewable
- DAC Efficiency: 75 %
- Transport: 300 km
- Temp: 800 °C

Then: Click "Run Experiment"
```

**Expected results** (streaming):
1. Status text: "Connecting to backend (cold start may take ~30s)..."
2. Status text: "Fetching results..."
3. Status text: (hidden)
4. **Tier 1**: Climate: ~6 kg CO₂-eq, Share of SOS: ~0.01 (SAFE) ✅
5. **Tier 2**: Biosphere & Freshwater tables appear
6. **Tier 3**: Land & Biogeochemical (collapsed)
7. **Metadata**: Experiment ID, timestamp, Brightway project
8. **Contributions**: Doughnut chart (Energy, Transport, Reactor Heat)

**Console check** (DevTools → Console):
- No red CORS errors ✅
- No 404s for assets ✅
- Network tab shows: `lca-backend-xxxx.ondigitalocean.app` requests (not localhost) ✅

### Step 6: Run a Live Experiment (BEV)

**Test case 2: BEV (to verify persistence & lifecycle)**
```
Scenario: Select fields
- Functional Unit: 100 km BEV Transport
- Tech: Future Average
- Sys: Pledges
- Electricity: EU Mix
- Vehicle Lifetime: 200,000 km
- Production Emissions: 15,000 kg
- Disposal: 500 kg

Then: Click "Run Experiment"
```

**Expected results**:
1. Same status flow
2. Climate impact: ~6 kg CO₂-eq (similar to DAC due to EU mix)
3. **Contributions differ**: Production, Use-Phase, Disposal (not Energy, Transport, Reactor Heat)
4. All tiers render
5. **Database check**: Experiment ID should still be retrievable after restart

---

## Validation Checklist

Run this checklist to confirm everything is working:

### Frontend (GitHub Pages)

- [ ] Open https://omer3kale.github.io/ltt-cloud/
- [ ] All assets load (no 404s in DevTools)
- [ ] Form renders with all fields
- [ ] Scenario cards exist (Clean Future, Today's Baseline, BEV)
- [ ] BEV-specific fields toggle when FU=BEV

### Backend (DigitalOcean)

```bash
# Test 1: Health check
curl https://lca-backend-xxxx.ondigitalocean.app/
# Expected: {"message":"LTT LCA Experiment API...","timestamp":"..."}

# Test 2: Create experiment
curl -X POST https://lca-backend-xxxx.ondigitalocean.app/experiments/run \
  -H "Content-Type: application/json" \
  -d '{
    "functional_unit":"1_kg_dac",
    "tech_scenario":"today",
    "sys_scenario":"current_policy",
    "variables":{
      "electricity_mix":"renewable",
      "dac_efficiency":75.0,
      "transport_distance_km":300.0,
      "reactor_temperature_c":800.0,
      "system_boundary":"cradle_to_grave"
    }
  }'
# Expected: {"id":"<uuid>"}

# Test 3: Fetch result
curl https://lca-backend-xxxx.ondigitalocean.app/experiments/<uuid>/result
# Expected: ExperimentResultResponse with impacts, contributions, interpretation

# Test 4: Rate limiting (fire 15 rapid requests, 11+ should get 429)
for i in {1..15}; do curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST https://lca-backend-xxxx.ondigitalocean.app/experiments/run \
  -H "Content-Type: application/json" \
  -d '{"functional_unit":"1_kg_dac","tech_scenario":"today","sys_scenario":"current_policy","variables":{"electricity_mix":"renewable","dac_efficiency":75,"transport_distance_km":300,"reactor_temperature_c":800,"system_boundary":"cradle_to_gate"}}'; done
# Expected: 200 200 200 ... 200 (10x) 429 429 429 429 429
```

- [ ] Health check returns 200
- [ ] POST /experiments/run returns {"id":"..."}
- [ ] GET /experiments/{id}/result returns 200 with full response
- [ ] Rate limiting active (11+ requests in 1 min get 429)

### Integration (Pages → Backend)

- [ ] Click "Run Experiment" on live GitHub Pages
- [ ] Status messages appear
- [ ] Results render (all 3 tiers visible)
- [ ] Doughnut chart renders (from local Chart.js)
- [ ] DevTools console has no red errors
- [ ] DevTools Network shows requests to DigitalOcean URL (not localhost)

### Data Quality

- [ ] Climate impact ~6 kg CO₂-eq (realistic)
- [ ] Share of SOS ~0.01 (realistic, SAFE)
- [ ] bw_activity_code populated (not null)
- [ ] Contributions sum to climate impact
- [ ] Interpretation array has entries for all 5 categories

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **502 Bad Gateway** | Backend not starting | Check DO logs; verify `requirements.txt` and `mock_api.py` are correct |
| **CORS error in console** | GitHub Pages domain not in allow_origins | Verify `mock_api.py` has `https://omer3kale.github.io` in allow_origins |
| **404 on style.css or app.js** | Asset paths are absolute (not relative) | Verify `public/index.html` uses `href="./style.css"` not `/style.css` |
| **Blank page on GitHub Pages** | Pages not enabled or wrong branch/folder | Go to Settings → Pages, verify "Deploy from a branch: main, /public" |
| **"Cannot reach backend" error** | API_BASE_URL has wrong Domain | Update with actual DO URL (e.g., `lca-backend-abc123.ondigitalocean.app`) |
| **Slow first request (30s+)** | Normal on first request (health check starting app) | Subsequent requests should be <1s |
| **No data in results** | Backend didn't compute impacts | Check DO logs for computation errors |

---

## Success Criteria (All = ✅ Live)

```markdown
✅ Backend deployed on DigitalOcean (URL: https://lca-backend-xxxx.ondigitalocean.app)
✅ Frontend deployed on GitHub Pages (URL: https://omer3kale.github.io/ltt-cloud/)
✅ POST /experiments/run returns experiment ID
✅ GET /experiments/{id}/result returns full result with 5 impacts
✅ Pages → Backend communication works (no CORS errors)
✅ Status messages display during experiment run
✅ Three-tier UI renders (climate KPI, tables, contributions)
✅ Doughnut chart renders (local Chart.js, not CDN)
✅ Rate limiting active (429 on >10 req/min)
✅ SQLite persistence works (experiments survive restart)
✅ All audit issues 4–10 verified
```

---

## Next Steps (After Going Live)

1. Share URLs with colleagues:
   ```
   Frontend: https://omer3kale.github.io/ltt-cloud/
   Backend API: https://lca-backend-xxxx.ondigitalocean.app/
   API Docs: https://lca-backend-xxxx.ondigitalocean.app/docs (ReDoc)
   ```

2. Keep monitoring:
   - DigitalOcean admin panel for logs
   - GitHub Pages for any build failures
   - Check experiments table (`experiments.db`) for data persistence

3. Next Phase (Week 1):
   - Brightway Cloud integration
   - Real LCA data from ecoinvent
   - Colleague onboarding with Jupyter notebooks

---

**Deployment Status**: READY TO GO LIVE 🚀  
**Estimated Time**: 20 minutes (mostly waiting for builds)  
**Risk Level**: Low (zero downtime, persisted data, auto-rollback if needed)

