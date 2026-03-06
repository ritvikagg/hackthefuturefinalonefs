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


def load_customer_profile(path: str = "data/customer_profile.json") -> Dict[str, Any]:
    """Load a customer profile JSON containing lanes, critical SKUs, SLA, and risk appetite."""
    # data/ lives at the repo root (two levels above this file).
    repo_root = HERE.parent.parent
    p = repo_root / path
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
        "You MUST always run this workflow first:\n"
        "1) Call load_erp_snapshot\n"
        "2) Call load_alert\n"
        "3) Call load_customer_profile\n"
        "4) Call compute_stockout_risk using the ERP values and the alert's predicted_delay_days, "
        "and the 'today' date provided by the user.\n"
        "\n"
        "RESPONSE MODE:\n"
        "- If the user message contains ONLY the date (e.g. 'Today is 2025-01-15. Use this as the today date.') or explicitly asks for 'full analysis' or 'full JSON output', then your reply MUST be ONLY the full JSON object described below (no markdown, no code fences).\n"
        "- If the user asks a SPECIFIC QUESTION (e.g. mitigation recommendation, supplier email, ERP reorder changes, escalation, revenue-at-risk summary, expedited freight vs reroute, exec summary), then answer that question clearly in natural language or the requested format (e.g. write the email, write the paragraph, give the escalation package). Do not output the full JSON in that case—just answer the question using the data from your tool calls.\n"
        "\n"
        "Use the customer profile to personalize your reasoning:\n"
        "- lanes: strings that represent the customer's lanes/routes and should be compared to the alert's affected_lane.\n"
        "- critical_skus: SKUs that are especially important for the customer.\n"
        "- sla_breach_probability_threshold: acceptable sla_breach_probability for this customer.\n"
        "- risk_appetite: object with cost_weight and service_weight that should guide trade-offs between cost and service.\n"
        "\n"
        "If the alert's affected_lane is NOT in the customer profile lanes, you MUST:\n"
        "- treat the disruption as lower priority in risk_summary.why_it_matters,\n"
        "- set recommended_plan.chosen_option to \"allocation_or_buffer\",\n"
        "- and explain in risk_summary.why_it_matters that you are monitoring or using allocation/buffer because the lane is outside the customer's primary lanes.\n"
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
        "- You MUST use load_customer_profile() in your reasoning about the SLA breach probability, which SKUs and lanes matter most, and which mitigation to recommend.\n"
        "\n"
        "Human-in-the-loop approval:\n"
        "- Consider a disruption HIGH-IMPACT if either compute_stockout_risk().gap_days > 0 OR compute_stockout_risk().sla_breach_probability is greater than customer_profile.sla_breach_probability_threshold.\n"
        "- For every HIGH-IMPACT case, you MUST include as the FIRST item in recommended_plan.steps the exact string: \"Require human approval before sending emails / executing changes.\".\n"
        "- For non high-impact cases you MUST NOT include that human-approval step.\n"
    ),
    tools=[load_erp_snapshot, load_alert, load_customer_profile, compute_stockout_risk],
)