"""
TruthLens Streamlit Web Application

Interactive UI for rumour & claim verification using the multi-agent pipeline.
Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
from utils.config import Config
from services.factcheck_service import FactCheckService
from services.gemini_service import GeminiService
from agents.claim_agent import ClaimAgent
from agents.memory_agent import MemoryAgent
from agents.evidence_agent import EvidenceAgent
from agents.reasoning_agent import ReasoningAgent

st.set_page_config(
    page_title="TruthLens - AI Rumour Verifier",
    page_icon="🔍",
    layout="centered"
)

# Custom Styling
st.markdown("""
<style>
    .report-card {
        padding: 20px;
        border-radius: 12px;
        background-color: #f8f9fa;
        margin-top: 15px;
        border: 1px solid #e9ecef;
    }
    .citation-card {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: #f1f3f5;
        border-left: 4px solid #495057;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 TruthLens")
st.caption("Multi-Agent Rumour Verification System powered by Google Gemini 2.5 Flash")


@st.cache_resource
def load_agents():
    config = Config()
    config.validate()
    factcheck = FactCheckService(api_key=config.google_factcheck_api_key)
    gemini = GeminiService(api_key=config.gemini_api_key)

    return {
        "claim": ClaimAgent(),
        "memory": MemoryAgent(history_file=config.history_file),
        "evidence": EvidenceAgent(factcheck_service=factcheck),
        "reasoning": ReasoningAgent(gemini_service=gemini)
    }


try:
    agents = load_agents()
except Exception as e:
    st.error(f"⚠️ Configuration error: {e}. Check your `.env` file.")
    st.stop()

# Input section
claim_input = st.text_input(
    "Enter a claim, rumour, or headline to fact-check:",
    placeholder="e.g., COVID vaccines contain microchips"
)

col_check1, col_check2 = st.columns([1, 1])
with col_check1:
    bypass_cache = st.checkbox("🔄 Bypass cache (force fresh live search)", value=False)

col1, col2 = st.columns([1, 4])
with col1:
    verify_clicked = st.button("🔎 Verify", type="primary", use_container_width=True)

if verify_clicked:
    if not claim_input.strip():
        st.warning("Please enter a valid claim.")
    else:
        norm_claim = agents["claim"].process(claim_input)
        result = None

        # Step 1: Check Cache if not bypassed
        if not bypass_cache:
            cached = agents["memory"].search(norm_claim)
            if cached and cached.get("status") == "SUCCESS":
                st.info(f"📋 Loaded from Cache (Verified at: {cached.get('verified_at', 'earlier')})")
                result = cached

        # Step 2: Live Verification if not in cache or bypassed
        if not result:
            with st.spinner("🔎 Searching official ClaimReviews & multi-source web evidence..."):
                evidence = agents["evidence"].gather(norm_claim)

            with st.spinner("🤖 Grounding evidence with Gemini 2.5 Flash..."):
                result = agents["reasoning"].analyze(norm_claim, evidence)
                if result.get("status") == "SUCCESS":
                    agents["memory"].save(result)

        # Presentation
        status = result.get("status", "SUCCESS")
        verdict = result.get("verdict", "Unverified")
        confidence = result.get("confidence", 0)
        explanation = result.get("explanation", "No explanation available.")
        citations = result.get("citations", [])
        model_used = result.get("model_used", "gemini-2.5-flash")
        verified_at = result.get("verified_at", "Just now")

        if status == "OPERATIONAL_FAILURE":
            st.error(f"❌ System Error ({result.get('error_type', 'API Error')}): {result.get('error_message')}")
        else:
            if verdict == "True":
                verdict_color = "#28a745"
                icon = "✅"
            elif verdict in ("False", "Misleading"):
                verdict_color = "#dc3545"
                icon = "❌"
            else:
                verdict_color = "#ffc107"
                icon = "⚠️"

            st.markdown(
                f"""
                <div style="background-color: {verdict_color}15; border-left: 6px solid {verdict_color}; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin: 0; color: {verdict_color};">{icon} Verdict: {verdict}</h3>
                    <p style="margin: 5px 0 0 0; font-weight: 600;">Evidence Confidence: {confidence}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.subheader("Grounded Reasoning & Analysis")
            st.write(explanation)

            # Multiple verified citations
            if citations:
                st.subheader(f"Verified Citations ({len(citations)})")
                for cit in citations:
                    st.markdown(
                        f"""
                        <div class="citation-card">
                            <strong>{cit.get('publisher', 'Source')}</strong> <em>({cit.get('tier', 'Web')})</em><br>
                            <a href="{cit.get('url', '#')}" target="_blank">{cit.get('title', 'Article link')}</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.caption(f"Evaluated with **{model_used}** | Timestamp: {verified_at}")

# History Expander
with st.sidebar:
    st.header("Recent Verifications")
    try:
        history = agents["memory"].get_all()
        if history:
            for item in reversed(history[-10:]):
                ver = item.get("verdict", "Unverified")
                v_icon = "✅" if ver == "True" else "❌" if ver in ("False", "Misleading") else "⚠️"
                st.write(f"{v_icon} **{item.get('claim', '')[:30]}...** — `{ver}`")
        else:
            st.caption("No history recorded yet.")
    except Exception:
        st.caption("History unavailable.")
