# DigitalOcean Deployment Guide

**Target**: LCA Dashboard Backend  
**Platform**: DigitalOcean App Platform (Apps)  
**Region**: Frankfurt (fra) — closest to RWTH Aachen  
**Cost**: ~$5/month (vs. Render free tier with 30s cold starts)  
**Frontend**: GitHub Pages at `https://omer3kale.github.io/ltt-cloud/`  

---

## Why DigitalOcean Over Render?

| Factor | Render Free | DigitalOcean Basic ($5/mo) |
|---|---|---|
| **Cold starts** | ~30s after 15min idle | ✅ None (always-on) |
| **Filesystem** | Ephemeral (reset on deploy) | ✅ Persistent SQLite |
| **Region** | Frankfurt ✅ | Frankfurt ✅ |
| **Auto-deploy** | Push to GitHub ✅ | Push to GitHub ✅ |
| **Health checks** | Manual | ✅ Automatic (30s interval) |
| **Experiments survive restart** | ❌ Lost | ✅ Saved in SQLite |

---

## Prerequisites

- GitHub account with `omer3kale/ltt-cloud` access
- DigitalOcean account (https://www.digitalocean.com) — $5/month billing
- `.do/app.yaml` committed and pushed to main branch ✅

---

## Part 1: Deploy Backend on DigitalOcean

### Option A: DigitalOcean UI (Easiest)

**Step 1: Log in to DigitalOcean**
1. Go to https://cloud.digitalocean.com
2. Click **Apps** (left sidebar)
3. Click **Create App**

**Step 2: Connect GitHub Repository**
1. Select **GitHub** as source
2. Authorize DigitalOcean access to your GitHub account
3. Search for and select `omer3kale/ltt-cloud`
4. Select branch: **main**
5. Click **Next**

**Step 3: Review App Spec**
1. DigitalOcean auto-reads `.do/app.yaml` from the repo
2. Verify settings:
   - **Name**: lca-backend
   - **Region**: fra (Frankfurt)
   - **Service**: api
   - **Run command**: `uvicorn mock_api:app --host 0.0.0.0 --port $PORT`
   - **Build command**: `pip install -r requirements.txt`
3. Click **Next**

**Step 4: Configure & Deploy**
1. Set resource tier: **Basic** (0.5GB RAM, 1 vCPU) — sufficient for MVP
2. Enable **Auto-deploy on push**: ✅ (checked)
3. Click **Create Resource**
4. Click **Deploy** to start first build

**Step 5: Monitor Build**
- Watch "Builds" tab for progress (5–10 min on first build)
- Once green ✅, app is live
- Copy backend URL: `https://lca-backend-xxxx.ondigitalocean.app`

---

### Option B: DigitalOcean CLI (doctl)

If you prefer terminal automation:

```bash
# Install doctl (macOS)
brew install doctl

# Authenticate
doctl auth init
# Paste your DigitalOcean API token when prompted

# Deploy from spec
cd /Users/sophiebeier/ltt-cloud
doctl apps create --spec .do/app.yaml

# Watch logs
doctl apps logs <APP_ID> --type run --follow

# Get app URL
doctl apps list
# Copy the URL (https://lca-backend-xxxx.ondigitalocean.app)
```

---

## Part 2: Update Frontend to Use DigitalOcean Backend

### Step 6: Update API_BASE_URL in app.js

Once DigitalOcean deployment is complete and you have the URL (e.g., `https://lca-backend-abc123.ondigitalocean.app`):

**File**: `public/app.js` (line 1–5)

Replace:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://lca-backend.onrender.com';  // OLD: Render placeholder
```

With:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://lca-backend-abc123.ondigitalocean.app';  // NEW: DigitalOcean URL
```

**Then commit and push:**
```bash
cd /Users/sophiebeier/ltt-cloud
git add public/app.js
git commit -m "chore: update API_BASE_URL to DigitalOcean backend"
git push origin main
```

GitHub Pages auto-rebuilds ~ immediately.

---

## Part 3: Update CORS in Backend

### Step 7: Verify GitHub Pages in CORS Allow-List

**File**: `mock_api.py` (lines ~160–170, the CORSMiddleware config)

Verify GitHub Pages domain is in `allow_origins`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://localhost:3000",
        "https://omer3kale.github.io",
        "https://omer3kale.github.io/ltt-cloud",  # ← Make sure this is present
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If missing, add it and push:
```bash
git add mock_api.py
git commit -m "chore: ensure GitHub Pages domain in CORS allow_origins"
git push origin main
```

DigitalOcean auto-redeploys on push.

---

## Part 4: End-to-End Testing

### Step 8: Test Local Development (Pre-Production)

**Terminal 1** (Backend on port 8000):
```bash
cd /Users/sophiebeier/ltt-cloud
python3 mock_api.py
# Output: Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2** (Frontend on port 8001):
```bash
cd /Users/sophiebeier/ltt-cloud
python3 -m http.server 8001 --directory public
# Output: Serving HTTP on 0.0.0.0:8001
```

**Browser Test**:
1. Open: http://localhost:8001
2. Fill form (DAC, today, EU mix)
3. Click "Run Experiment"
4. Expect:
   - Status: "Connecting to backend..." → "Fetching results..." → (hidden)
   - Results display: three tiers + SOS bar + contributions chart ✅

### Step 9: Test GitHub Pages Live Endpoint

**Browser Test**:
1. Open: https://omer3kale.github.io/ltt-cloud/
2. Fill form (BEV, future_average, pledges)
3. Click "Run Experiment"
4. Expect:
   - Status messages appear
   - Results from **DigitalOcean backend** (not localhost)
   - No console errors
   - Doughnut chart renders (local Chart.js) ✅

### Step 10: Backend Health Check

```bash
# From your local machine
curl https://lca-backend-abc123.ondigitalocean.app/
# Expected response:
# {"message":"LTT LCA Experiment API (Brightway-ready MVP)","timestamp":"2026-03-28T..."}
```

---

## Monitoring & Troubleshooting

### View Logs (DigitalOcean UI)

1. Go to **Apps** → **lca-backend** → **Logs**
2. Select **Component**: api
3. Select **Type**: run (application output) or build (deployment output)

### View Logs (CLI)

```bash
doctl apps logs <APP_ID> --type run --follow
```

### Common Issues

| Issue | Cause | Fix |
|---|---|---|
| **502 Bad Gateway** | Backend crashed or didn't start | Check logs for error; redeploy |
| **CORS errors** | Frontend domain not in allow_origins | Add domain, push, wait for redeploy |
| **404 on assets** | Asset paths are absolute (e.g., `/style.css`) | Verify paths are relative (`./style.css`) |
| **Slow first request** | Health check not passing | Check logs; verify SQLite init |
| **Experiments lost after restart** | SQLite not persisted | Verify `experiments.db` is in filesystem |

### Redeploy Manually

No need — DigitalOcean auto-deploys on `git push origin main`.

But if you want to force redeploy:
1. UI: **Apps** → **lca-backend** → **Actions** → **Restart App**
2. CLI: `doctl apps update <APP_ID>`

---

## Custom Domain (Optional)

To use a custom domain like `lca-api.ltt.rwth-aachen.de`:

1. Verify you control the domain DNS
2. In DigitalOcean UI: **Apps** → **lca-backend** → **Settings** → **Domains**
3. Add custom domain
4. Update DNS records as shown in DigitalOcean console
5. Wait 5–15 min for certificate issuance
6. Update `app.js` to use custom domain URL

---

## Cost Estimate

| Service | Cost | Notes |
|---|---|---|
| **DigitalOcean App** | ~$5/month | 0.5GB, 1 vCPU, auto-scaling disabled |
| **GitHub Pages** | Free | Unlimited static hosting |
| **SQLite** | Free | Local file storage on app filesystem |
| **Total** | **~$5/month** | (vs. Render free + cold starts) |

---

## 10-Step Master Sequence (All Fixes + DO Deploy)

```markdown
1. ✅ Apply Issues 4–10 code blocks (already done: commit 68088fd)
2. ✅ Create .do/app.yaml and push (done: commit f078864)
3. ✅ Verify .do/app.yaml in GitHub (check main branch)
4. → Deploy on DigitalOcean via UI or doctl
5. → Wait for build to complete (~5–10 min)
6. → Copy backend URL (https://lca-backend-xxxx.ondigitalocean.app)
7. → Update API_BASE_URL in app.js, commit, push
8. → Test locally (localhost:8001 → localhost:8000)
9. → Test live (GitHub Pages → DigitalOcean backend)
10. → Verify end-to-end (DAC + BEV experiments work)
11. → Share URLs with colleagues:
    - Frontend: https://omer3kale.github.io/ltt-cloud/
    - Backend: https://lca-backend-xxxx.ondigitalocean.app/
12. → Mark all audit issues 1–10 as ✅ CLOSED
```

---

## Success Criteria

- ✅ Backend running on DigitalOcean (no cold starts)
- ✅ Frontend on GitHub Pages (all assets load)
- ✅ POST /experiments/run returns {"id": "uuid"}
- ✅ GET /experiments/{id}/result returns full result
- ✅ SQLite persists experiments across app restart
- ✅ Rate limiting active (10/minute per IP)
- ✅ Status messages show during experiment run
- ✅ BEV activity code populated in response
- ✅ Chart.js renders offline (local file)
- ✅ Doughnut chart appears in results

---

## Timeline

| Step | Duration | Notes |
|---|---|---|
| 1. Deploy on DO | 5–10 min | First build includes dependencies |
| 2. Update app.js | 2 min | Next push auto-triggers GitHub Pages build |
| 3. Test locally | 5 min | Verify backend + frontend on localhost |
| 4. Test live | 5 min | Verify GitHub Pages → DigitalOcean |
| **Total** | **15–20 min** | Ready for colleague onboarding |

---

## Next Steps (Phase 2)

Once backend is live on DigitalOcean:

1. **Brightway Cloud Integration** (Week 1):
   - Request "LCAEPE" shared project credentials
   - Install `brightway-cloud` client library
   - Replace mock formulas with real LCA data

2. **Colleague Onboarding** (Week 2):
   - Share GitHub Pages + DigitalOcean URLs
   - Document API endpoints
   - Create Jupyter notebook templates

3. **Production Hardening** (Week 3+):
   - Add Managed PostgreSQL for true persistence
   - Set up CI/CD monitoring via GitHub Actions
   - Configure DigitalOcean monitoring alerts

---

**Deployment Date**: 28 March 2026  
**Status**: Ready for DigitalOcean deployment  
**Support**: Check logs via DigitalOcean UI or `doctl apps logs`
