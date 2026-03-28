#!/usr/bin/env python3
"""
LCA Experiment API Backend — Brightway-Ready MVP
Implements the full schema for scenario-based LCA and AESA.
Supports five core Planetary Boundary-aligned impact categories.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import sqlite3
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# ============================================================================
# ENUMS
# ============================================================================

class FunctionalUnitEnum(str, Enum):
    KG_DAC = "1_kg_dac"
    KWH_ELEC = "1_kwh_elec"
    HKM_BEV = "100_km_bev"


class TechScenarioEnum(str, Enum):
    TODAY = "today"
    FUTURE_AVERAGE = "future_average"
    FUTURE_BEST_CASE = "future_best_case"


class SysScenarioEnum(str, Enum):
    CURRENT_POLICY = "current_policy"
    PLEDGES = "pledges"
    PARIS_2C = "paris_2c"
    PARIS_15C = "paris_15c"


class ElecMixEnum(str, Enum):
    COAL = "coal"
    NATURAL_GAS = "natural_gas"
    RENEWABLE = "renewable"
    EU_MIX = "eu_mix"


class CoreImpactCategoryEnum(str, Enum):
    """5 core Planetary Boundary-aligned categories."""
    CLIMATE_CHANGE = "climate_change"
    BIOSPHERE_INTEGRITY = "biosphere_integrity"
    FRESHWATER_USE = "freshwater_use"
    LAND_SYSTEM_CHANGE = "land_system_change"
    BIOGEOCHEMICAL_FLOWS = "biogeochemical_flows"


class SosStatusEnum(str, Enum):
    """Interpretation of share of Safe Operating Space."""
    SAFE = "safe"
    CRITICAL = "critical"
    BEYOND_SOS = "beyond_sos"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ExperimentVariables(BaseModel):
    """Parametric inputs for the foreground system."""
    electricity_mix: ElecMixEnum
    dac_efficiency: float = Field(ge=0, le=100, default=70.0)
    transport_distance_km: float = Field(ge=0, default=500.0)
    reactor_temperature_c: float = Field(ge=0, le=1200, default=750.0)
    system_boundary: str = Field(
        default="cradle_to_grave",
        pattern="^(cradle_to_grave|cradle_to_gate)$"
    )
    # BEV-specific (optional)
    vehicle_lifetime_km: Optional[float] = 200000.0
    production_emissions_kg_co2: Optional[float] = 20000.0
    disposal_emissions_kg_co2: Optional[float] = 1000.0


class ImpactResult(BaseModel):
    """LCIA midpoint result for a single impact category."""
    category: str
    value: float
    unit: str
    share_of_sos: float  # Mandatory: always present


class ContributionItem(BaseModel):
    """Contribution breakdown for climate_change or other impacts."""
    name: str
    value: float
    category: str = "climate_change"


class InterpretationEntry(BaseModel):
    """Interpretation flags for absolute sustainability assessment."""
    category: str
    within_sos: bool
    sos_status: SosStatusEnum
    share_of_sos: float


class LcaMetadata(BaseModel):
    """Metadata linking to Brightway and LCIA method."""
    bw_project: str
    bw_database: str
    impact_method: str
    sos_thresholds: Dict[str, float]
    bw_activity_code: Optional[str] = None


class ExperimentRunRequest(BaseModel):
    """Request to run an LCA experiment."""
    functional_unit: FunctionalUnitEnum
    tech_scenario: TechScenarioEnum = TechScenarioEnum.TODAY
    sys_scenario: SysScenarioEnum = SysScenarioEnum.CURRENT_POLICY
    variables: ExperimentVariables
    description: Optional[str] = Field(default=None, max_length=300)
    bw_project: Optional[str] = None
    bw_database: Optional[str] = None
    bw_activity_code: Optional[str] = None
    impact_method: Optional[str] = None


class ExperimentResultResponse(BaseModel):
    """Full response from an LCA experiment."""
    id: str
    timestamp: str
    functional_unit: FunctionalUnitEnum
    tech_scenario: TechScenarioEnum
    sys_scenario: SysScenarioEnum
    variables: ExperimentVariables
    lca_metadata: LcaMetadata
    impacts: List[ImpactResult]
    contributions: List[ContributionItem]
    interpretation: List[InterpretationEntry]
    additional_impacts: Optional[List[ImpactResult]] = None


# ============================================================================
# FASTAPI APP & MIDDLEWARE
# ============================================================================

app = FastAPI(
    title="LTT LCA Experiment API",
    description="Brightway-ready backend for scenario-based LCA and AESA"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://localhost:3000",
        "https://omer3kale.github.io",
        "https://omer3kale.github.io/ltt-cloud",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting (Issue 9)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# Global Planetary Boundary thresholds (reference state)
# Source: Steffen et al. 2015, updated in Hjalsted et al. 2021
GLOBAL_PB_THRESHOLDS = {
    "climate_change": 5.0e12,        # 5 Pg CO2-eq/year = 5e12 kg CO2-eq/year
    "biosphere_integrity": 2.5,      # PDF·m²·yr (global, per m²-year)
    "freshwater_use": 1.0e12,        # 1000 km³/year = 1e12 m³/year
    "land_system_change": 100e6,     # 100 Mha/year = 100e6 hectares
    "biogeochemical_flows": 2.0e12,  # 2 Tg N/year = 2e12 kg N/year
}

# AESA egalitarian allocation: per-capita annual budgets
WORLD_POPULATION = 8.1e9  # people (2026)

def calculate_sos_thresholds() -> Dict[str, float]:
    """
    Calculate per-capita annual AESA thresholds via egalitarian allocation.
    Converts global PB from planetary scale to per-capita annual scale.
    Per Hjalsted et al. 2021: share_of_sos = individual_impact / allocated_budget
    """
    return {
        "climate_change": GLOBAL_PB_THRESHOLDS["climate_change"] / WORLD_POPULATION,  # kg CO2-eq/person/year
        "biosphere_integrity": GLOBAL_PB_THRESHOLDS["biosphere_integrity"] / WORLD_POPULATION,  # per person
        "freshwater_use": GLOBAL_PB_THRESHOLDS["freshwater_use"] / WORLD_POPULATION,  # m³/person/year
        "land_system_change": GLOBAL_PB_THRESHOLDS["land_system_change"] / WORLD_POPULATION,  # ha/person/year
        "biogeochemical_flows": GLOBAL_PB_THRESHOLDS["biogeochemical_flows"] / WORLD_POPULATION,  # kg N/person/year
    }

SOS_THRESHOLDS = calculate_sos_thresholds()

# Brightway activity code mapping per functional unit (Issue 5)
ACTIVITY_MAP: Dict[str, str] = {
    "1_kg_dac": "direct air capture, CO2, 1 kg | ecoinvent 3.10 cutoff",
    "1_kwh_elec": "market for electricity, medium voltage | CH | ecoinvent 3.10",
    "100_km_bev": "transport, passenger car, battery electric | RER | ecoinvent 3.10",
}

ELECTRICITY_GWP = {
    "coal": 0.82,
    "natural_gas": 0.49,
    "renewable": 0.04,
    "eu_mix": 0.30,
}

# In-memory experiment store
experiments: Dict[str, ExperimentResultResponse] = {}

# ============================================================================
# DATABASE (SQLite) HELPERS — Issue 10
# ============================================================================

DB_PATH = Path("experiments.db")


def init_db() -> None:
    """Initialize SQLite database for persistent experiment storage."""
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS experiments (
          id TEXT PRIMARY KEY,
          result_json TEXT NOT NULL
        )
        """
    )
    con.commit()
    con.close()


def save_experiment(exp_id: str, result_dict: Dict[str, Any]) -> None:
    """Store experiment result in SQLite."""
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO experiments (id, result_json) VALUES (?, ?)",
        (exp_id, json.dumps(result_dict)),
    )
    con.commit()
    con.close()


def load_experiment(exp_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve experiment result from SQLite."""
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT result_json FROM experiments WHERE id = ?",
        (exp_id,),
    ).fetchone()
    con.close()
    return json.loads(row[0]) if row else None


# ============================================================================
# COMPUTATION FUNCTIONS
# ============================================================================

def compute_impacts(req: ExperimentRunRequest) -> List[ImpactResult]:
    """
    Parametric multi-impact calculation for 5 core PB categories.
    Routes to specialized calculators based on functional unit.
    """
    fu = req.functional_unit
    
    if fu == FunctionalUnitEnum.HKM_BEV:
        return _compute_impacts_bev(req)
    else:
        return _compute_impacts_dac(req)


def _compute_impacts_dac(req: ExperimentRunRequest) -> List[ImpactResult]:
    """Compute impacts for DAC (1 kg) or electricity (1 kWh) functional units."""
    eff = req.variables.dac_efficiency / 100.0
    mix = req.variables.electricity_mix.value
    dist = req.variables.transport_distance_km
    temp = req.variables.reactor_temperature_c

    gwp_elec = ELECTRICITY_GWP.get(mix, 0.30)

    # Technology scenario multipliers (ex-ante learning)
    tech_mult = {
        "today": 1.0,
        "future_average": 0.75,
        "future_best_case": 0.55,
    }

    # System scenario multipliers (prospective, SSP/RCP-mapped)
    sys_mult = {
        "current_policy": 1.0,
        "pledges": 0.85,
        "paris_2c": 0.65,
        "paris_15c": 0.45,
    }

    t_mult = tech_mult.get(req.tech_scenario.value, 1.0)
    s_mult = sys_mult.get(req.sys_scenario.value, 1.0)

    # Parametric GWP100 formula (base driver for all impacts)
    gwp = (
        (1.5 / max(eff, 0.01)) * gwp_elec * 10
        + dist * 0.0002
        + (temp / 750.0) * 5.0
    ) * t_mult * s_mult

    # Raw impact values for all 5 core categories
    raw = {
        "climate_change": (gwp, "kg CO2-eq"),
        "biosphere_integrity": (gwp * 0.04, "PDF·m²·yr"),
        "freshwater_use": (gwp * 0.06, "m³"),
        "land_system_change": (gwp * 0.02, "m²a·crop-eq"),
        "biogeochemical_flows": (gwp * 0.015, "kg N-eq"),
    }

    return [
        ImpactResult(
            category=cat,
            value=round(val, 6),
            unit=unit,
            share_of_sos=round(val / SOS_THRESHOLDS.get(cat, 1.0), 4),
        )
        for cat, (val, unit) in raw.items()
    ]


def _compute_impacts_bev(req: ExperimentRunRequest) -> List[ImpactResult]:
    """Compute impacts for BEV (100 km) with lifecycle assessment."""
    vehicle_lifetime = req.variables.vehicle_lifetime_km or 200000.0
    production_emissions = req.variables.production_emissions_kg_co2 or 20000.0
    disposal_emissions = req.variables.disposal_emissions_kg_co2 or 1000.0
    
    # Use-phase energy for 100 km (0.2 kWh/km)
    energy_per_100km = 20.0
    gwp_elec = ELECTRICITY_GWP.get(req.variables.electricity_mix.value, 0.30)
    use_phase_emissions = energy_per_100km * gwp_elec
    
    # Distribute production/disposal over lifetime
    cycles_per_lifetime = vehicle_lifetime / 100.0
    production_per_100km = production_emissions / cycles_per_lifetime
    disposal_per_100km = disposal_emissions / cycles_per_lifetime
    
    gwp_total = production_per_100km + use_phase_emissions + disposal_per_100km
    
    # BEV-specific scenario multipliers
    tech_mult = {"today": 1.0, "future_average": 0.65, "future_best_case": 0.40}
    sys_mult = {"current_policy": 1.0, "pledges": 0.85, "paris_2c": 0.65, "paris_15c": 0.45}
    
    t_mult = tech_mult.get(req.tech_scenario.value, 1.0)
    s_mult = sys_mult.get(req.sys_scenario.value, 1.0)
    gwp_final = gwp_total * t_mult * s_mult
    
    # Scale other impacts from BEV GWP
    raw = {
        "climate_change": (gwp_final, "kg CO2-eq"),
        "biosphere_integrity": (gwp_final * 0.03, "PDF·m²·yr"),
        "freshwater_use": (gwp_final * 0.04, "m³"),
        "land_system_change": (gwp_final * 0.015, "m²a·crop-eq"),
        "biogeochemical_flows": (gwp_final * 0.01, "kg N-eq"),
    }
    
    return [
        ImpactResult(
            category=cat,
            value=round(val, 6),
            unit=unit,
            share_of_sos=round(val / SOS_THRESHOLDS.get(cat, 1.0), 4),
        )
        for cat, (val, unit) in raw.items()
    ]


def compute_sos_status(share_of_sos: float) -> SosStatusEnum:
    """Classify share_of_sos into interpretation status."""
    if share_of_sos < 0.7:
        return SosStatusEnum.SAFE
    elif share_of_sos <= 1.0:
        return SosStatusEnum.CRITICAL
    else:
        return SosStatusEnum.BEYOND_SOS


def compute_interpretation(impacts: List[ImpactResult]) -> List[InterpretationEntry]:
    """Build interpretation entries from impact results."""
    return [
        InterpretationEntry(
            category=impact.category,
            within_sos=impact.share_of_sos <= 1.0,
            sos_status=compute_sos_status(impact.share_of_sos),
            share_of_sos=impact.share_of_sos,
        )
        for impact in impacts
    ]


def compute_contributions(req: ExperimentRunRequest, gwp_climate: float) -> List[ContributionItem]:
    """
    Contribution breakdown for climate_change.
    Scales based on electricity mix and functional unit.
    """
    fu = req.functional_unit
    
    if fu == FunctionalUnitEnum.HKM_BEV:
        return _contributions_bev(req, gwp_climate)
    else:
        return _contributions_dac(req, gwp_climate)


def _contributions_dac(req: ExperimentRunRequest, gwp_climate: float) -> List[ContributionItem]:
    """Contribution breakdown for DAC and electricity functional units."""
    eff = req.variables.dac_efficiency / 100.0
    gwp_elec = ELECTRICITY_GWP.get(req.variables.electricity_mix.value, 0.30)
    
    dac_energy_raw = (1.5 / max(eff, 0.01)) * gwp_elec * 10
    transport_raw = req.variables.transport_distance_km * 0.0002
    heat_raw = (req.variables.reactor_temperature_c / 750.0) * 5.0
    
    total_raw = dac_energy_raw + transport_raw + heat_raw
    scale = gwp_climate / max(total_raw, 0.001)
    
    return [
        ContributionItem(name="DAC Energy", value=round(dac_energy_raw * scale, 3)),
        ContributionItem(name="Transport", value=round(transport_raw * scale, 3)),
        ContributionItem(name="Reactor Heat", value=round(heat_raw * scale, 3)),
    ]


def _contributions_bev(req: ExperimentRunRequest, gwp_climate: float) -> List[ContributionItem]:
    """Contribution breakdown for BEV functional unit."""
    vehicle_lifetime = req.variables.vehicle_lifetime_km or 200000.0
    production_emissions = req.variables.production_emissions_kg_co2 or 20000.0
    disposal_emissions = req.variables.disposal_emissions_kg_co2 or 1000.0
    
    gwp_elec = ELECTRICITY_GWP.get(req.variables.electricity_mix.value, 0.30)
    energy_per_100km = 20.0
    use_phase = energy_per_100km * gwp_elec
    
    cycles_per_lifetime = vehicle_lifetime / 100.0
    production_per_cycle = production_emissions / cycles_per_lifetime
    disposal_per_cycle = disposal_emissions / cycles_per_lifetime
    
    total_raw = production_per_cycle + use_phase + disposal_per_cycle
    scale = gwp_climate / max(total_raw, 0.001)
    
    return [
        ContributionItem(name="Production", value=round(production_per_cycle * scale, 3)),
        ContributionItem(name="Use-Phase", value=round(use_phase * scale, 3)),
        ContributionItem(name="Disposal", value=round(disposal_per_cycle * scale, 3)),
    ]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check."""
    return {
        "message": "LTT LCA Experiment API (Brightway-ready MVP)",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/experiments/run", status_code=200)
@limiter.limit("10/minute")
def run_experiment(request: Request, req: ExperimentRunRequest):
    """
    Start an LCA experiment and return experiment ID.
    Rate limited to 10/minute per IP (Issue 9).
    
    Returns:
        {"id": "uuid"} on success (HTTP 200)
    
    Raises:
        HTTPException 400 on invalid request
        HTTP 429 on rate limit exceeded
    """
    try:
        exp_id = str(uuid.uuid4())

        # Compute impacts for the 5 core PB categories
        impacts = compute_impacts(req)

        # Get climate_change value for contribution calculation
        climate_impact = next((i for i in impacts if i.category == "climate_change"), None)
        climate_value = climate_impact.value if climate_impact else 0.0

        # Compute contributions for climate_change
        contributions = compute_contributions(req, climate_value)

        # Compute interpretation entries
        interpretation = compute_interpretation(impacts)

        # Build LCA metadata
        bw_project = req.bw_project or "LCAEPE"
        bw_database = req.bw_database or "ecoinvent-3.10-cutoff"
        impact_method = req.impact_method or "EF3.1_PB"

        # Issue 5: Populate bw_activity_code from ACTIVITY_MAP
        bw_activity_code = ACTIVITY_MAP.get(req.functional_unit, None)

        lca_metadata = LcaMetadata(
            bw_project=bw_project,
            bw_database=bw_database,
            impact_method=impact_method,
            sos_thresholds=SOS_THRESHOLDS,
            bw_activity_code=bw_activity_code,
        )

        # Build full response
        result = ExperimentResultResponse(
            id=exp_id,
            timestamp=datetime.utcnow().isoformat(),
            functional_unit=req.functional_unit,
            tech_scenario=req.tech_scenario,
            sys_scenario=req.sys_scenario,
            variables=req.variables,
            lca_metadata=lca_metadata,
            impacts=impacts,
            contributions=contributions,
            interpretation=interpretation,
            additional_impacts=None,
        )

        # Store in memory and SQLite (Issue 10)
        experiments[exp_id] = result
        save_experiment(exp_id, result.model_dump())

        return {"id": exp_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Experiment creation failed: {str(e)}")


@app.get("/experiments/{exp_id}/result", status_code=200)
def get_experiment_result(exp_id: str):
    """
    Retrieve experiment results by ID.
    Checks memory cache first, then SQLite (Issue 10).
    
    Returns:
        ExperimentResultResponse (HTTP 200) on success
    
    Raises:
        HTTPException 404 if experiment not found
    """
    # Check in-memory cache first
    if exp_id in experiments:
        result = experiments[exp_id]
        return result.model_dump()
    
    # Fall back to SQLite (Issue 10)
    stored = load_experiment(exp_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"Experiment {exp_id} not found")
    
    return stored


if __name__ == "__main__":
    import uvicorn
    
    # Initialize SQLite database (Issue 10)
    init_db()
    
    uvicorn.run(app, host="127.0.0.1", port=8000)

