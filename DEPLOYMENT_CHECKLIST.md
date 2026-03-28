# Deployment Checklist: LCA Dashboard

**Status**: Ready to Deploy  
**GitHub Repo**: omer3kale/ltt-cloud  
**Frontend URL**: https://omer3kale.github.io/ltt-cloud/  
**Backend Region**: Frankfurt (Render)  

---

## Pre-Deployment Verification ✅

| Item | Status | Details |
|------|--------|---------|
| Asset paths (relative) | ✅ OK | `href="style.css"`, `src="app.js"` (no leading `/`) |
| Backend running | ✅ OK | Port 8000, PID 33229 |
| Frontend files exist | ✅ OK | index.html, style.css, app.js in `/public` |
| Pydantic validation | ✅ OK | CORS enabled, 5 PB categories working |
| AUDIT_RESULTS.md | ✅ OK | All 3 blockers fixed |

---

## 13-Step Deployment Sequence

### **Phase 1: Push Frontend to GitHub (Steps 1–3)**

**Step 1: Stage local files**
```bash
cd /Users/sophiebeier/ltt-cloud
git add public/index.html public/style.css public/app.js
git status  # Verify 3 files staged
```

**Step 2: Commit**
```bash
git commit -m "feat: add three-tier LCA dashboard frontend

- Tier 1: Climate KPI with SOS bar (green/yellow/red)
- Tier 2: Biosphere + freshwater compact table
- Tier 3: Land + biogeochemical collapsible section
- Scenario cards: Clean Future, Today's Baseline, BEV Transport
- Asset paths: relative (GitHub Pages compatible)
"
```

**Step 3: Push to main**
```bash
git push origin main
```

✅ **Verification**: Check [omer3kale/ltt-cloud/tree/main/public](https://github.com/omer3kale/ltt-cloud/tree/main/public) shows 3 new files

---

### **Phase 2: Enable GitHub Pages (Steps 4–5)**

**Step 4: Go to repo Settings → Pages**
- Source: Deploy from a branch
- Branch: `main` / `(root)` folder (NOT `/public`)
- ⚠️ NOTE: GitHub automatically serves from `/public` folder if it exists

**Step 5: Wait for deployment**
- GitHub will build & deploy automatically
- Watch for green checkmark in "Actions" tab
- Site goes live at: `https://omer3kale.github.io/ltt-cloud/`

✅ **Verification**: Visit https://omer3kale.github.io/ltt-cloud/ → Form renders, no 404s

---

### **Phase 3: Create Render Backend (Steps 6–7)**

**Step 6: Create new Web Service on Render.com**
- Source: GitHub repo `omer3kale/ltt-cloud`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn mock_api:app --host 0.0.0.0 --port $PORT`
- Environment: `PYTHONUNBUFFERED=true`
- Region: **Frankfurt** (closest to Aachen)
- Plan: Free tier

**Step 7: Note the deployment URL**
- Format: `https://lca-backend-xxxx.onrender.com`
- Save for next steps

✅ **Verification**: Backend should start; visit health endpoint and check logs

---

### **Phase 4: Update Frontend API Endpoint (Step 8)**

**Step 8: Update `public/app.js` with environment-aware API_BASE_URL**

Replace:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

With:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://lca-backend-xxxx.onrender.com';  // Replace xxxx with your Render URL
```

Then commit & push:
```bash
git add public/app.js
git commit -m "fix: environment-aware API endpoint (localhost vs render)"
git push origin main
```

✅ **Verification**: GitHub Pages rebuilds automatically; check Actions tab

---

### **Phase 5: Update CORS Configuration (Step 9)**

**Step 9: Add GitHub Pages domain to CORS in `mock_api.py`**

Update:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://localhost:3000",
        "https://omer3kale.github.io",  # ← ADD THIS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit & push:
```bash
git add mock_api.py
git commit -m "fix: add GitHub Pages domain to CORS allow_origins"
git push origin main
```

✅ **Verification**: Render auto-redeploys on push; check backend logs for startup

---

### **Phase 6: Optional GitHub Actions Auto-Deployment (Step 10)**

**Step 10: Create `.github/workflows/deploy.yml`** (optional)

```yaml
name: Deploy Frontend to GitHub Pages

on:
  push:
    branches: [main]
    paths: ['public/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

Then commit & push:
```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Pages auto-deployment workflow"
git push origin main
```

✅ **Verification**: Actions tab shows successful deployment

---

### **Phase 7: End-to-End Testing (Steps 11–13)**

**Step 11: Test localhost deployment (pre-production)**
```bash
# Terminal 1: Backend on port 8000
cd /Users/sophiebeier/ltt-cloud && python3 mock_api.py

# Terminal 2: Frontend on port 8001
python3 -m http.server 8001 --directory public

# Visit: http://localhost:8001
# Fill form → Run Experiment → See three-tier results
```

**Step 12: Test GitHub Pages endpoint**
1. Open: https://omer3kale.github.io/ltt-cloud/
2. Verify form renders (no 404s, no missing CSS)
3. Fill form → "Run Experiment"
4. Should receive results from Render backend (not localhost)

**Step 13: Verify Render backend health**
```bash
curl https://lca-backend-xxxx.onrender.com/
# Should return: {"message": "LTT LCA Experiment API (...)", "timestamp": "..."}
```

✅ **All checks passed**: Deployment complete!

---

## Known Issues & Workarounds

| Issue | Impact | Workaround |
|-------|--------|-----------|
| **Render cold start** | First request takes 20–30s | Add monitoring; user should wait |
| **In-memory storage reset** | Experiments lost on Render redeploy | Plan database integration (Phase 3+) |
| **Chart.js CDN** | No offline support | Add local Chart.js if needed |
| **Asset paths** | Will 404 if absolute paths used | ✅ Already relative; OK |
| **RWTH logo path** | May 404 if not found | Update `background-image: url()` path in CSS |

---

## Rollback Plan

If issues occur:

1. **Frontend broken**: Revert last commit to `public/` folder
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Backend broken**: Redeploy from Render dashboard or push new main commit
   ```bash
   git push origin main  # Triggers auto-redeploy
   ```

3. **CORS issues**: Check Render logs for 403 errors; update `mock_api.py` and push

---

## Post-Deployment (Phase 3+)

Once deployment verified:
- [ ] Share GitHub Pages URL with colleagues
- [ ] Create Jupyter notebook template (with API docs)
- [ ] Document API endpoints for programmatic access
- [ ] Plan database integration (PostgreSQL on Render)
- [ ] Set up CI/CD monitoring

---

**Deployment Readiness**: ✅ READY  
**Estimated Duration**: 15–20 minutes  
**Date**: 28 March 2026
