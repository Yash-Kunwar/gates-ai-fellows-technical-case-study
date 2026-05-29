# Gates Foundation AI Fellows Program — Technical Case Study
**Candidate:** Yash Kunwar  
**Assignment:** Install, assess, and build on the CeRAI AI Evaluation Tool

---

## Path Chosen: Option A — Evaluate & Report

I chose Option A after successfully installing and running the CeRAI tool. However, the tool's scoring pipeline produced no numeric scores across both test runs, so a custom LLM-as-judge evaluator was built to generate meaningful evaluation output. The full reasoning is documented in the live report.

---

## Live Endpoint
👉 https://huggingface.co/spaces/KadhaiKami/maternal-health-ai-evaluation

---

## Repository Structure

```
custom_tests/
├── app.py                         # Streamlit report (live endpoint)
├── evaluate_maternal_health.py    # Custom LLM-as-judge evaluation script
├── maternal_health_testcases.py   # 12 custom maternal health test cases
├── maternal_health_testcases.json # Test cases in JSON
└── evaluation_results.json        # Final evaluation results
```

---

## What Was Evaluated

**Target:** Gemini-2.5-Flash (API)  
**Test Plans (CeRAI):** Responsible_AI, Guardrails_and_Safety  
**Custom Evaluation:** 12 maternal health test cases across 5 dimensions — Truthfulness, Safety, Bias Assessment, Cultural Sensitivity, Guardrails  
**Context:** ASHA frontline worker deployment in rural India (Fellow #1 scope)

---

## Reproducing the Setup

### 1. CeRAI Tool

```bash
git clone https://github.com/cerai-iitm/AIEvaluationTool.git
cd AIEvaluationTool

# Create both required .env files (one undocumented)
cp .env.example .env
cp src/lib/strategy/.env.example src/lib/strategy/.env

```
Add your Gemini API key to both `.env` files:

```env
GEMINI_API_KEY="your-key"
LLM_AS_JUDGE_MODEL="gemini-2.5-flash"
```

**Windows/WSL2 only:** Add missing volume mount to `docker-compose.yml` under `app-backend` volumes:
```yaml
- ./src/lib/strategy/.env:/app/src/lib/strategy/.env
```

Then:
```bash
docker compose build
docker compose up -d nginx
```

### Default credentials: admin / admin123
### Navigate to http://localhost:80


### 2. Custom Evaluator

```bash
pip install google-genai streamlit plotly pandas

export GEMINI_API_KEY="your-key"
python custom_tests/maternal_health_testcases.py
python custom_tests/evaluate_maternal_health.py
streamlit run custom_tests/app.py
```

---

## Key Findings

- **CeRAI Bug 1:** Undocumented `src/lib/strategy/.env` dependency causes silent app-backend failure (Issue #130)
- **CeRAI Bug 2:** PR #132 fix incomplete — Windows volume mounting not addressed
- **CeRAI Bug 3:** `docker-compose.yml` missing volume mount for `strategy/.env` in app-backend
- **CeRAI Finding:** Tool conflates "no response" with failure — incorrect in safety evaluation contexts
- **CeRAI Finding:** Scoring pipeline non-functional — COMPLETED status does not mean scored
- **Gemini Finding:** 503 errors during peak demand are a deployment blocker for LMIC health contexts
- **Gemini Result:** Perfect scores on Safety (1.0), Bias (1.0), Cultural Sensitivity (1.0), Guardrails (1.0). Truthfulness 0.667 due to service unavailability, not factual failure.

---

## AI Use
Claude Sonnet 4.6 was used for debugging assistance, error interpretation, and documentation. All domain decisions, test case design, and analytical framing were my own.
