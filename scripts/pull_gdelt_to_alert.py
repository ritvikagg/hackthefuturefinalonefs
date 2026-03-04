from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request


def _read_env_var(repo_root: Path, name: str) -> Optional[str]:
    """
    Read an environment variable, falling back to the local .env file.

    This mirrors the simple .env handling pattern used elsewhere in the repo,
    but keeps the logic self-contained in this script.
    """
    if os.environ.get(name):
        return os.environ[name]

    env_path = repo_root / ".env"
    if not env_path.exists():
        return None

    try:
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith(f"{name}="):
                    continue
                return line.split("=", 1)[1].strip()
    except OSError:
        return None

    return None


def _fetch_top_supply_chain_article(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Query NewsData for the most recent supply-chain disruption headline.

    We intentionally keep this logic simple and robust:
    - Use a broad query for supply chain / port / shipping disruptions.
    - Return the first result if available.
    - Swallow network / API errors and let the caller decide how to handle them.
    """
    # Keep the request shape as close as possible to the working
    # browser example you tried: just apikey + q.
    query_params = {
        "apikey": api_key,
        "q": "supply chain OR port congestion OR shipping delay OR logistics disruption",
    }

    url = "https://newsdata.io/api/1/latest?" + urlencode(query_params)
    req = Request(url, headers={"User-Agent": "supplychain-demo/1.0"})

    try:
        with urlopen(req, timeout=10) as resp:
            # Some Python versions don't expose .status, so fall back to getcode().
            status = getattr(resp, "status", resp.getcode())
            if status != 200:
                print(f"NewsData HTTP error status={status}", file=sys.stderr)
                return None
            data = json.load(resp)
    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        print(f"NewsData request failed: {exc!r}", file=sys.stderr)
        return None

    # NewsData typically returns a "results" list containing article objects.
    results = data.get("results")
    if not isinstance(results, list) or not results:
        return None

    return results[0]


def _article_to_alert(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a NewsData article into our alert.json schema:
    {event, predicted_delay_days, affected_lane, confidence}.

    The mapping is intentionally heuristic but stable so the agent prompt
    does not need to change.
    """
    title = article.get("title") or ""
    description = article.get("description") or ""

    text = f"{title}. {description}".strip()
    if not text:
        text = "Supply chain disruption detected."

    # Very simple heuristic for delay days – could be refined later.
    predicted_delay_days = 7

    countries = article.get("country") or []
    if isinstance(countries, str):
        countries = [countries]
    if isinstance(countries, list) and countries:
        affected_lane = " / ".join(str(c).upper() for c in countries)
    else:
        affected_lane = "Global supply chain"

    # Fixed confidence for now; can be tuned based on metadata later.
    confidence = 0.8

    return {
        "event": text,
        "predicted_delay_days": predicted_delay_days,
        "affected_lane": affected_lane,
        "confidence": confidence,
    }


def main() -> None:
    """
    Fetch the latest supply-chain disruption and write it to alert.json.

    - If NEWSDATA_API_KEY is missing or the API request fails, we keep
      the existing alert.json untouched so the demo never breaks.
    """
    repo_root = Path(__file__).resolve().parents[1]
    alert_path = repo_root / "supplychain-agent" / "my_first_agent" / "alert.json"

    # Load the existing alert so we can keep it on failure.
    last_alert: Optional[Dict[str, Any]] = None
    if alert_path.exists():
        try:
            with alert_path.open("r", encoding="utf-8") as f:
                last_alert = json.load(f)
        except Exception:
            last_alert = None

    api_key = _read_env_var(repo_root, "NEWSDATA_API_KEY")
    if not api_key:
        print(
            "NEWSDATA_API_KEY is not set in the environment or .env; "
            "keeping existing alert.json.",
            file=sys.stderr,
        )
        return

    article = _fetch_top_supply_chain_article(api_key)
    if not article:
        print(
            "Failed to fetch a supply-chain article from NewsData; "
            "keeping existing alert.json.",
            file=sys.stderr,
        )
        return

    alert = _article_to_alert(article)

    try:
        alert_path.parent.mkdir(parents=True, exist_ok=True)
        with alert_path.open("w", encoding="utf-8") as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)
        print(f"Wrote updated alert to {alert_path}")
    except Exception as exc:
        print(f"ERROR: Failed to write alert.json: {exc}", file=sys.stderr)
        # Best effort only: if writing fails, there's nothing else to do here.


if __name__ == "__main__":
    main()

