from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_MITIGATION_OPTIONS = {"air_freight", "reroute", "allocation_or_buffer"}
VALID_CHOSEN_OPTIONS = REQUIRED_MITIGATION_OPTIONS


def load_latest_output() -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "out" / "latest.json"

    if not out_path.exists():
        raise FileNotFoundError(
            f"Could not find output file at {out_path}. "
            "Run scripts/smoke_run.py first to generate it."
        )

    with out_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_output(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    # Top-level keys
    for key in ["risk_summary", "mitigations", "recommended_plan", "drafted_actions"]:
        if key not in payload:
            errors.append(f"Missing top-level key: {key}")

    if "mitigations" in payload:
        mitigations = payload["mitigations"]
        if not isinstance(mitigations, list):
            errors.append("mitigations must be a list")
        else:
            if len(mitigations) != 3:
                errors.append(f"mitigations must contain exactly 3 entries, got {len(mitigations)}")

            seen_options = {m.get("option") for m in mitigations if isinstance(m, dict)}
            missing_options = REQUIRED_MITIGATION_OPTIONS - seen_options
            extra_options = seen_options - REQUIRED_MITIGATION_OPTIONS
            if missing_options:
                errors.append(f"mitigations missing required options: {sorted(missing_options)}")
            if extra_options:
                errors.append(f"mitigations contains unexpected options: {sorted(extra_options)}")

    if "recommended_plan" in payload:
        rp = payload["recommended_plan"]
        if not isinstance(rp, dict):
            errors.append("recommended_plan must be an object")
        else:
            chosen = rp.get("chosen_option")
            if chosen not in VALID_CHOSEN_OPTIONS:
                errors.append(
                    "recommended_plan.chosen_option must be one of "
                    f"{sorted(VALID_CHOSEN_OPTIONS)}, got {chosen!r}"
                )

    if "drafted_actions" in payload:
        da = payload["drafted_actions"]
        if not isinstance(da, dict):
            errors.append("drafted_actions must be an object")
        else:
            exec_summary = da.get("exec_summary")
            if not isinstance(exec_summary, list):
                errors.append("drafted_actions.exec_summary must be a list of strings")
            else:
                if len(exec_summary) != 5:
                    errors.append(
                        "drafted_actions.exec_summary must contain exactly 5 bullet strings, "
                        f"got {len(exec_summary)}"
                    )

    return errors


def main() -> None:
    try:
        payload = load_latest_output()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    errors = validate_output(payload)

    if errors:
        print("Output validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        raise SystemExit(1)

    print("Output validation PASSED.")


if __name__ == "__main__":
    main()

