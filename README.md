### LTT Cloud LCA Platform ###

Cloud-ready Python monorepo for Brightway-based LCA dashboards at RWTH Aachen (Chair for Technical Thermodynamics / LTT).

***Goals***

- Turn Brightway-based LCA models into a collaborative web dashboard.
- Keep everything Python-first but ready to interoperate with Java (e.g., MontiCore, optimization).
- Target RWTH Kubernetes PaaS for deployment.
- Provide a PWA frontend (installable, offline-capable wrapper) with RWTH/LTT branding.

***Tech Stack***

 Python 3.12
 FastAPI for backend/API
 Streamlit for internal/exploration dashboards
 PostgreSQL (SQLAlchemy + Alembic) for project/scenario/run data
 Redis for caching simulation results
 Brightway25 for LCA
 Docker + docker-compose for local dev
// Helm/Knative manifests for RWTH Kubernetes

***Local Development***

1. Install dependencies: <pip install -e .>
2. Run <docker-compose up> to start services.
3. Access:
   - PWA: http://localhost:8080
   - UI: http://localhost:8501
   - API: http://localhost:8000

***Structure***

See src/ for code, k8s/ for Kubernetes manifests, docker/ for containers.

***Secrets***

This is an open-source project. **Never put secrets in code, config files, or commit history.**

- **Local dev:** Copy `.env.example` to `.env`, fill in real values. `.env` is gitignored.
- **CI/CD:** Set secrets in GitHub Actions (Settings > Secrets).
- **Production:** Provide env vars via Kubernetes Secret objects.

All Python code reads configuration through `ltt_core.config.get_settings()`, which expects the same env var names everywhere. See [SECURITY.md](SECURITY.md) for the full secret flow.