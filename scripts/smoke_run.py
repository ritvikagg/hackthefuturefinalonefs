from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def _ensure_google_api_key(repo_root: Path) -> None:
    """Ensure GOOGLE_API_KEY is set, loading it from .env if needed."""
    if os.environ.get("GOOGLE_API_KEY"):
        return

    env_path = repo_root / ".env"
    if not env_path.exists():
        raise RuntimeError(
            "GOOGLE_API_KEY is not set and .env file was not found.\n"
            "Either set the GOOGLE_API_KEY environment variable or add it to .env."
        )

    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("GOOGLE_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    os.environ["GOOGLE_API_KEY"] = value
                    return

    raise RuntimeError(
        "GOOGLE_API_KEY is not set and could not be read from .env.\n"
        "Make sure your .env contains a line like:\n"
        "GOOGLE_API_KEY=your-api-key-here"
    )


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences like ```json ... ``` if present."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence
        lines = stripped.splitlines()
        # Drop first line (``` or ```json)
        if lines:
            lines = lines[1:]
        # If last line is closing fence, drop it
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _append_run_log(
    repo_root: Path,
    agent_module: Any,
    result: Dict[str, Any],
) -> None:
    """
    Append a single run record to logs/runs.jsonl.

    The log is append-only and captures:
    - timestamp
    - alert_used (alert JSON)
    - erp_snapshot_used (ERP snapshot dict)
    - risk_summary (from the model output)
    - chosen_option (from recommended_plan)
    """
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "runs.jsonl"

    try:
        alert_used = agent_module.load_alert()
    except Exception:
        alert_used = None

    try:
        erp_snapshot_used = agent_module.load_erp_snapshot()
    except Exception:
        erp_snapshot_used = None

    risk_summary = result.get("risk_summary")
    recommended_plan = result.get("recommended_plan") or {}
    chosen_option = None
    if isinstance(recommended_plan, dict):
        chosen_option = recommended_plan.get("chosen_option")

    entry: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "alert_used": alert_used,
        "erp_snapshot_used": erp_snapshot_used,
        "risk_summary": risk_summary,
        "chosen_option": chosen_option,
    }

    with log_path.open("a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
        f.write("\n")


def main() -> None:
    """
    Run the supply chain agent with a fixed 'today' date and
    save the final model output to out/latest.json.
    """

    repo_root = Path(__file__).resolve().parents[1]

    # Ensure the Gemini API key is available for google.genai / ADK.
    _ensure_google_api_key(repo_root)

    # Ensure the agent package is importable even when running this script directly.
    supplychain_pkg = repo_root / "supplychain-agent"
    if supplychain_pkg.exists():
        sys.path.insert(0, str(supplychain_pkg))

    try:
        import my_first_agent.agent as agent_module  # type: ignore[import-not-found]
        from my_first_agent import root_agent  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Failed to import root_agent from my_first_agent") from exc

    # Fixed date required by compute_stockout_risk (YYYY-MM-DD).
    today = "2025-01-15"

    print(f"Running agent with today={today}...")

    # Set up an in-memory session and runner, mirroring what `adk run .` does.
    app_name = "supplychain_demo"
    user_id = "smoke_user"
    session_id = "smoke_session"

    session_service = InMemorySessionService()
    session_service.create_session_sync(app_name=app_name, user_id=user_id, session_id=session_id)

    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)

    # Send a single user message telling the agent what today's date is.
    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Today is {today}. Use this as the 'today' date.")],
    )

    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    # Find the final response event and parse its JSON payload.
    final_text: str | None = None
    for event in events:
        if hasattr(event, "is_final_response") and event.is_final_response() and event.content:
            # Assume the agent returns a single text part containing the JSON.
            part = event.content.parts[0]
            if hasattr(part, "text") and part.text:
                final_text = part.text
                break

    if not final_text:
        raise RuntimeError("Did not receive a final JSON response from the agent.")

    try:
        cleaned = _clean_json_text(final_text)
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Agent output was not valid JSON:\n{final_text}") from exc

    out_dir = repo_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Append a memory log entry capturing the inputs and key decision.
    _append_run_log(repo_root=repo_root, agent_module=agent_module, result=result)

    print(f"Wrote agent output to {out_path}")


if __name__ == "__main__":
    main()

