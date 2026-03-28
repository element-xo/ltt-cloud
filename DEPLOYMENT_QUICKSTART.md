# 🚀 Quick-Start Deployment Guide

**Audience**: Run these commands sequentially to deploy LCA Dashboard to GitHub Pages + Render  
**Time**: ~15 minutes  
**Prerequisites**: GitHub account, Render.com account (free tier)

---

## Phase 1: Push Frontend to GitHub (5 min)

### Step 1–3: Commit & Push
```bash
cd /Users/sophiebeier/ltt-cloud

# Stage files
git add public/index.html public/style.css public/app.js mock_api.py

# Commit with message
git commit -m "feat: deploy three-tier LCA dashboard to GitHub Pages

- Add environment-aware API endpoint (localhost vs Render)
- Update CORS for GitHub Pages domain
- Asset paths: relative (GitHub-compatible)

Fixes: AESA allocation, BEV lifecycle, contributions scaling
Validated: AUDIT_RESULTS.md"

# Push to GitHub
git push origin main

# Verify: Check https://github.com/omer3kale/ltt-cloud/tree/main/public
# Should show 3 new files
```

✅ **Check**: Visit [GitHub repo](https://github.com/omer3kale/ltt-cloud) → `/public` folder → 3 files present

---

## Phase 2: Enable GitHub Pages (2 min)

### Step 4–5: GitHub UI Setup
1. Go to [Repo Settings](https://github.com/omer3kale/ltt-cloud/settings)
2. Left sidebar → **Pages**
3. Source: `Deploy from a branch`
4. Branch: `main`, folder: `/ (root)` **← IMPORTANT: GitHub serves from `/public` subfolder automatically**
5. Save → Wait for green checkmark in **Actions** tab

✅ **Check**: Visit https://omer3kale.github.io/ltt-cloud/ → Form loads, no 404s

---

## Phase 3: Create Render Backend (10 min)

### Step 6–7: Render.com Web Service Setup
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. **Connect your repository**:
   - GitHub: `omer3kale/ltt-cloud`
   - Authorize if prompted
4. **Configure service**:
   - **Name**: `lca-backend` (or similar)
   - **Root Directory**: `/` (empty)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn mock_api:app --host 0.0.0.0 --port $PORT`
5. **Environment**:
   - Add: `PYTHONUNBUFFERED` = `true`
6. **Plan**: Free tier (OK for development)
7. **Region**: `Frankfurt` (closest to Aachen)
8. Click **Create Web Service**

Render starts deploying (watch logs for ~2–5 minutes)

✅ **When complete**: Note the URL (e.g., `https://lca-backend-abc123.onrender.com`)

### Step 8: Update app.js with Render URL

Once Render URL is available, update `public/app.js`:

```javascript
// Line 2: Replace 'lca-backend.onrender.com' with your actual URL
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://lca-backend-abc123.onrender.com';  // ← Your Render URL
```

Then push:
```bash
git add public/app.js
git commit -m "chore: update Render backend URL"
git push origin main
```

✅ **Check**: GitHub Pages auto-rebuilds (check Actions tab)

---

## Phase 4: End-to-End Testing (3 min)

### Step 9–11: Local Pre-Production Test

**Terminal 1** (Backend):
```bash
cd /Users/sophiebeier/ltt-cloud
python3 mock_api.py
# Should show: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2** (Frontend):
```bash
cd /Users/sophiebeier/ltt-cloud
python3 -m http.server 8001 --directory public
# Should show: Serving HTTP on 0.0.0.0:8001
```

**Browser**:
- Open: http://localhost:8001
- Fill form → Click "Run Experiment"
- ✅ Should see three-tier results (climate KPI, impacts table, contributions chart)

### Step 12: Test GitHub Pages Live Endpoint

**Browser**:
- Open: https://omer3kale.github.io/ltt-cloud/
- Fill form → Click "Run Experiment"
- ✅ Should see three-tier results from **Render backend** (not localhost)
- ✅ No console errors; CORS working

### Step 13: Verify Render Backend Health

```bash
curl https://lca-backend-abc123.onrender.com/
# Expected response:
# {"message":"LTT LCA Experiment API...","timestamp":"2026-03-28T..."}
```

---

## ✅ Deployment Complete!

| Endpoint | URL | Status |
|----------|-----|--------|
| **Frontend** | https://omer3kale.github.io/ltt-cloud/ | ✅ Live |
| **Backend** | https://lca-backend-abc123.onrender.com | ✅ Live |
| **API Health** | `curl` to `/` endpoint | ✅ Running |

---

## Troubleshooting

### "404 Not Found" on GitHub Pages
- **Cause**: Asset paths are absolute (e.g., `/style.css`)
- **Fix**: Verify `public/index.html` has `href="style.css"` (not `/style.css`)
```bash
grep "href=" public/index.html | head -2
```

### "CORS error" in browser console
- **Cause**: Frontend domain not in `mock_api.py` allow_origins
- **Fix**: Update `mock_api.py`, commit, push (Render auto-redeploys)

### Render backend returns 503 "Service Unavailable"
- **Cause**: Still building or cold start
- **Fix**: Wait 1–2 minutes; refresh page
- **Prevention**: Add monitoring alert

### Form submission hangs or times out
- **Cause**: Render free tier cold start (first request = 20–30 sec)
- **Fix**: Inform users; consider upgrading plan

---

## What's Next?

Once deployed, proceed to Phase 1 (Week 1):

1. [ ] **Brighway Cloud onboarding**: Email Brightway team for shared project credentials
2. [ ] **Install brightway-cloud**: `pip install brightway-cloud`
3. [ ] **Implement real LCA**: Replace `mock_api.py` with live Brightway calculations
4. [ ] **Test against ecoinvent-3.10**: Validate 5 impacts match real data
5. [ ] **Share with colleagues**: Send GitHub Pages URL + API docs

---

**Deployment Date**: 28 March 2026  
**Estimated Time**: 15 minutes  
**Support**: Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed steps
