import streamlit as st
import json
import time
from datetime import datetime
import threading

# Import your local pipeline
from utility import run_factcheck_pipeline  

# Page configuration
st.set_page_config(
    page_title="NewsGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal CSS
st.markdown("""<style>
    .main { padding-top: 1rem; }
    .title-container { text-align: center; padding: 1.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; margin-bottom: 1.5rem; color: white; }
    .verdict-reliable { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 0.8rem; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 1rem; font-size: 2.5rem;}
    .verdict-unreliable { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 0.8rem; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 1rem; font-size: 2.5rem;}
    .verdict-mixed { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 0.8rem; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 1rem; font-size: 2.5rem;}
    .verdict-not-enough-evidence { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 0.8rem; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 1rem; font-size: 2.5rem;}
    .score-card { background: white; padding: 1rem; border-radius: 10px; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 2px solid #667eea; }
    .source-card { background: white; padding: 0.8rem; border-radius: 8px; margin: 0.3rem 0;
        border-left: 3px solid #667eea; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .metric-small { background: #f8f9fa; padding: 0.6rem; border-radius: 6px;
        text-align: center; margin: 0.2rem; }
</style>""", unsafe_allow_html=True)


# ---- Wrapper to directly call pipeline ----
def analyze_with_local_function(news_text: str):
    try:
        parsed, sources = run_factcheck_pipeline(news_text)

        # Convert stance → UI verdict class
        stance = parsed.get("stance", "insufficient").lower()
        if stance == "supports":
            verdict_class = "verdict-reliable"
            verdict_text = "Reliable"
        elif stance == "refutes":
            verdict_class = "verdict-unreliable"
            verdict_text = "Unreliable"
        elif stance == "mixture":
            verdict_class = "verdict-mixed"
            verdict_text = "Mixed Evidence"
        else:
            verdict_class = "verdict-not-enough-evidence"
            verdict_text = "Not Enough Evidence"

        return {
            "verdict": verdict_text,
            "credibility_score": parsed.get("confidence", 50),
            "explanation": parsed.get("explanation", "No explanation"),
            "verdict_class": verdict_class,
            "sources": [{"title": s["title"], "url": s["url"]} for s in sources]
        }, None

    except Exception as e:
        return None, f"Local function error: {str(e)}"


# ---- Fallback mock ----
FALLBACK_ANALYSIS = {
    "verdict": "Demo Mode",
    "credibility_score": 75,
    "explanation": "Backend unavailable - showing demo analysis",
    "verdict_class": "verdict-mixed",
    "sources": [
        {"title": "Demo Source 1", "url": "https://example.com/1"},
        {"title": "Demo Source 2", "url": "https://example.com/2"}
    ]
}

# ---- Session state ----
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False

# ---- Header ----
st.markdown("""<div class="title-container">
    <h1>🛡️ NewsGuard AI</h1>
    <p style="margin: 0; opacity: 0.9;">AI-Powered News Credibility Analysis</p>
</div>""", unsafe_allow_html=True)


# ---- Input UI ----
if not st.session_state.analyzed and not st.session_state.analyzing:
    st.markdown("### 📰 Analyze News Article")
    news_text = st.text_area(
        "Enter article text:",
        height=120,
        placeholder="Enter news article text for credibility analysis...",
        key="news_input"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button("🔍 Analyze Now", type="primary", use_container_width=True)

    if analyze_button and news_text.strip():
        st.session_state.analyzing = True
        st.rerun()
    elif analyze_button:
        st.error("⚠️ Please enter article text!")

# ---- Analysis ----
elif st.session_state.analyzing:
    with st.spinner("🤖 Analysis in progress..."):
        result, error = analyze_with_local_function(st.session_state.get("news_input", ""))

    if error:
        st.error(error)
        st.info("💡 Using fallback demo mode")
        st.session_state.result = FALLBACK_ANALYSIS
    else:
        st.session_state.result = result

    st.session_state.analyzed = True
    st.session_state.analyzing = False
    st.rerun()

# ---- Results ----
else:
    result = st.session_state.result

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""<div class="{result['verdict_class']}">
            {result['verdict']}
        </div>""", unsafe_allow_html=True)
        st.markdown(f"**Analysis:** {result['explanation']}")

    with col2:
        score = result['credibility_score']
        st.markdown(f"""
        <div class="score-card">
            <h2 style="margin: 0; color: #667eea; font-size: 2rem;">{score}%</h2>
            <p style="margin: 0.5rem 0; color: #666;">Credibility</p>
            <div style="background: #e9ecef; height: 4px; border-radius: 2px;">
                <div style="background: #667eea; height: 100%; width: {score}%; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if result.get('sources'):
        st.markdown("### 🔗 Reference Sources")
        for source in result['sources']:
            st.markdown(f"""
            <div class="source-card">
                <strong>{source.get('title', 'Unknown Title')}</strong><br>
                <a href="{source.get('url', '#')}" target="_blank" style="color: #667eea; text-decoration: none; font-size: 0.9rem;">
                    🔗 {source.get('url', 'No URL')}
                </a>
            </div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Analyze Another", use_container_width=True):
            st.session_state.analyzed = False
            st.session_state.analyzing = False
            st.session_state.result = None
            st.rerun()

    with col2:
        result_json = json.dumps(result, indent=2)
        st.download_button(
            "💾 Download Report",
            data=result_json,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

st.markdown("---")
st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem;'>🚀 NewsGuard AI Prototype</p>", unsafe_allow_html=True)
