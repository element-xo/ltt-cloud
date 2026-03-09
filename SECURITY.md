# Security Policy -- LTT Cloud (Open Source)

## Sensitive Information Management

This project is **open source** under the RWTH / element-xo enterprise.
All code pushed to `element-xo` is publicly visible.

### Rules

1. **Never commit secrets.** No passwords, tokens, API keys, or credentials in source code.
2. **Use `.env` files locally.** `.env` is in `.gitignore` and will never be tracked.
3. **`.env.example` is the template.** It contains placeholder values only -- copy it to `.env` and fill in real values locally.
4. **Use GitHub Secrets for CI/CD.** Store all deployment credentials in GitHub Actions secrets under the organization settings.
5. **Use Kubernetes Secrets in production.** Never bake credentials into container images or YAML committed to the repo.

### What goes where

| Secret type | Local dev | CI/CD | Production (K8s) |
|---|---|---|---|
| DB credentials | `.env` (gitignored) | GitHub Actions Secrets | K8s Secret |
| Redis URL | `.env` | GitHub Actions Secrets | K8s ConfigMap |
| API keys / tokens | `.env` | GitHub Actions Secrets | K8s Secret |
| TLS certs | local trust store | GitHub Actions Secrets | K8s Secret / cert-manager |

---

## Secret Flow Overview

### 1. Local Development

```
.env.example  --(copy)-->  .env  --(read by)-->  docker-compose + Python Settings
```

- Developer copies `.env.example` to `.env` and fills in local values.
- `.env` is listed in `.gitignore` -- it is never tracked or pushed.
- `docker-compose.yml` loads `.env` via `env_file: .env`.
- Python reads the same variables through `ltt_core.config.Settings` (pydantic BaseSettings with `env_file=".env"`).

### 2. GitHub Actions (CI/CD)

```
GitHub Secrets  --(injected as env vars)-->  CI runner  -->  docker build / tests
```

- All secrets (`DATABASE_URL`, `REDIS_URL`, registry tokens, etc.) are stored in **Settings > Secrets and variables > Actions** in the GitHub repository or organization.
- Workflow YAML references them as `${{ secrets.DATABASE_URL }}` -- GitHub masks the values in logs automatically.
- Never `echo` or print secrets in CI steps.

### 3. Kubernetes / Knative (Production)

```
kubectl create secret  -->  K8s Secret object  --(envFrom / valueFrom)-->  Pod env vars
```

- Credentials are stored in a Kubernetes `Secret` named `ltt-cloud-secrets` in namespace `ltt-lca`.
- Deployments and Knative Services reference the secret via `envFrom` or individual `env[].valueFrom.secretKeyRef`.
- The container sees the **same environment variable names** that the Python `Settings` class expects (`DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT`).
- Example:

```yaml
# In a Deployment spec:
envFrom:
  - secretRef:
      name: ltt-cloud-secrets
# Or per-variable:
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: ltt-cloud-secrets
        key: DATABASE_URL
```

---

### If you accidentally commit a secret

1. Rotate the credential immediately.
2. Use `git filter-branch` or `git filter-repo` to remove it from history.
3. Force-push the cleaned history.
4. Notify the team.

### Pre-commit hook (recommended)

Install `detect-secrets` to catch accidental secret commits:

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```

Add to `.pre-commit-config.yaml` if using pre-commit hooks.
