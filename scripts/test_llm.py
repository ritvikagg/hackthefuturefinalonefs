#!/usr/bin/env python3
"""
One-command test for the supply chain LLM agent: run the agent, then validate output.
Usage (from repo root):
  python scripts/test_llm.py
  python scripts/test_llm.py --today 2025-02-01
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run agent smoke test then validate output.")
    parser.add_argument(
        "--today",
        default="2025-01-15",
        help="Date to pass to the agent as 'today' (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    # Smoke run currently uses a fixed today in the script; we could extend smoke_run to accept it.
    # For now, just run smoke_run then validate.
    print("Step 1: Running agent (smoke_run.py)...")
    r = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "smoke_run.py")],
        cwd=str(repo_root),
    )
    if r.returncode != 0:
        print("Smoke run FAILED.", file=sys.stderr)
        return r.returncode

    print("Step 2: Validating output...")
    r2 = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_output.py")],
        cwd=str(repo_root),
    )
    if r2.returncode != 0:
        print("Validation FAILED.", file=sys.stderr)
        return r2.returncode

    print("\nLLM test PASSED: agent ran and output is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
