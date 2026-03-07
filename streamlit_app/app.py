import os
import json
import pandas as pd
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="SupplyShield Demo", layout="wide")
st.title("SupplyShield: Supply Chain Resilience Agent (Demo)")

st.caption("Live news → alert.json → risk scoring → mitigation options → drafted actions + approval gate")

# --- Config ---
API_KEY = st.secrets.get("NEWSDATA_API_KEY", os.getenv("NEWSDATA_API_KEY", "")).strip()
NEWSDATA_URL = "https://newsdata.io/api/1/news"

QUERY = st.sidebar.text_input("News query", "port strike shipping logistics congestion delay")
min_conf = st.sidebar.slider("Min confidence", 0.0, 1.0, 0.6, 0.05)

# --- Helper functions ---
LABEL_KEYWORDS = {
    "STRIKE": ["strike", "walkout", "union", "dockworkers", "longshore"],
    "PORT_DISRUPTION": ["port", "terminal", "congestion", "backlog", "closure", "vessel", "container"],
    "SANCTIONS": ["sanction", "embargo", "export control"],
    "GEOPOLITICAL": ["conflict", "escalation", "attack", "war", "blockade"],
    "WEATHER": ["storm", "hurricane", "typhoon", "flood", "wildfire", "earthquake"],
}

def guess_label(title: str, desc: str) -> str:
    t = (title + " " + desc).lower()
    for label, kws in LABEL_KEYWORDS.items():
        if any(k in t for k in kws):
            return label
    return "OTHER"

def guess_severity(title: str, desc: str) -> str:
    t = (title + " " + desc).lower()
    if any(k in t for k in ["shutdown", "closed", "blockade", "major", "severe", "halt"]):
        return "high"
    if any(k in t for k in ["delay", "congestion", "strike", "disruption"]):
        return "medium"
    return "low"

def sev_to_delay(sev: str) -> int:
    return {"low": 2, "medium": 7, "high": 14}.get(sev, 5)

def compute_risk(alert: dict, erp: dict) -> dict:
    on_hand = float(erp["on_hand"])
    daily = float(erp["daily_demand"])
    inbound_eta = erp["inbound_eta"]
    delay = int(alert["predicted_delay_days"])
    today = datetime.utcnow().date().isoformat()

    # Simple stockout math (demo)
    days_to_stockout = on_hand / daily if daily > 0 else 10**9

    risk = {
        "sku": erp["sku"],
        "today": today,
        "days_to_stockout": round(days_to_stockout, 2),
        "original_inbound_eta": inbound_eta,
        "predicted_delay_days": delay,
        "sla_breach_probability": 0.7 if days_to_stockout < delay else 0.15,
        "why_it_matters": "Stockout risk drives downtime, expedite cost, and SLA penalties."
    }
    return risk

def simulate_options(risk: dict):
    return [
        {"option": "air_freight", "cost": "High", "speed": "Fastest", "impact": "Protect OTIF when stockout is near"},
        {"option": "reroute", "cost": "Medium", "speed": "Medium", "impact": "Avoid affected lane/port"},
        {"option": "allocation_or_buffer", "cost": "Medium", "speed": "Medium", "impact": "Reallocate inventory / build safety stock"},
    ]

def choose_option(risk: dict):
    if risk["days_to_stockout"] <= 7 or risk["sla_breach_probability"] >= 0.6:
        return "air_freight"
    return "reroute"

# --- Mock ERP snapshot (for demo) ---
st.sidebar.subheader("Mock ERP Snapshot")
sku = st.sidebar.text_input("SKU", "MCU-17")
on_hand = st.sidebar.number_input("On hand", min_value=0.0, value=1000.0)
daily_demand = st.sidebar.number_input("Daily demand", min_value=0.1, value=42.0)
inbound_eta = st.sidebar.text_input("Inbound ETA (YYYY-MM-DD)", "2026-03-20")

erp = {"sku": sku, "on_hand": on_hand, "daily_demand": daily_demand, "inbound_eta": inbound_eta}

# --- Ingest from NewsData ---
col1, col2, col3 = st.columns([1,1,1])

with col1:
    st.subheader("1) Ingest live signals")
    if st.button("Pull latest disruption news"):
        if not API_KEY:
            st.error("Missing NEWSDATA_API_KEY in Streamlit Secrets.")
        else:
            r = requests.get(NEWSDATA_URL, params={"apikey": API_KEY, "q": QUERY, "language": "en"}, timeout=30)
            data = r.json()
            results = data.get("results", []) or []
            st.session_state["results"] = results
            st.success(f"Fetched {len(results)} articles")

with col2:
    st.subheader("2) Filter + classify")
    results = st.session_state.get("results", [])
    if results:
        rows = []
        for a in results[:50]:
            title = a.get("title","") or ""
            desc = a.get("description","") or ""
            label = guess_label(title, desc)
            sev = guess_severity(title, desc)
            conf = 0.85 if label != "OTHER" else 0.55
            if conf >= min_conf and label != "OTHER":
                rows.append({
                    "title": title,
                    "label": label,
                    "severity": sev,
                    "confidence": conf,
                    "link": a.get("link","")
                })
        st.session_state["filtered"] = rows
        st.write(f"Relevant items: {len(rows)}")

with col3:
    st.subheader("3) Human approval gate")
    approved = st.checkbox("Approve recommended action")
    st.session_state["approved"] = approved

st.divider()

filtered = st.session_state.get("filtered", [])
if not filtered:
    st.info("Click **Pull latest disruption news** to start.")
    st.stop()

df = pd.DataFrame(filtered).sort_values(["confidence","severity"], ascending=False)
st.subheader("Relevant disruption events")
st.dataframe(df.head(20), use_container_width=True)

top = df.iloc[0].to_dict()
alert = {
    "event": top["title"],
    "label": top["label"],
    "severity": top["severity"],
    "confidence": float(top["confidence"]),
    "predicted_delay_days": sev_to_delay(top["severity"]),
    "affected_lane": "ASIA_TO_EU (demo)",
    "source_url": top["link"],
}

st.subheader("Customer relevance + risk scoring")
risk = compute_risk(alert, erp)
st.json({"alert": alert, "risk": risk})

st.subheader("Mitigation options + recommended plan")
options = simulate_options(risk)
chosen = choose_option(risk)

st.table(pd.DataFrame(options))
st.write("**Recommended:**", chosen)

st.subheader("Drafted actions")
st.text_area("Supplier email draft",
             f"Subject: Urgent ETA confirmation\n\nWe detected: {alert['label']} ({alert['severity']}). Please confirm updated ETA and mitigation options.\nLink: {alert['source_url']}",
             height=140)
st.text_area("Exec summary (5 bullets)",
             "\n".join([
                 f"Signal: {alert['label']} severity={alert['severity']} confidence={alert['confidence']}",
                 f"SKU: {risk['sku']} days_to_stockout={risk['days_to_stockout']}",
                 f"Predicted delay days: {alert['predicted_delay_days']}",
                 f"Recommended: {chosen}",
                 "Approval required for high-impact actions."
             ]),
             height=140)

st.subheader("Execution")
if st.session_state.get("approved"):
    st.success("✅ Approved. (Demo) Would trigger PO changes / supplier outreach.")
else:
    st.warning("⏸ Not approved yet. Draft-only mode.")
