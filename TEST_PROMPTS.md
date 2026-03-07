# Test prompts for the Supply Chain Agent

Use these **exact prompts** with the agent to test mitigation, emails, escalation, and exec summary.

**How to run:** From the project folder, run the script with **python** and the **scripts/** path, and pass the prompt in quotes:

```powershell
cd "c:\Users\ritvi\Desktop\UNI\hackthefuturefinalonefs-main"
python scripts/run_prompt.py "PASTE_PROMPT_HERE"
```

You must use `python scripts/run_prompt.py` — not just `run_prompt.py` (Windows won’t find it).

---

## 1. Mitigation recommendation

**Prompt:**
```
What mitigation do you recommend right now and why?
```

**What to check:** Clear recommendation (air_freight / reroute / allocation_or_buffer) with reasoning tied to the current alert and customer profile.

---

## 2. Supplier email and ERP reorder changes

**Prompt:**
```
Give me a supplier email and recommended ERP reorder changes for the current risk.
```

**What to check:** A ready-to-send supplier email (subject + body) and concrete ERP reorder suggestions (e.g. quantity, dates, safety stock).

---

## 3. Executive escalation

**Prompt:**
```
Should we escalate to exec? If yes, what should the package say?
```

**What to check:** Yes/no with reasoning (e.g. SLA breach probability vs threshold, lane criticality), and if yes, a short escalation package (bullets or paragraph) for leadership.

---

## 4. Revenue-at-risk and actions summary

**Prompt:**
```
Summarize revenue-at-risk and suggested actions in one paragraph.
```

**What to check:** One concise paragraph covering exposure (revenue/operational risk) and the main recommended actions.

---

## 5. Expedited freight vs reroute for highest-risk lane

**Prompt:**
```
Should we trigger expedited freight or reroute for the highest-risk lane?
```

**What to check:** A clear choice (expedited freight vs reroute) with reasoning based on the current lane, SKU, and risk.

---

## 6. Exec summary for disruption score

**Prompt:**
```
Write a short exec summary for the current disruption score.
```

**What to check:** Short exec summary (e.g. 5 bullets or one short paragraph) with disruption score/impact and key actions.

---

## Copy-paste list (no descriptions)

Use these in:

`python scripts/run_prompt.py "…"`

1. `What mitigation do you recommend right now and why?`
2. `Give me a supplier email and recommended ERP reorder changes for the current risk.`
3. `Should we escalate to exec? If yes, what should the package say?`
4. `Summarize revenue-at-risk and suggested actions in one paragraph.`
5. `Should we trigger expedited freight or reroute for the highest-risk lane?`
6. `Write a short exec summary for the current disruption score.`

---

## Full JSON output (unchanged behavior)

To get the **full structured JSON** (same as `smoke_run.py`), use a date-only or “full analysis” message. Example:

```powershell
python scripts/run_prompt.py "Use this as the today date."
```

Or keep using the smoke run:

```powershell
python scripts/smoke_run.py
```

Then check `out/latest.json` and run `python scripts/validate_output.py`.
