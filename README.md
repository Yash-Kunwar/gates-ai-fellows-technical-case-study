# Gates Foundation AI Fellows Program — Technical Case Study
**Candidate:** Yash Kunwar  
**Assignment:** Install, assess, and build on the CeRAI AI Evaluation Tool

---

### Path Chosen: Option B - Critique & Rebuild

I initially set out to evaluate the endpoint (Option A). However, after successfully installing the CeRAI tool, I determined it was fundamentally limited: the scoring pipeline was non-functional (producing no numeric scores), and the tool's logic incorrectly conflates "no response" with failure in safety contexts. Following Option B, I systematically documented these infrastructure bugs and implemented a custom LLM-as-judge evaluator as a minimal viable alternative to successfully generate the maternal health evaluation output. The full critique and alternative are documented in the live report.

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
- **CeRAI Bug 2:** `docker-compose.yml` missing volume mount for `strategy/.env` in app-backend
- **CeRAI Finding:** Tool conflates "no response" with failure — incorrect in safety evaluation contexts
- **CeRAI Finding:** Scoring pipeline non-functional — COMPLETED status does not mean scored
- **Gemini Finding:** 503 errors during peak demand are a deployment blocker for LMIC health contexts
- **Gemini Result:** Perfect scores on Safety (1.0), Bias (1.0), Cultural Sensitivity (1.0), Guardrails (1.0). Truthfulness 0.667 due to service unavailability, not factual failure.

---

## AI Use
Claude Sonnet 4.6 was used for debugging assistance and documentation. All domain decisions, test case design, and analytical framing were my own.
