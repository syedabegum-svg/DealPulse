# 🧠 DealPulse — Memory-Powered Deal Intelligence

**HackWithHyderabad 3.0 — AI Agents That Learn Using Hindsight**

DealPulse is a B2B sales deal-intelligence agent that remembers prospect interactions, objections, commitments and outcomes over time. Instead of giving generic sales advice, it uses persistent Hindsight memory to prepare a salesperson using the accumulated history of a deal.

## Why Hindsight is central

DealPulse maps the agent workflow to Hindsight's three core operations:

1. **Retain** — every call, email, objection, commitment and outcome is stored.
2. **Recall** — relevant historical memories are retrieved for a question.
3. **Reflect** — Hindsight reasons over accumulated memories to produce a contextual answer.

This makes the product improve as the deal develops.

## Run locally

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure Hindsight

Copy `.env.example` to `.env` and add your Hindsight Cloud API key.

```text
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=...
HINDSIGHT_BANK_ID=dealpulse-demo
```

### 4. Run

```bash
streamlit run app.py
```

The app also has a local fallback so the UI can be tested without API keys. **For the actual hackathon submission/demo, configure Hindsight Cloud.**

## Judge demo

1. Click **Load demo deal**.
2. Open **Deal Copilot**.
3. Ask: `Prepare me for today's Acme call`.
4. Open **Memory** to show the recalled deal history.
5. Add a new interaction:
   `Acme will only proceed if we can prove six-month ROI.`
6. Ask the same preparation question again.
7. Explain that the second answer can incorporate the new information because the deal's memory is persistent.

## Suggested 3-minute presentation

**Problem:** Sales reps repeatedly reread CRM notes before every call and can miss previous objections and commitments.

**Solution:** DealPulse creates a long-term memory for each deal.

**Memory demo:** Show the five Acme interactions.

**Learning demo:** Add the six-month ROI condition and ask for a new call brief.

**Technology:** React-like product experience via Streamlit, Python, Hindsight Cloud, and optional Groq.

## Project structure

```text
DealPulse/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
└── .streamlit/
```

## Important

Do not commit `.env` or API keys to GitHub.

The app deliberately keeps a local fallback for development. The competition's actual memory demonstration should be performed with Hindsight Cloud connected.
