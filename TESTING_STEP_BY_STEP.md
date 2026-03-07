# How to Test the Supply Chain Agent — Step by Step

Follow these steps in order. All commands are run from the **project folder**  
`hackthefuturefinalonefs-main` (the folder that contains `supplychain-agent`, `scripts`, and `data`).

---

## Step 1: Open a terminal in the project folder

1. Open your terminal (PowerShell or Command Prompt).
2. Go to the project folder:
   ```powershell
   cd "c:\Users\ritvi\Desktop\UNI\hackthefuturefinalonefs-main"
   ```
3. Check you’re in the right place — you should see folders like `supplychain-agent`, `scripts`, `data`:
   ```powershell
   dir
   ```

---

## Step 2: Make sure Python and the API key are set up

1. **Check Python** (you need 3.10 or newer):
   ```powershell
   python --version
   ```

2. **Check your API key**  
   The agent uses Google’s Gemini API. You need a key in one of these ways:
   - **Option A:** A file named `.env` in the project folder (same folder as `supplychain-agent`) with a line like:
     ```
     GOOGLE_API_KEY=your-actual-key-here
     ```
   - **Option B:** The environment variable `GOOGLE_API_KEY` set in your terminal.

   You already have a `.env` file; just make sure that line is there and the key is valid.

3. **Install dependencies** (only needed once):
   ```powershell
   pip install google-adk google-genai
   ```

---

## Step 3: Run the agent (smoke test)

This step runs your LLM agent with the current alert, ERP data, and customer profile.

1. From the project folder, run:
   ```powershell
   python scripts/smoke_run.py
   ```

2. **What to expect:**
   - It may take 20–60 seconds (it calls the Gemini API).
   - You might see a deprecation warning; you can ignore it.
   - At the end you should see:
     ```
     Running agent with today=2025-01-15...
     Wrote agent output to ...\out\latest.json
     ```

3. **If something goes wrong:**
   - **"GOOGLE_API_KEY is not set"** → Add or fix the key in `.env` (see Step 2).
   - **"Failed to import root_agent"** → Make sure you ran the command from the project folder (the one that contains `supplychain-agent`).
   - **"Did not receive a final JSON response"** → The model might have timed out or returned something unexpected; try running again.

---

## Step 4: Check that the output is valid (validation)

The agent writes its answer to `out/latest.json`. This step checks that the file has the right structure and content.

1. Run:
   ```powershell
   python scripts/validate_output.py
   ```

2. **What to expect:**
   - If everything is correct:
     ```
     Output validation PASSED.
     ```
   - If something is wrong, you’ll see a list of errors (e.g. missing key, wrong number of mitigations).

3. **If validation fails:**  
   Fix the issue (e.g. adjust the agent’s instructions or the data in `alert.json` / `customer_profile.json`), then run **Step 3** again, then **Step 4** again.

---

## Step 5: Look at the agent’s output (optional but useful)

1. Open the file:
   ```
   out/latest.json
   ```
   (Same folder as `supplychain-agent`; there is an `out` folder with `latest.json` inside.)

2. **What’s in there:**
   - **risk_summary** — Which SKU, stockout date, delay, and why it matters.
   - **mitigations** — Three options: air_freight, reroute, allocation_or_buffer.
   - **recommended_plan** — Which option the agent chose and the steps (including “human approval” when needed).
   - **drafted_actions** — Example supplier email, logistics email, and a 5-bullet exec summary.

This is how you “see” what the LLM decided.

---

## Step 6: Run both steps in one command (shortcut)

After you’re comfortable with Steps 3 and 4, you can do both in one go:

```powershell
python scripts/test_llm.py
```

- This runs `smoke_run.py` and then `validate_output.py`.
- If both succeed, you’ll see: **LLM test PASSED**.

---

## Step 7: Test different scenarios (optional)

To see how the agent behaves in different situations, change the input data and run Step 3 (and then Step 4) again.

| What you want to test | What to change | Where |
|-----------------------|----------------|--------|
| Stronger disruption | Increase `predicted_delay_days` or change `affected_lane` | `supplychain-agent/my_first_agent/alert.json` |
| Different customer lanes | Add or remove lanes (e.g. add `"UNITED STATES OF AMERICA"`) | `data/customer_profile.json` → `lanes` |
| Stricter SLA | Lower `sla_breach_probability_threshold` (e.g. `0.3`) | `data/customer_profile.json` |
| Less stock / more demand | Change `on_hand`, `daily_demand`, or `inbound_eta` | `supplychain-agent/my_first_agent/erp_snapshot.csv` |

After editing, run:

```powershell
python scripts/smoke_run.py
python scripts/validate_output.py
```

(or `python scripts/test_llm.py`) and then look at `out/latest.json` again to see how the recommendation changed.

---

## Quick reference — order of steps

1. Open terminal → `cd` to project folder.  
2. Check Python and `.env` (API key); install `google-adk` and `google-genai` if needed.  
3. Run: `python scripts/smoke_run.py` → expect “Wrote agent output to ...\out\latest.json”.  
4. Run: `python scripts/validate_output.py` → expect “Output validation PASSED.”  
5. Open `out/latest.json` to read the agent’s decision.  
6. (Optional) Use `python scripts/test_llm.py` to do step 3 + 4 in one command.  
7. (Optional) Change `alert.json`, `customer_profile.json`, or `erp_snapshot.csv` and repeat 3–5 to test different scenarios.

That’s the full step-by-step process to test your agent.
