from __future__ import annotations

import csv
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from google.adk.agents.llm_agent import Agent

HERE = Path(__file__).parent


def load_erp_snapshot(path: str = "erp_snapshot.csv") -> Dict[str, Any]:
    """Load a 1-row ERP snapshot CSV for the demo."""
    p = HERE / path
    with p.open("r", newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))

    return {
        "sku": row["sku"],
        "on_hand": float(row["on_hand"]),
        "daily_demand": float(row["daily_demand"]),
        "inbound_qty": float(row["inbound_qty"]),
        "inbound_eta": row["inbound_eta"],
    }


def load_alert(path: str = "alert.json") -> Dict[str, Any]:
    """Load a disruption alert JSON for the demo."""
    p = HERE / path
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_stockout_risk(
    on_hand: float,
    daily_demand: float,
    inbound_eta: str,
    predicted_delay_days: int,
    today: str,
) -> Dict[str, Any]:
    """Compute stockout risk and SLA breach probability (simple heuristic)."""
    today_d = datetime.strptime(today, "%Y-%m-%d").date()
    eta = datetime.strptime(inbound_eta, "%Y-%m-%d").date()
    new_eta = date.fromordinal(eta.toordinal() + int(predicted_delay_days))

    days_to_stockout = on_hand / daily_demand if daily_demand > 0 else 10**9
    stockout_date = date.fromordinal(today_d.toordinal() + math.ceil(days_to_stockout))

    gap_days = (new_eta - stockout_date).days
    inbound_after_stockout = gap_days > 0

    return {
        "today": today_d.isoformat(),
        "days_to_stockout": round(days_to_stockout, 2),
        "projected_stockout_date": stockout_date.isoformat(),
        "original_inbound_eta": eta.isoformat(),
        "new_inbound_eta": new_eta.isoformat(),
        "inbound_after_stockout": inbound_after_stockout,
        "gap_days": int(gap_days) if inbound_after_stockout else 0,
        "sla_breach_probability": 0.7 if inbound_after_stockout else 0.15,
    }


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Supply chain resilience agent (demo).",
    instruction=(
        "You are a supply chain resilience agent.\n"
        "You MUST follow this workflow strictly:\n"
        "1) Call load_erp_snapshot\n"
        "2) Call load_alert\n"
        "3) Call compute_stockout_risk using the ERP values and the alert's predicted_delay_days, "
        "and the 'today' date provided by the user.\n"
        "\n"
        "Output MUST be ONLY valid JSON (no markdown, no code fences) with this exact schema:\n"
        "{\n"
        '  "risk_summary": {\n'
        '    "sku": "MCU-17",\n'
        '    "today": "YYYY-MM-DD",\n'
        '    "days_to_stockout": 0,\n'
        '    "projected_stockout_date": "YYYY-MM-DD",\n'
        '    "original_inbound_eta": "YYYY-MM-DD",\n'
        '    "new_inbound_eta": "YYYY-MM-DD",\n'
        '    "gap_days": 0,\n'
        '    "sla_breach_probability": 0,\n'
        '    "why_it_matters": "string"\n'
        "  },\n"
        '  "mitigations": [\n'
        "    {\n"
        '      "option": "air_freight",\n'
        '      "why": "string",\n'
        '      "estimated_cost_impact": "string",\n'
        '      "estimated_service_impact": "string"\n'
        "    }\n"
        "  ],\n"
        '  "recommended_plan": {\n'
        '    "chosen_option": "air_freight",\n'
        '    "steps": ["string", "string", "string"],\n'
        '    "decision_rationale": "string"\n'
        "  },\n"
        '  "drafted_actions": {\n'
        '    "supplier_email": "string",\n'
        '    "logistics_email": "string",\n'
        '    "exec_summary": ["b1", "b2", "b3", "b4", "b5"]\n'
        "  }\n"
        "}\n"
        "\n"
        "Constraints:\n"
        "- mitigations must contain EXACTLY 3 objects (one per option): air_freight, reroute, allocation_or_buffer.\n"
        "- recommended_plan.chosen_option MUST be one of: air_freight, reroute, allocation_or_buffer.\n"
        "- drafted_actions.exec_summary must contain EXACTLY 5 bullet strings.\n"
        "- risk_summary.sku MUST equal load_erp_snapshot().sku.\n"
        "- All dates and numbers must match compute_stockout_risk output.\n"
    ),
    tools=[load_erp_snapshot, load_alert, compute_stockout_risk],
)