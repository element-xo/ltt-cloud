from fastapi import FastAPI
from .routers import health, lca, scenarios

app = FastAPI(title="LTT LCA API")

app.include_router(health.router)
app.include_router(lca.router)
app.include_router(scenarios.router)

@app.get("/")
def root():
    return {"message": "LTT LCA API"}