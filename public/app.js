// Environment-aware API endpoint
const API_BASE_URL = (function () {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';  // Development
  }
  // Production: DigitalOcean backend
  // INSTRUCTION: Replace xxxx with your actual DigitalOcean app ID
  // Get URL from: https://cloud.digitalocean.com/apps → your app → Live Domain
  return 'https://lca-backend-xxxx.ondigitalocean.app';
})();

const API_URL = API_BASE_URL;

// DOM Elements
const experimentForm = document.getElementById('experimentForm');
const runButton = document.getElementById('runButton');
const errorBox = document.getElementById('errorBox');
const resultContainer = document.getElementById('resultContainer');
const noResultBox = document.getElementById('noResultBox');
const functionalUnitSelect = document.getElementById('functional_unit');
const bevFieldset = document.getElementById('bev-fieldset');

// Chart instance
let contributionChart = null;

// ============ EVENT LISTENERS ============

functionalUnitSelect.addEventListener('change', handleFunctionalUnitChange);
runButton.addEventListener('click', handleRunExperiment);

// Initialize scenario cards
document.querySelectorAll('.scenario-card').forEach(card => {
  card.addEventListener('click', () => loadScenarioCard(card));
});

// ============ FORM HANDLING ============

function handleFunctionalUnitChange() {
  const value = functionalUnitSelect.value;
  
  // Show/hide BEV fields
  if (value === '100_km_bev') {
    bevFieldset.style.display = 'block';
  } else {
    bevFieldset.style.display = 'none';
  }

  // Show/hide other fields based on functional unit
  const dacEfficiencyGroup = document.getElementById('dac-efficiency-group');
  const transportDistanceGroup = document.getElementById('transport-distance-group');
  const reactorTemperatureGroup = document.getElementById('reactor-temperature-group');

  if (value === '1_kg_dac') {
    dacEfficiencyGroup.style.display = 'block';
    transportDistanceGroup.style.display = 'block';
    reactorTemperatureGroup.style.display = 'block';
  } else if (value === '1_kwh_elec') {
    dacEfficiencyGroup.style.display = 'none';
    transportDistanceGroup.style.display = 'none';
    reactorTemperatureGroup.style.display = 'none';
  } else if (value === '100_km_bev') {
    dacEfficiencyGroup.style.display = 'none';
    transportDistanceGroup.style.display = 'none';
    reactorTemperatureGroup.style.display = 'none';
  }
}

function loadScenarioCard(card) {
  // Load form values from scenario card data attributes
  document.getElementById('functional_unit').value = card.dataset.functionalUnit;
  document.getElementById('tech_scenario').value = card.dataset.techScenario;
  document.getElementById('sys_scenario').value = card.dataset.sysScenario;
  document.getElementById('electricity_mix').value = card.dataset.electricityMix;
  document.getElementById('system_boundary').value = card.dataset.systemBoundary;

  if (card.dataset.dacEfficiency) {
    document.getElementById('dac_efficiency').value = card.dataset.dacEfficiency;
  }
  if (card.dataset.transportDistanceKm) {
    document.getElementById('transport_distance_km').value = card.dataset.transportDistanceKm;
  }
  if (card.dataset.reactorTemperatureC) {
    document.getElementById('reactor_temperature_c').value = card.dataset.reactorTemperatureC;
  }

  // Update UI visibility
  handleFunctionalUnitChange();

  // Automatically run experiment
  handleRunExperiment();
}

// ============ API INTERACTION ============

async function handleRunExperiment() {
  const runButton = document.getElementById('runButton');
  const statusMsg = document.getElementById('status-msg');

  runButton.disabled = true;
  runButton.textContent = 'Running...';
  statusMsg.style.display = 'block';
  statusMsg.textContent = 'Connecting to backend (cold start may take ~30s)...';

  try {
    // Clear previous errors
    errorBox.style.display = 'none';
    errorBox.textContent = '';

    // Build request payload
    const functionalUnit = document.getElementById('functional_unit').value;
    const techScenario = document.getElementById('tech_scenario').value;
    const sysScenario = document.getElementById('sys_scenario').value;
    const systemBoundary = document.getElementById('system_boundary').value;

    const request = {
      functional_unit: functionalUnit,
      tech_scenario: techScenario,
      sys_scenario: sysScenario,
      variables: {
        electricity_mix: document.getElementById('electricity_mix').value,
        dac_efficiency: parseFloat(document.getElementById('dac_efficiency').value) || 75,
        transport_distance_km: parseFloat(document.getElementById('transport_distance_km').value) || 300,
        reactor_temperature_c: parseFloat(document.getElementById('reactor_temperature_c').value) || 800,
        system_boundary: systemBoundary,
      },
    };

    // Add BEV fields if present
    if (functionalUnit === '100_km_bev') {
      request.variables.vehicle_lifetime_km = parseFloat(document.getElementById('vehicle_lifetime_km').value) || 200000;
      request.variables.production_emissions_kg_co2 = parseFloat(document.getElementById('production_emissions_kg_co2').value) || 20000;
      request.variables.disposal_emissions_kg_co2 = parseFloat(document.getElementById('disposal_emissions_kg_co2').value) || 1000;
    }

    console.log('Request payload:', request);

    // POST to run experiment
    statusMsg.textContent = 'Fetching results...';
    const runResponse = await fetch(`${API_URL}/experiments/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!runResponse.ok) {
      const err = await runResponse.json().catch(() => ({}));
      statusMsg.textContent = `Error ${runResponse.status}: ${err.detail || runResponse.statusText}`;
      return;
    }

    const runData = await runResponse.json();
    const experimentId = runData.id;
    console.log('Experiment ID:', experimentId);

    // GET result
    const resultResponse = await fetch(`${API_URL}/experiments/${experimentId}/result`);
    if (!resultResponse.ok) {
      statusMsg.textContent = `Result fetch failed (${resultResponse.status}).`;
      return;
    }

    const result = await resultResponse.json();
    console.log('Result:', result);

    // Render results
    statusMsg.style.display = 'none';
    renderResults(result);
  } catch (error) {
    console.error('Error:', error);
    statusMsg.textContent = `Network error: ${error.message}`;
  } finally {
    runButton.disabled = false;
    runButton.textContent = 'Run Experiment';
  }
}

// ============ RESULTS RENDERING ============

function renderResults(result) {
  resultContainer.style.display = 'flex';
  noResultBox.style.display = 'none';

  // Populate metadata
  document.getElementById('exp-id').textContent = result.id.substring(0, 8) + '...';
  document.getElementById('exp-timestamp').textContent = new Date(result.timestamp).toLocaleString();
  document.getElementById('exp-bw-project').textContent = result.lca_metadata.bw_project;
  document.getElementById('exp-bw-database').textContent = result.lca_metadata.bw_database;
  document.getElementById('exp-impact-method').textContent = result.lca_metadata.impact_method;

  // Find impacts by category
  const impactMap = {};
  result.impacts.forEach(impact => {
    impactMap[impact.category] = impact;
  });

  const interpretationMap = {};
  result.interpretation.forEach(entry => {
    interpretationMap[entry.category] = entry;
  });

  // Tier 1: Climate
  const climateImpact = impactMap['climate_change'];
  if (climateImpact) {
    const climateInterpretation = interpretationMap['climate_change'];
    
    document.getElementById('climate-value').textContent = climateImpact.value.toFixed(3);
    document.getElementById('climate-share').textContent = 
      `Share of SOS: ${climateImpact.share_of_sos.toFixed(3)} (${(climateImpact.share_of_sos * 100).toFixed(1)}%)`;
    
    renderSosBar('climate-sos-bar', climateImpact.share_of_sos, climateInterpretation);
    
    const sosStatus = climateInterpretation.sos_status;
    let interpretation = '';
    if (sosStatus === 'safe') {
      interpretation = '✓ Within Safe Operating Space';
    } else if (sosStatus === 'critical') {
      interpretation = '⚠ Approaching SOS boundary (70-100%)';
    } else {
      interpretation = '✗ Beyond Safe Operating Space (>100%)';
    }
    document.getElementById('climate-interpretation').textContent = interpretation;
  }

  // Tier 2: Biosphere & Freshwater
  const tier2Categories = ['biosphere_integrity', 'freshwater_use'];
  const tier2Tbody = document.getElementById('tier2-tbody');
  tier2Tbody.innerHTML = '';
  tier2Categories.forEach(cat => {
    const impact = impactMap[cat];
    const interp = interpretationMap[cat];
    if (impact) {
      const row = createImpactRow(cat, impact, interp);
      tier2Tbody.appendChild(row);
    }
  });

  // Tier 3: Land & Biogeochemical
  const tier3Categories = ['land_system_change', 'biogeochemical_flows'];
  const tier3Tbody = document.getElementById('tier3-tbody');
  tier3Tbody.innerHTML = '';
  tier3Categories.forEach(cat => {
    const impact = impactMap[cat];
    const interp = interpretationMap[cat];
    if (impact) {
      const row = createImpactRow(cat, impact, interp);
      tier3Tbody.appendChild(row);
    }
  });

  // Contributions
  renderContributions(result.contributions, climateImpact?.value || 0);
}

function createImpactRow(categoryKey, impact, interpretation) {
  const row = document.createElement('tr');
  
  const categoryName = {
    biosphere_integrity: 'Biosphere Integrity',
    freshwater_use: 'Freshwater Use',
    land_system_change: 'Land System Change',
    biogeochemical_flows: 'Biogeochemical Flows',
  }[categoryKey];

  const statusBadgeClass = `status-${interpretation.sos_status}`;
  const statusText = {
    safe: 'Safe',
    critical: 'Critical',
    beyond_sos: 'Beyond SOS',
  }[interpretation.sos_status];

  row.innerHTML = `
    <td>${categoryName}</td>
    <td>${impact.value.toFixed(4)} ${impact.unit}</td>
    <td>${impact.share_of_sos.toFixed(3)}</td>
    <td><span class="status-badge ${statusBadgeClass}">${statusText}</span></td>
  `;
  
  return row;
}

function renderSosBar(elementId, shareOfSos, interpretation) {
  const bar = document.getElementById(elementId);
  bar.innerHTML = '';

  const width = Math.min(shareOfSos * 100, 100);
  const statusClass = {
    safe: 'safe',
    critical: 'critical',
    beyond_sos: 'beyond',
  }[interpretation.sos_status];

  const fill = document.createElement('div');
  fill.className = `sos-bar-fill ${statusClass}`;
  fill.style.width = width + '%';
  fill.textContent = (shareOfSos * 100).toFixed(1) + '%';

  bar.appendChild(fill);

  // Add marker at 70% (critical boundary)
  const marker = document.createElement('div');
  marker.className = 'sos-bar-marker sos-marker-1';
  bar.appendChild(marker);
}

function renderContributions(contributions, climateValue) {
  const list = document.getElementById('contributionList');
  list.innerHTML = '';

  if (!contributions || contributions.length === 0) {
    list.innerHTML = '<p>No contributions data</p>';
    return;
  }

  contributions.forEach(contrib => {
    const percentage = climateValue > 0 ? (contrib.value / climateValue * 100).toFixed(1) : 0;
    
    const item = document.createElement('div');
    item.className = 'contribution-item';
    item.innerHTML = `
      <strong>${contrib.name}</strong>
      <span>${contrib.value.toFixed(3)} kg CO₂-eq (${percentage}%)</span>
    `;
    list.appendChild(item);
  });

  // Chart
  renderContributionChart(contributions);
}

function renderContributionChart(contributions) {
  const ctx = document.getElementById('contributionChart').getContext('2d');

  // Destroy existing chart if it exists
  if (contributionChart) {
    contributionChart.destroy();
  }

  contributionChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: contributions.map(c => c.name),
      datasets: [{
        data: contributions.map(c => c.value),
        backgroundColor: ['#00549F', '#E8641C', '#9C27B0'],
        borderColor: ['#003B70', '#C24A0F', '#6A1B9A'],
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.parsed.toFixed(3) + ' kg CO₂-eq';
            }
          }
        }
      },
    },
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  handleFunctionalUnitChange();
});

// Service worker registration
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(err => {
    console.log("Service Worker registration failed:", err);
  });
}
