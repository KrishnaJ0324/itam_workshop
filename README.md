# ReadyOps ITAM Agent
### AI-Powered IT Asset Management  ·  Criterion Networks  ·  Cisco Live 2026

---

## Two Ways to Use This

### Option A — AI Agent (recommended for demos)
Ask questions in plain English. Get instant reports. No coding.

### Option B — Run All Scripts
Generate all 4 reports with one command. Good for batch output.

---

## Option A — AI Agent Setup

### Step 1 — Install dependencies (one time only)
```
pip install -r requirements.txt
```

### Step 2 — Add your API key
```
cp .env.example .env
```
Open `.env` and replace `your_openrouter_api_key_here` with your key from https://openrouter.ai/keys

### Step 3 — Start the agent
```
python agent.py
```

### Step 4 — Open your browser
```
http://localhost:7860
```

That's it. Ask anything.

---

## Example Questions

| What you ask | What you get |
|---|---|
| List all publishers with ACV and TCV | Full publisher portfolio table |
| Which contracts expire in 90 days? | Flagged renewal list with owners |
| Which titles are under 40% utilisation? | Cut candidates sorted by cost |
| Who owns the Workday contract? | Owner + stakeholders instantly |
| Give me a VP briefing note | Executive summary ready to send |
| Which P1 incidents are still open? | Open ticket list with context |

---

## Option B — Run All Scripts

```
python run_all.py
```

Reports appear in `output/` — no browser needed.

---

## Repository Structure

```
readyops-itam-demo/
├── agent.py              <- AI agent with Gradio UI  <- START HERE
├── run_all.py            <- batch run all 4 reports
├── requirements.txt      <- Python dependencies
├── .env.example          <- copy this to .env and add your key
├── data/
│   ├── cisco_publishers.csv     <- 35 publishers
│   ├── software_licenses.csv    <- 25 software titles
│   └── it_incidents.csv         <- 50 IT incidents
├── scripts/              <- individual report scripts
└── output/               <- generated reports appear here
```

---

## Key Numbers

| Metric | Value |
|---|---|
| Publishers tracked | 35 |
| Total ACV portfolio | $27,000,000 |
| Total TCV | $92,000,000 |
| Software titles | 25 |
| Unused license savings | $1,793,000 |
| P1 incidents | 23 |
| Repeat incident rate | 66% |
| SLA breach rate | 65% |

---

Criterion Networks  |  ReadyOps Agentic-AI Platform  |  Powered by Claude via OpenRouter
