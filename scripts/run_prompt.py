#!/usr/bin/env python3
"""
Run the supply chain agent with a custom prompt and print the response.
Use this to test specific questions (mitigation, email, escalation, etc.).

Usage (from repo root):
  python scripts/run_prompt.py "What mitigation do you recommend right now and why?"
  python scripts/run_prompt.py "Give me a supplier email and recommended ERP reorder changes for the current risk."

If no argument is given, reads one line from stdin.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def _ensure_google_api_key(repo_root: Path) -> None:
    if os.environ.get("GOOGLE_API_KEY"):
        return
    env_path = repo_root / ".env"
    if not env_path.exists():
        raise RuntimeError(
            "GOOGLE_API_KEY is not set and .env not found. Add GOOGLE_API_KEY to .env in the repo root."
        )
    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GOOGLE_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    os.environ["GOOGLE_API_KEY"] = value
                    return
    raise RuntimeError("GOOGLE_API_KEY not found in .env.")


def _get_final_text(content) -> str:
    """Extract all text from content.parts (agent may return multiple parts)."""
    if not content or not getattr(content, "parts", None):
        return ""
    parts = content.parts
    texts = []
    for part in parts:
        if hasattr(part, "text") and part.text:
            texts.append(part.text)
    return "\n".join(texts).strip()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    _ensure_google_api_key(repo_root)

    supplychain_pkg = repo_root / "supplychain-agent"
    if supplychain_pkg.exists():
        sys.path.insert(0, str(supplychain_pkg))

    try:
        from my_first_agent import root_agent  # type: ignore[import-not-found]
    except Exception as e:
        print(f"Failed to import agent: {e}", file=sys.stderr)
        return 1

    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        print("Enter your prompt (one line):", file=sys.stderr)
        user_prompt = sys.stdin.readline().strip()
        if not user_prompt:
            print("No prompt provided.", file=sys.stderr)
            return 1

    today = "2025-01-15"
    full_message = f"Today is {today}. {user_prompt}"

    app_name = "supplychain_prompt"
    user_id = "prompt_user"
    session_id = "prompt_session"

    session_service = InMemorySessionService()
    session_service.create_session_sync(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)

    content = types.Content(role="user", parts=[types.Part(text=full_message)])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    final_text = None
    for event in events:
        if hasattr(event, "is_final_response") and event.is_final_response() and event.content:
            final_text = _get_final_text(event.content)
            break

    if not final_text:
        print("No final response from the agent.", file=sys.stderr)
        return 1

    print(final_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
