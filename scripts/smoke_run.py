from __future__ import annotations

import json
import sys
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def main() -> None:
    """
    Run the supply chain agent with a fixed 'today' date and
    save the final model output to out/latest.json.
    """

    repo_root = Path(__file__).resolve().parents[1]

    # Ensure the agent package is importable even when running this script directly.
    supplychain_pkg = repo_root / "supplychain-agent"
    if supplychain_pkg.exists():
        sys.path.insert(0, str(supplychain_pkg))

    try:
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
        result = json.loads(final_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Agent output was not valid JSON:\n{final_text}") from exc

    out_dir = repo_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote agent output to {out_path}")


if __name__ == "__main__":
    main()

