### LTT Cloud LCA Platform ###

Cloud-ready Python monorepo for Brightway-based LCA dashboards at RWTH Aachen (Chair for Technical Thermodynamics / LTT).

***Goals***

- Turn Brightway-based LCA models into a collaborative web dashboard.
- Keep everything Python-first but ready to interoperate with Java (e.g., MontiCore, optimization).
- Target RWTH Kubernetes PaaS for deployment.
- Provide a PWA frontend (installable, offline-capable wrapper) with RWTH/LTT branding.

***Structure***

See src/ for code, k8s/ for Kubernetes manifests, docker/ for containers.

***Secrets***

This is an open-source project. **Never put secrets in code, config files, or commit history.**

All Python code reads configuration through `ltt_core.config.get_settings()`, which expects the same env var names everywhere. See [SECURITY.md](SECURITY.md) for the full secret flow.
