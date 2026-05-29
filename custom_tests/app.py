import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Maternal Health AI Evaluation",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main { max-width: 1100px; }
    .block-container { padding-top: 2rem; }
    h1 { font-size: 1.4rem; font-weight: 600; }
    h2 { font-size: 1.1rem; font-weight: 600; border-bottom: 1px solid #333; padding-bottom: 4px; }
    h3 { font-size: 0.95rem; font-weight: 600; }
    .stMetric label { font-size: 0.75rem; color: #888; }
    .stMetric [data-testid="metric-container"] { background: #111; padding: 12px; border-radius: 4px; border: 1px solid #222; }
    code { font-size: 0.8rem; }
    .finding-box { background: #111; border-left: 3px solid #444; padding: 10px 14px; margin: 6px 0; border-radius: 2px; font-size: 0.85rem; }
    .critical { border-left-color: #e05252; }
    .pass { border-left-color: #52e052; }
    .warn { border-left-color: #e0b452; }
    hr { border-color: #222; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_results():
    p = Path("custom_tests/evaluation_results.json")
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


data = load_results()

if not data:
    st.error("evaluation_results.json not found. Run evaluate_maternal_health.py first.")
    st.stop()

results = data["results"]
meta = data["evaluation_metadata"]
metric_avgs = data["metric_averages"]
infra = data["infrastructure_findings"]

st.markdown("# Maternal Health AI Evaluation Report")
st.markdown(f"`target: {meta['target_model']}` &nbsp;|&nbsp; `judge: {meta['judge_model']}` &nbsp;|&nbsp; `{meta['timestamp'][:10]}`")
st.markdown(f"*{meta['context']}*")
st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Overall Score", f"{data['overall_score']:.3f}")
col2.metric("Test Cases", meta["total_test_cases"])
col3.metric("Scored", meta["scored_cases"])
col4.metric("Unscored", meta["failed_cases"])
col5.metric("Critical Issues", data["critical_issues_count"])

st.divider()

st.markdown("## Scores by Metric")

metrics = {k: v for k, v in metric_avgs.items() if v != "not_scored"}
not_scored = [k for k, v in metric_avgs.items() if v == "not_scored"]

fig = go.Figure(go.Bar(
    x=list(metrics.keys()),
    y=list(metrics.values()),
    marker_color=["#52e052" if v == 1.0 else "#e0b452" if v >= 0.5 else "#e05252" for v in metrics.values()],
    text=[f"{v:.3f}" for v in metrics.values()],
    textposition="outside",
    width=0.4
))
fig.update_layout(
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    font_color="#ccc",
    yaxis=dict(range=[0, 1.15], gridcolor="#222", tickformat=".1f"),
    xaxis=dict(gridcolor="#222"),
    height=300,
    margin=dict(t=20, b=20, l=20, r=20),
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

if not_scored:
    st.caption(f"⚠ Not scored (quota exhausted): {', '.join(not_scored)}")

st.divider()

st.markdown("## Infrastructure Findings")

c1, c2 = st.columns(2)
c1.markdown(f"""
<div class="finding-box critical">
<strong>Quota Exhaustion</strong><br>
{infra['quota_exhaustion_count']} test cases failed due to Gemini free-tier RPD limit (20/day).
A 12-case suite requires at least 24 API calls (agent + judge). Free tier is structurally insufficient.
</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="finding-box warn">
<strong>Service Unavailability (503)</strong><br>
{infra['service_unavailability_count']} cases returned 503 during peak demand.
For LMIC frontline health workers, model unavailability during emergencies is a patient safety risk.
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="finding-box warn">
<strong>LMIC Deployment Implication</strong><br>
{infra['finding']}
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("## Test Case Results")

df = pd.DataFrame([{
    "ID": r["id"],
    "Metric": r["metric"],
    "Dimension": r["dimension"],
    "Score": r["score"] if r["score"] is not None else None,
    "Critical": "🔴" if r.get("critical_issue") else "✅",
    "Status": "SCORED" if r["score"] is not None else "UNSCORED"
} for r in results])

st.dataframe(
    df,
    use_container_width=True,
    height=420,
    column_config={
        "Score": st.column_config.NumberColumn(format="%.3f"),
    }
)

st.divider()

st.markdown("## Case Detail Viewer")

case_ids = [r["id"] for r in results]
selected = st.selectbox("Select test case", case_ids)

case = next(r for r in results if r["id"] == selected)

col_a, col_b = st.columns([1, 2])

with col_a:
    st.markdown(f"**ID:** `{case['id']}`")
    st.markdown(f"**Metric:** `{case['metric']}`")
    st.markdown(f"**Dimension:** {case['dimension']}")
    score_display = f"{case['score']:.3f}" if case['score'] is not None else "UNSCORED"
    st.markdown(f"**Score:** `{score_display}`")
    st.markdown(f"**LMIC Relevance:** {case['lmic_relevance']}")

with col_b:
    st.markdown("**User Prompt**")
    st.code(case["user_prompt"], language=None)

    st.markdown("**Expected Behavior**")
    st.code(case["expected_behavior"], language=None)

    st.markdown("**Agent Response**")
    response_text = case["agent_response"]
    if response_text.startswith("ERROR"):
        st.error(response_text)
    else:
        st.text_area("", response_text, height=150, disabled=True, label_visibility="collapsed")

    if case["reasoning"]:
        st.markdown("**Judge Reasoning**")
        box_class = "critical" if case.get("critical_issue") else "pass"
        st.markdown(f'<div class="finding-box {box_class}">{case["reasoning"]}</div>', unsafe_allow_html=True)

    if case.get("recommendation") and case["recommendation"] != "No improvements needed.":
        st.markdown(f"**Recommendation:** {case['recommendation']}")

st.divider()

st.markdown("## CeRAI Tool Assessment")

st.markdown("""
<div class="finding-box warn">
<strong>About the CeRAI AI Evaluation Tool</strong><br>
Open-source framework developed at IIT Madras for automated evaluation of conversational AI systems.
Evaluates endpoints via structured text inputs against quality metrics covering accuracy, safety, and user experience.
Supports API endpoints, WhatsApp bots, and web-based interfaces. Version 2.0 released April 21, 2026.
</div>
""", unsafe_allow_html=True)

st.markdown("### Bugs Encountered and Fixed")

st.markdown("""
<div class="finding-box critical">
<strong>Bug 1 — Undocumented Second .env File (src/lib/strategy/.env)</strong><br>
<strong>What happened:</strong> Following the README setup instructions exactly
(<code>cp .env.example .env</code>) caused <code>app-backend</code> to fail silently on startup.
The container health check failed repeatedly with:<br>
<code>[ERROR] Could not find the .env file at path: /app/src/lib/strategy/.env</code><br><br>
<strong>Root cause:</strong> The tool ships two <code>.env.example</code> files — one at root and one at
<code>src/lib/strategy/</code> — but the documentation only mentions the root copy command.
The strategy layer requires its own environment file for LLM judge configuration.<br><br>
<strong>Fix applied:</strong> <code>cp src/lib/strategy/.env.example src/lib/strategy/.env</code><br>
<strong>Status:</strong> Reported as GitHub Issue #130. PR #132 was opened but not yet merged at time of evaluation.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="finding-box critical">
<strong>Bug 2 — PR #132 Fix Incomplete: Windows Volume Mounting Not Addressed</strong><br>
<strong>What happened:</strong> Even after creating <code>src/lib/strategy/.env</code> on the host machine,
<code>app-backend</code> continued to fail with the same error on Windows.<br><br>
<strong>Root cause:</strong> PR #132 fixed the documentation but did not address the
<code>docker-compose.yml</code> volume mount. On Windows/WSL2, the file exists on the host
but Docker cannot see it because the compose file never mounts it into the container.
The PR was tested only on macOS (Apple M4 Pro) where file sharing behavior differs.<br><br>
<strong>Fix applied:</strong> Manually added the missing volume mount to the <code>app-backend</code>
service in <code>docker-compose.yml</code>:<br>
<code>- ./src/lib/strategy/.env:/app/src/lib/strategy/.env</code><br>
<strong>Status:</strong> Unreported upstream. Windows-specific gap in PR #132.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="finding-box critical">
<strong>Bug 3 — docker-compose.yml Missing Volume Mount for strategy/.env in app-backend</strong><br>
<strong>What happened:</strong> The <code>app-backend</code> service definition in
<code>docker-compose.yml</code> only mounts two volumes —
<code>interface_manager_logs</code> and <code>config.json</code>.
The <code>src/lib/strategy/.env</code> file is never declared as a volume mount,
meaning the container cannot access it regardless of whether it exists on the host.<br><br>
<strong>Root cause:</strong> Architectural oversight — the strategy layer's configuration
was not included in the container's volume definitions.<br><br>
<strong>Fix applied:</strong> Added explicit volume mount to <code>docker-compose.yml</code> app-backend service.
This is the same fix as Bug 2 but a distinct root cause — one is a docs gap, the other is a compose configuration gap.
</div>
""", unsafe_allow_html=True)

st.markdown("### Additional Findings")

st.markdown("""
<div class="finding-box critical">
<strong>Finding 1 — CeRAI Conflates "No Response" with Failure in Safety Contexts</strong><br>
During the Guardrails_and_Safety test run, test case P1251 (Toxicity_Level) was marked FAILED.
The user prompt contained a racial slur. The model correctly refused to engage and returned no response.<br><br>
In responsible AI evaluation, <strong>refusing to respond to toxic input IS the correct behavior.</strong>
The tool has no mechanism to distinguish between a model that failed to respond due to an error
and a model that correctly declined a harmful request. This is a fundamental evaluation logic gap
for any safety-focused assessment framework. A responsible AI evaluation tool must treat
guardrail activations as PASS conditions, not failures.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="finding-box critical">
<strong>Finding 2 — 503 Errors as a Deployment Risk for LMIC Health Contexts</strong><br>
During evaluation runs, 3 test cases returned HTTP 503 (Service Unavailable) due to peak demand
on the Gemini API. In a general consumer context this is a minor inconvenience.
In LMIC maternal health deployment contexts, it is a patient safety risk.<br><br>
Consider the scenario: an ASHA worker queries a maternal health chatbot about a woman
presenting with severe headache and blurred vision at 8 months — signs of eclampsia.
A 503 error at that moment means no response reaches the worker.
Delayed recognition of eclampsia is a leading cause of preventable maternal death.<br><br>
<strong>Any AI system deployed for frontline health decision support in LMICs must have
a documented reliability SLA, fallback mechanisms, and offline capability.</strong>
Free-tier API access is structurally incompatible with this requirement.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="finding-box warn">
<strong>Finding 3 — Scoring Pipeline Produces No Numeric Scores</strong><br>
Across both CeRAI test runs (Responsible_AI and Guardrails_and_Safety), all test cases
that reached COMPLETED status showed "-" in the Score column. The LLM-as-judge layer
executed but failed to return parseable numeric scores to the database.<br><br>
This means the tool completed API calls and stored conversations, but its core evaluation
output — quantitative scoring — is non-functional in the current version.
The COMPLETED status reflects successful request execution, not successful evaluation.
</div>
""", unsafe_allow_html=True)

st.markdown("### CeRAI Test Run Results")

cerai_data = {
    "Run": ["Run 1 — Responsible_AI", "Run 2 — Guardrails_and_Safety"],
    "Target": ["Gemini-2.5-Flash (API)", "Gemini-2.5-Flash (API)"],
    "Duration": ["27s", "23s"],
    "Completed": [3, 4],
    "Failed": [7, 6],
    "Scores Produced": ["None", "None"],
    "Completion Rate": ["30%", "40%"]
}

st.dataframe(pd.DataFrame(cerai_data), use_container_width=True, hide_index=True)

st.markdown("### Why a Custom Evaluator Was Built")
st.markdown("""
Given the CeRAI tool's non-functional scoring pipeline, a custom LLM-as-judge evaluator was
implemented to produce the maternal health evaluation results shown above. This was not a
rejection of the tool — it was a pragmatic response to documented infrastructure constraints,
consistent with producing meaningful evaluation output within the assignment timeframe.
The custom evaluator uses the same LLM-as-judge pattern the CeRAI tool intends to implement,
applied to a domain-specific maternal health test suite designed for ASHA worker deployment contexts.
""")

st.divider()

st.markdown("## AI Use Disclosure")

st.markdown("""
<div class="finding-box warn">
<strong>How AI was used in completing this assignment</strong><br><br>
This assignment was completed with significant assistance from <strong>Claude Sonnet 4.6</strong>
(Anthropic), used as a collaborative debugging and documentation partner throughout the process.<br><br>
<strong>Specific uses:</strong><br>
- <strong>Installation debugging</strong> — interpreting Docker container logs, identifying the
undocumented strategy .env dependency, diagnosing the Windows volume mounting gap, and
resolving the docker-compose.yml fix. Claude helped parse error output and reason through
root causes systematically.<br><br>
- <strong>API debugging</strong> — identifying the deprecated <code>google.generativeai</code>
library, resolving model name mismatches between gemini-2.0-flash and gemini-2.5-flash,
and diagnosing quota exhaustion vs rate limiting errors.<br><br>
- <strong>Code scaffolding</strong> — the evaluation script structure, judge prompt design,
and Streamlit report layout were developed collaboratively. All domain-specific content
(maternal health test cases, LMIC context, clinical reasoning) was authored by me based
on my bioinformatics background and understanding of the Fellows #1 project scope.<br><br>
- <strong>Documentation</strong> — Claude helped synthesize findings from multiple debugging
sessions, evaluation runs, and CeRAI tool observations into this structured report. The
analytical framing — particularly the LMIC deployment risk analysis and safety context findings —
reflects my own judgment; Claude helped articulate and organise it clearly.<br><br>
<strong>Course corrections:</strong> Initial attempts used the wrong Gemini model (2.0 instead of 2.5),
the deprecated Python library, and insufficient rate limiting. Each was identified through
error output analysis with Claude's help and corrected iteratively.<br><br>
<strong>What AI did not do:</strong> AI did not determine which bugs were significant, did not
design the maternal health evaluation dimensions, did not make the decision to build a custom
evaluator, and did not write the clinical reasoning behind test case design. Those judgments
were mine.
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("## Machine-Readable Summary")
st.json({
    "target_model": meta["target_model"],
    "evaluation_context": "Maternal health AI for LMIC frontline worker (ASHA) deployment",
    "overall_score": data["overall_score"],
    "metric_averages": metric_avgs,
    "scored_cases": meta["scored_cases"],
    "total_cases": meta["total_test_cases"],
    "critical_issues": data["critical_issues_count"],
    "infrastructure_issues": {
        "quota_exhaustion": infra["quota_exhaustion_count"],
        "service_unavailability": infra["service_unavailability_count"]
    },
    "deployment_ready_lmic": False,
    "recommended_next_steps": [
        "Upgrade to paid Gemini API tier with reliability SLA",
        "Expand test suite to 100+ cases across Hindi and regional languages",
        "Conduct validation with actual ASHA workers",
        "Implement fallback model for high-demand periods",
        "Add human-in-the-loop for critical safety decisions"
    ]
})

st.divider()
st.caption("Gates Foundation AI Fellows Program — Technical Case Study | Yash Kunwar")