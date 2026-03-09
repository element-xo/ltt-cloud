import streamlit as st

from ltt_core.config import RWTH_BLUE

st.set_page_config(
    page_title="RWTH LTT LCA Dashboard",
    layout="wide"
)

# Header
st.markdown(f"""
<div style="background-color: {RWTH_BLUE}; padding: 10px; color: white;">
    <h1>RWTH LTT Energiesysteme · LCA Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar
co2 = st.sidebar.slider("CO2 mass (t)", 0.0, 100.0, 10.0)
energy = st.sidebar.slider("Electricity input (MWh)", 0.0, 1000.0, 100.0)

if st.button("Run LCA"):
    # Call API
    import requests
    response = requests.post("http://localhost:8000/lca", json={
        "functional_unit": {"co2": co2, "energy": energy},
        "method": ["IPCC", "2013", "total"]
    })
    if response.ok:
        result = response.json()
        st.metric("LCA Score (CO2-eq)", result["score"])
        st.bar_chart([result["score"], 0])  # Placeholder chart