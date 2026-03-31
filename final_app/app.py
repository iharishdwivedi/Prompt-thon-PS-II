import streamlit as st
import os
import json
import tempfile
from pathlib import Path
import time
import webbrowser
import math
import importlib.util
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import stage functions
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys_path_stage1 = os.path.join(_root, "stage1")
sys_path_stage2 = os.path.join(_root, "stage2_3")
sys_path_stage4 = os.path.join(_root, "stage4")
sys_path_stage5 = os.path.join(_root, "stage5")
sys_path_try    = os.path.join(_root, "try")

sys = __import__('sys')
if sys_path_stage1 not in sys.path:
    sys.path.insert(0, sys_path_stage1)
if sys_path_stage2 not in sys.path:
    sys.path.insert(0, sys_path_stage2)
if sys_path_stage4 not in sys.path:
    sys.path.insert(0, sys_path_stage4)
if sys_path_stage5 not in sys.path:
    sys.path.insert(0, sys_path_stage5)
if sys_path_try not in sys.path:
    sys.path.insert(0, sys_path_try)

from parser.floorplan_parser import parse_floorplan
from image_processor import process_image
from graph_builder import build_graph, classify_walls
from threejs_exporter import export_threejs
from material_db import load_materials
from tradeoff_engine import analyze_all
from prompt_builder import build_prompt
from gemini_client import call_gemini
from vision_parser import parse as vision_parse

# Hide sidebar
st.set_page_config(page_title="Autonomous Structural Intelligence System", page_icon="🏗", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════════ */
/* ELEGANT BEIGE & WHITE DESIGN SYSTEM */
/* ═══════════════════════════════════════════════════════════════════ */

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --primary: #d4a574;
    --primary-light: #e6b885;
    --primary-dark: #c49663;
    --accent: #f5f5dc;
    --accent-light: #fafafa;
    --success: #a8a878;
    --warning: #d4af37;
    --danger: #c49663;
    --bg-primary: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
    --bg-secondary: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
    --bg-dark: linear-gradient(135deg, #e0e0e0 0%, #d0d0d0 100%);
    --text-primary: #4a4a4a;
    --text-secondary: #6b6b6b;
    --text-light: #8b8b8b;
    --border: #e0e0e0;
    --shadow: rgba(0, 0, 0, 0.08);
    --beige-light: #f8f6f0;
    --beige-medium: #ede6d6;
    --beige-dark: #d4c4a8;
    --off-white: #fefefe;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary);
    background-attachment: fixed;
    color: var(--text-primary);
    font-family: 'Georgia', 'Times New Roman', serif;
    overflow-x: hidden;
    line-height: 1.6;
}

body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="texture" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="rgba(212, 196, 168, 0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23texture)"/></svg>');
    pointer-events: none;
    z-index: -1;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* ANIMATIONS */
/* ═══════════════════════════════════════════════════════════════════ */

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes gentlePulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

@keyframes softGlow {
    0%, 100% { box-shadow: 0 4px 20px rgba(212, 166, 116, 0.1); }
    50% { box-shadow: 0 4px 30px rgba(212, 166, 116, 0.2); }
}

@keyframes slideIn {
    from { transform: translateX(-10px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* ═══════════════════════════════════════════════════════════════════ */
/* TYPOGRAPHY */
/* ═══════════════════════════════════════════════════════════════════ */

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-weight: 600;
    letter-spacing: -0.3px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    font-family: 'Georgia', serif;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* HERO SECTION */
/* ═══════════════════════════════════════════════════════════════════ */

.hero-container {
    background: linear-gradient(135deg, var(--beige-light) 0%, var(--beige-medium) 100%);
    padding: 60px 50px;
    border-radius: 20px;
    color: var(--text-primary);
    text-align: center;
    margin-bottom: 40px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 1.2s ease-out;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
    animation: slideIn 3s ease-in-out infinite;
}

.hero-title {
    font-size: 48px;
    font-weight: 700;
    margin-bottom: 20px;
    letter-spacing: -1px;
    color: var(--primary-dark);
    position: relative;
    z-index: 2;
}

.hero-subtitle {
    font-size: 20px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    font-weight: 500;
}

.hero-description {
    font-size: 16px;
    color: var(--text-light);
    max-width: 650px;
    margin: 0 auto;
    line-height: 1.7;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* STAGE HEADER */
/* ═══════════════════════════════════════════════════════════════════ */

.stage-header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 36px;
    font-weight: 700;
    padding: 0;
    margin: 0 0 20px 0;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stage-breadcrumb {
    display: flex;
    gap: 16px;
    align-items: center;
    font-size: 14px;
    color: var(--text-light);
    margin-bottom: 30px;
    animation: fadeInUp 1s ease-out;
    flex-wrap: wrap;
}

.breadcrumb-item {
    padding: 8px 16px;
    background: var(--off-white);
    border: 1px solid var(--border);
    border-radius: 25px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px var(--shadow);
}

.breadcrumb-item:hover {
    transform: translateY(-2px);
    background: var(--beige-light);
}

.breadcrumb-item.active {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(212, 166, 116, 0.3);
}

/* ═══════════════════════════════════════════════════════════════════ */
/* UPLOAD AREA */
/* ═══════════════════════════════════════════════════════════════════ */

.upload-container {
    background: var(--off-white);
    border: 2px dashed var(--border);
    border-radius: 20px;
    padding: 60px 50px;
    text-align: center;
    transition: all 0.4s ease;
    margin: 30px 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px var(--shadow);
    animation: fadeInUp 1s ease-out 0.3s both;
}

.upload-container:hover {
    border-color: var(--primary);
    background: var(--beige-light);
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.upload-icon {
    font-size: 72px;
    margin-bottom: 24px;
    color: var(--primary);
    animation: gentlePulse 2s ease-in-out infinite;
}

.upload-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
}

.upload-text {
    color: var(--text-secondary);
    font-size: 16px;
    margin-bottom: 24px;
    line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* RESULT BOX */
/* ═══════════════════════════════════════════════════════════════════ */

.result-box {
    background: var(--off-white);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 32px;
    margin: 30px 0;
    box-shadow: 0 4px 20px var(--shadow);
    transition: all 0.3s ease;
    animation: fadeInUp 1s ease-out 0.5s both;
}

.result-box:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-light);
}

.result-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* ═══════════════════════════════════════════════════════════════════ */
/* METRIC CARD */
/* ═══════════════════════════════════════════════════════════════════ */

.metric-card {
    background: var(--off-white);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 12px var(--shadow);
    animation: fadeInUp 1s ease-out;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    border-color: var(--primary);
}

.metric-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-light);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 36px;
    font-weight: 700;
    color: var(--primary-dark);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* ═══════════════════════════════════════════════════════════════════ */
/* BUTTONS */
/* ═══════════════════════════════════════════════════════════════════ */

.button-container {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin: 40px 0;
    flex-wrap: wrap;
}

button {
    font-weight: 600;
    border-radius: 12px;
    border: 2px solid var(--primary);
    padding: 14px 28px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 3px 12px var(--shadow);
    position: relative;
    overflow: hidden;
    background: var(--off-white);
    color: var(--primary-dark);
    font-family: 'Georgia', serif;
    animation: fadeInUp 1s ease-out;
}

button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(212, 166, 116, 0.1), transparent);
    transition: left 0.5s;
}

button:hover::before {
    left: 100%;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    background: var(--beige-light);
    border-color: var(--primary-dark);
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: white;
    border: none;
}

.btn-secondary {
    background: var(--off-white);
    color: var(--primary-dark);
    border: 2px solid var(--primary);
}

.btn-success {
    background: linear-gradient(135deg, var(--success) 0%, #9a9a6a 100%);
    color: white;
    border: none;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* PROGRESS INDICATOR */
/* ═══════════════════════════════════════════════════════════════════ */

.progress-bar {
    background: var(--beige-light);
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 30px 0;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-fill {
    background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
    height: 100%;
    animation: slideIn 0.8s ease;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* LOADING SPINNER */
/* ═══════════════════════════════════════════════════════════════════ */

.spinner {
    display: inline-block;
    width: 24px;
    height: 24px;
    border: 3px solid var(--beige-light);
    border-radius: 50%;
    border-top-color: var(--primary);
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* ═══════════════════════════════════════════════════════════════════ */
/* INFO BOX */
/* ═══════════════════════════════════════════════════════════════════ */

.info-box {
    background: var(--beige-light);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin: 24px 0;
    color: var(--text-primary);
    animation: fadeInUp 1s ease-out;
    box-shadow: 0 2px 12px var(--shadow);
}

.info-box p {
    margin: 0;
    font-size: 16px;
    line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* EXPANDER */
/* ═══════════════════════════════════════════════════════════════════ */

[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 16px;
    background: var(--off-white);
    box-shadow: 0 2px 8px var(--shadow);
}

/* ═══════════════════════════════════════════════════════════════════ */
/* RESPONSIVE */
/* ═══════════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
    .hero-title { font-size: 36px; }
    .stage-header { font-size: 28px; }
    .button-container { flex-direction: column; gap: 16px; }
    button { width: 100%; padding: 16px; }
    .upload-container { padding: 40px 30px; }
    .result-box { padding: 24px; }
    .metric-card { padding: 20px; }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_stage" not in st.session_state:
    st.session_state.current_stage = 0
    st.session_state.uploaded_file_path = None
    st.session_state.ocr_results = None
    st.session_state.vision_results = None
    st.session_state.model_3d_path = None
    st.session_state.stage2_data = None
    st.session_state.material_results = None
    st.session_state.material_3d_path = None
    st.session_state.material_decisions = None
    st.session_state.ai_report = None
    st.session_state.blockchain_result = None
    st.session_state.floor_hash = None

# ─── STAGE 0: UPLOAD ─────────────────────────────────────────────────────
if st.session_state.current_stage == 0:
    # Hero Section
    st.markdown("""
<div class="hero-container">
    <div class="hero-title">🏗 Autonomous Structural Intelligence System</div>
    <div class="hero-subtitle">Autonomous Structural Intelligence Platform</div>
    <div class="hero-description">
        Transform your floor plans into comprehensive structural analysis with AI-powered insights
    </div>
</div>
""", unsafe_allow_html=True)
    
    import requests as _req

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two-column layout: Upload LEFT | Blockchain RIGHT ────────
    col_upload, col_chain = st.columns([1, 1], gap="large")

    # ── LEFT: Upload ─────────────────────────────────────────────
    with col_upload:
        st.markdown("""
        <div class="upload-container">
            <div class="upload-icon">📤</div>
            <div class="upload-title">Upload Floor Plan</div>
            <div class="upload-text">
                Drag and drop or click to select your floor plan image<br>
                <span style="font-size: 12px; color: #94a3b8;">PNG, JPG, JPEG, GIF, BMP up to 200MB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Choose floor plan image",
                                         type=["png", "jpg", "jpeg", "gif", "bmp"],
                                         label_visibility="hidden")

        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded_file.getbuffer())
                st.session_state.uploaded_file_path = tmp.name

            st.markdown("<br>", unsafe_allow_html=True)
            st.image(uploaded_file, caption="✓ Floor Plan Ready for Analysis", use_column_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🚀 Begin Analysis", key="start_btn", use_container_width=True):
                    st.session_state.current_stage = 1
                    st.rerun()
            with col_b:
                if st.button("🔄 Choose Different File", key="reupload", use_container_width=True):
                    st.session_state.uploaded_file_path = None
                    st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="info-box">
                <p><strong>✨ Get Started:</strong> Upload a high-quality floor plan image to begin
                the analysis pipeline. The system will extract room layouts, detect structural
                elements, generate a 3D model, and provide AI-powered insights.</p>
            </div>
            """, unsafe_allow_html=True)

    # ── RIGHT: Blockchain Verification Panel ─────────────────────
    with col_chain:
        FLASK_URL   = "http://localhost:5050"
        CONTRACT_ID = "CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J"

        st.markdown("""
        <div style="background:linear-gradient(135deg,var(--beige-medium) 0%,var(--beige-light) 100%);
                    border:1px solid var(--border);border-radius:16px;padding:24px">
            <p style="color:var(--primary-dark);font-size:13px;font-weight:700;text-transform:uppercase;
                      letter-spacing:1px;margin-bottom:4px">⛓ Blockchain Verification</p>
            <p style="color:var(--text-secondary);font-size:12px;margin-bottom:16px">
                Already have a report? Verify, check ownership or browse the registry — no upload needed.
            </p>
            <div style="display:grid;grid-template-columns:1fr;gap:10px">
                <div style="background:var(--off-white);border:1px solid var(--border);border-radius:12px;padding:14px 16px">
                    <div style="color:var(--primary-dark);font-weight:700;font-size:13px;margin-bottom:4px">🔍 Verify a Report</div>
                    <div style="color:var(--text-secondary);font-size:12px;line-height:1.5">Paste a floor plan hash and instantly confirm the structural report is authentic and untampered on Stellar blockchain.</div>
                </div>
                <div style="background:var(--off-white);border:1px solid var(--border);border-radius:12px;padding:14px 16px">
                    <div style="color:var(--primary-dark);font-weight:700;font-size:13px;margin-bottom:4px">👤 Check Ownership</div>
                    <div style="color:var(--text-secondary);font-size:12px;line-height:1.5">Look up which wallet address registered a floor plan design. Immutable IP ownership proof for architects.</div>
                </div>
                <div style="background:var(--off-white);border:1px solid var(--border);border-radius:12px;padding:14px 16px">
                    <div style="color:var(--primary-dark);font-weight:700;font-size:13px;margin-bottom:4px">📚 Browse Public Registry</div>
                    <div style="color:var(--text-secondary);font-size:12px;line-height:1.5">See every floor plan analysis ever anchored on Stellar. Full tamper-proof audit trail for regulators.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Inline verify form ────────────────────────────────────
        with st.expander("🔍 Verify a Report now", expanded=False):
            h = st.text_input("Floor Plan Hash", placeholder="Paste 32-char hash here...",
                              key="home_verify_hash")
            if st.button("Verify on Blockchain", key="home_verify_btn", use_container_width=True):
                if h.strip():
                    with st.spinner("Querying Stellar..."):
                        try:
                            r = _req.get(f"{FLASK_URL}/api/get_report/{h.strip()}", timeout=20)
                            d = r.json()
                            if d.get("success"):
                                st.success("✅ Report verified on Stellar blockchain")
                                st.code(d.get("result_xdr", ""), language=None)
                            else:
                                st.error(f"❌ {d.get('error','Not found')}")
                        except Exception as e:
                            st.error("❌ Flask server not running. Start it with:  cd web3  then  python app.py")
                else:
                    st.warning("Enter a hash first")

        with st.expander("👤 Check Ownership now", expanded=False):
            h2 = st.text_input("Floor Plan Hash", placeholder="Paste 32-char hash here...",
                               key="home_owner_hash")
            if st.button("Check Owner", key="home_owner_btn", use_container_width=True):
                if h2.strip():
                    with st.spinner("Looking up registry..."):
                        try:
                            r = _req.get(f"{FLASK_URL}/api/get_owner/{h2.strip()}", timeout=20)
                            d = r.json()
                            if d.get("success"):
                                st.success("✅ Ownership record found")
                                st.code(d.get("result_xdr", ""), language=None)
                            else:
                                st.error(f"❌ {d.get('error','Not found')}")
                        except Exception as e:
                            st.error("❌ Flask server not running. Start it with:  cd web3  then  python app.py")
                else:
                    st.warning("Enter a hash first")

        with st.expander("📚 Browse Public Registry now", expanded=False):
            if st.button("Load Registry", key="home_registry_btn", use_container_width=True):
                with st.spinner("Fetching on-chain registry..."):
                    try:
                        rc = _req.get(f"{FLASK_URL}/api/report_count", timeout=20).json()
                        rh = _req.get(f"{FLASK_URL}/api/all_hashes",   timeout=20).json()
                        count = rc.get("result_xdr", "?") if rc.get("success") else "?"
                        st.metric("Total Reports On-Chain", count)
                        if rh.get("success"):
                            st.code(rh.get("result_xdr", ""), language=None)
                        else:
                            st.error(f"❌ {rh.get('error')}")
                    except Exception as e:
                        st.error("❌ Flask server not running. Start it with:  cd web3  then  python app.py")

        st.markdown(f"""
        <div style="margin-top:12px;padding:10px 14px;background:var(--beige-light);
                    border-radius:8px;border:1px solid var(--border)">
            <a href="https://stellar.expert/explorer/testnet/contract/{CONTRACT_ID}"
               target="_blank"
               style="color:var(--primary);font-size:12px">🔗 View Contract on Stellar Explorer ↗</a>
        </div>
        """, unsafe_allow_html=True)

# ─── STAGE 1: OCR ────────────────────────────────────────────────────────
elif st.session_state.current_stage == 1:
    # Breadcrumb
    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item active">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<h1 class="stage-header">🔍 OCR Detection</h1>', unsafe_allow_html=True)
    st.markdown('Extracting room labels, dimensions, and structural elements', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(1/7, text="Stage 1 of 7")
    
    if st.session_state.ocr_results is None:
        with st.spinner("🔄 Processing image with OCR..."):
            try:
                ocr_results = parse_floorplan(st.session_state.uploaded_file_path, "output")
                st.session_state.ocr_results = ocr_results
                st.balloons()  # Celebration animation
                st.success("🎉 OCR Processing Complete!")
            except Exception as e:
                st.error(f"❌ OCR Error: {str(e)}")
                if st.button("⬅️ Back to Upload"):
                    st.session_state.current_stage = 0
                    st.rerun()
    
    if st.session_state.ocr_results:
        results = st.session_state.ocr_results
        room_counts = results.get("room_counts", {})
        ocr_data = results.get("ocr", {})
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Results
        st.markdown("""
        <div class="result-box">
            <div class="result-title">📊 Room Detection Results</div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🛏️ Bedrooms</div>
                <div class="metric-value">%d</div>
            </div>
            """ % room_counts.get("bedroom", 0), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🚿 Bathrooms</div>
                <div class="metric-value">%d</div>
            </div>
            """ % room_counts.get("bathroom", 0), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">📏 Dimensions</div>
                <div class="metric-value">%d</div>
            </div>
            """ % len(ocr_data.get("dimensions", [])), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">📝 Annotations</div>
                <div class="metric-value">%d</div>
            </div>
            """ % len(ocr_data.get("annotations", [])), unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("📋 View Detected Text Details"):
            dims = ocr_data.get("dimensions", [])
            labels = ocr_data.get("room_labels", [])
            anns = ocr_data.get("annotations", [])
            if labels:
                st.markdown("**🏠 Room Labels Detected**")
                for item in labels:
                    st.markdown(f"- `{item.get('text','')}` → **{item.get('normalized','')}** (confidence: {int(item.get('confidence',0)*100)}%)")
            if dims:
                st.markdown("**📏 Dimensions Detected**")
                for item in dims:
                    st.markdown(f"- `{item.get('text','')}` (confidence: {int(item.get('confidence',0)*100)}%)")
            if anns:
                st.markdown("**📝 Other Annotations**")
                for item in anns:
                    st.markdown(f"- `{item.get('text','')}`)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Back", key="back_1", use_container_width=True):
                st.session_state.current_stage = 0
                st.rerun()
        with col2:
            st.markdown("")  # Spacer
        with col3:
            if st.button("➡️ Next: Vision Analysis", key="next_1", use_container_width=True):
                st.session_state.current_stage = 2
                st.rerun()

# ─── STAGE 2: VISION ─────────────────────────────────────────────────────
elif st.session_state.current_stage == 2:
    # Breadcrumb
    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item active">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<h1 class="stage-header">📐 Vision Analysis</h1>', unsafe_allow_html=True)
    st.markdown('Detecting walls, columns, and structural geometry', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(2/7, text="Stage 2 of 7")
    
    if st.session_state.vision_results is None and st.session_state.stage2_data is None:
        with st.spinner("🔄 Processing image and analyzing geometry..."):
            try:
                # Process image
                vision_data = process_image(st.session_state.uploaded_file_path)
                st.session_state.vision_results = vision_data
                
                # Build graph
                nodes, edges = build_graph(vision_data["segments"])
                classified = classify_walls(nodes, edges, 
                                           vision_data["image_size"]["width"], 
                                           vision_data["image_size"]["height"])
                
                outer = [e for e in classified if e["wall_class"] == "load_bearing_outer"]
                spine = [e for e in classified if e["wall_class"] == "load_bearing_spine"]
                parts = [e for e in classified if e["wall_class"] == "partition"]
                
                stage2_data = {
                    "image_size": vision_data["image_size"],
                    "nodes": nodes,
                    "walls": classified,
                    "rooms": vision_data.get("rooms", []),
                    "summary": {
                        "nodes": len(nodes),
                        "edges": len(edges),
                        "load_bearing_outer": len(outer),
                        "load_bearing_spine": len(spine),
                        "partition": len(parts),
                        "rooms": len(vision_data.get("rooms", []))
                    }
                }
                st.session_state.stage2_data = stage2_data
                st.balloons()  # Celebration animation
                st.success("🎉 Vision Analysis Complete!")
            except Exception as e:
                st.error(f"❌ Vision Analysis Error: {str(e)}")
    
    if st.session_state.stage2_data:
        data = st.session_state.stage2_data["summary"]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="result-box">
            <div class="result-title">🧊 Geometry Detection Results</div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">📍 Nodes</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["nodes"], unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🔗 Edges</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["edges"], unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🏠 Rooms</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["rooms"], unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">📏 Scale</div>
                <div class="metric-value">100%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Second row of metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🧱 Outer Walls</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["load_bearing_outer"], unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">🎯 Spine Walls</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["load_bearing_spine"], unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">📦 Partitions</div>
                <div class="metric-value">%d</div>
            </div>
            """ % data["partition"], unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("📋 View Wall Classification Details"):
            walls = st.session_state.stage2_data.get("walls", [])
            outer_w = [w for w in walls if w.get("wall_class") == "load_bearing_outer"]
            spine_w = [w for w in walls if w.get("wall_class") == "load_bearing_spine"]
            part_w  = [w for w in walls if w.get("wall_class") == "partition"]
            for cls_name, cls_walls, color in [
                ("🧱 Load-Bearing Outer", outer_w, "#3b82f6"),
                ("🎯 Load-Bearing Spine", spine_w, "#8b5cf6"),
                ("📦 Partition",          part_w,  "#10b981"),
            ]:
                if cls_walls:
                    st.markdown(f"**{cls_name}** — {len(cls_walls)} walls")
                    for w in cls_walls[:5]:
                        st.markdown(f"  - Length: `{w.get('length',0):.0f}px` | Angle: `{w.get('angle',0):.1f}°`")
                    if len(cls_walls) > 5:
                        st.markdown(f"  _...and {len(cls_walls)-5} more_")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Back", key="back_2", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()
        with col2:
            st.markdown("")  # Spacer
        with col3:
            if st.button("➡️ Next: 3D Model", key="next_2", use_container_width=True):
                st.session_state.current_stage = 3
                st.rerun()

# ─── STAGE 3: 3D MODEL ───────────────────────────────────────────────────
elif st.session_state.current_stage == 3:
    # Breadcrumb
    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item active">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<h1 class="stage-header">🧊 3D Model Generation</h1>', unsafe_allow_html=True)
    st.markdown('Interactive three-dimensional visualization with Three.js', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(3/7, text="Stage 3 of 7")
    
    if st.session_state.model_3d_path is None:
        with st.spinner("🔄 Generating interactive 3D model..."):
            try:
                stage2_data = st.session_state.stage2_data
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                
                html_path = os.path.join(output_dir, "model_3d.html")
                export_threejs(
                    classified_edges=stage2_data["walls"],
                    rooms=stage2_data["rooms"],
                    image_w=stage2_data["image_size"]["width"],
                    image_h=stage2_data["image_size"]["height"],
                    output_path=html_path
                )
                st.session_state.model_3d_path = html_path
                st.balloons()  # Celebration animation
                st.success("🎉 3D Model Generated!")
            except Exception as e:
                st.error(f"❌ 3D Model Error: {str(e)}")
    
    if st.session_state.model_3d_path and os.path.exists(st.session_state.model_3d_path):
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="result-box">
            <div class="result-title">🎨 Interactive 3D Visualization</div>
            <p style="color: #64748b; margin-bottom: 16px; font-size: 14px;">
                Use your mouse to rotate, zoom, and interact with the model. 
                Different colors represent different wall types.
            </p>
        """, unsafe_allow_html=True)
        
        with open(st.session_state.model_3d_path, "r") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=700, scrolling=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chrome Button
        st.markdown("<br>", unsafe_allow_html=True)
        col_chrome, col_spacer = st.columns([1, 2])
        with col_chrome:
            if st.button("🌐 Open in Chrome", key="open_chrome", use_container_width=True):
                abs_path = os.path.abspath(st.session_state.model_3d_path)
                webbrowser.open(f"file:///{abs_path}", new=2)
                st.success("✓ Opening in Chrome...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", key="back_3", use_container_width=True):
            st.session_state.current_stage = 2
            st.rerun()
    with col2:
        st.markdown("")  # Spacer
    with col3:
        if st.button("➡️ Next: Materials", key="next_3", use_container_width=True):
            st.session_state.current_stage = 4
            st.rerun()

# ─── STAGE 4: MATERIALS ──────────────────────────────────────────────────
elif st.session_state.current_stage == 4:
    # Breadcrumb
    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item active">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<h1 class="stage-header">🧱 Material Analysis</h1>', unsafe_allow_html=True)
    st.markdown('Cost-strength tradeoff analysis for structural materials', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(4/7, text="Stage 4 of 7")
    
    if st.session_state.material_results is None:
        with st.spinner("🔄 Analyzing materials and generating recommendations..."):
            try:
                stage2_data = st.session_state.stage2_data
                
                # Load materials from Excel (Book1.xlsx in stage4)
                excel_path = os.path.join(os.path.dirname(__file__), "..", "stage4", "Book1.xlsx")
                if os.path.exists(excel_path):
                    materials = load_materials(excel_path)
                    
                    summary = stage2_data["summary"]
                    wall_stats = {
                        "load_bearing_outer": summary.get("load_bearing_outer", 0),
                        "load_bearing_spine": summary.get("load_bearing_spine", 0),
                        "partition": summary.get("partition", 0),
                    }
                    # analyze_all(materials, wall_stats) — correct signature
                    tradeoff_results = analyze_all(materials, wall_stats)
                    
                    st.session_state.material_results = tradeoff_results
                    st.session_state.material_decisions = tradeoff_results
                    st.balloons()  # Celebration animation
                    st.success("🎉 Material Analysis Complete!")
                    
                    # Generate 3D model from try/try_app.py → build_threejs
                    try:
                        vision_data = vision_parse(st.session_state.uploaded_file_path)
                        output_dir = "output"
                        os.makedirs(output_dir, exist_ok=True)
                        material_3d_path = os.path.join(output_dir, "model_3d_materials.html")
                        
                        spec = importlib.util.spec_from_file_location(
                            "try_app",
                            os.path.join(sys_path_try, "try_app.py")
                        )
                        try_app_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(try_app_module)
                        
                        img_w = vision_data["summary"]["image_size"]["width"]
                        img_h = vision_data["summary"]["image_size"]["height"]
                        try_app_module.build_threejs(vision_data, img_w, img_h, material_3d_path)
                        st.session_state.material_3d_path = material_3d_path
                    except Exception as e:
                        st.warning(f"⚠️ 3D Material Model generation skipped: {str(e)}")
                        
                else:
                    st.warning("⚠️ Materials database (Book1.xlsx) not found. Skipping material analysis.")
                    st.session_state.material_results = {"status": "no_data"}
            except Exception as e:
                st.warning(f"⚠️ Material Analysis: {str(e)}")
                st.session_state.material_results = {"status": "error", "message": str(e)}
    
    if st.session_state.material_results:
        results = st.session_state.material_results
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if results.get("status") != "no_data":
            ELEMENT_LABELS = {
                "load_bearing_outer": ("🧱", "Outer Walls",  "#3b82f6"),
                "load_bearing_spine": ("🎯", "Spine Walls",  "#8b5cf6"),
                "partition":          ("📦", "Partitions",   "#10b981"),
                "slab":               ("🏗",  "Floor Slab",   "#f59e0b"),
                "column":             ("🔩", "Columns",      "#ef4444"),
            }
            SCORE_COLORS = ["#10b981", "#3b82f6", "#94a3b8"]  # rank 1,2,3

            for element, (icon, label, color) in ELEMENT_LABELS.items():
                recs = results.get(element, [])
                if not recs:
                    continue
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;
                            padding:24px;margin-bottom:20px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.04)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px">
                        <span style="font-size:22px">{icon}</span>
                        <span style="font-size:17px;font-weight:700;color:#0f172a">{label}</span>
                        <span style="margin-left:auto;font-size:11px;font-weight:600;
                                     color:{color};background:{color}18;
                                     padding:3px 10px;border-radius:20px;border:1px solid {color}44">
                            Top {len(recs)} Materials
                        </span>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
                """, unsafe_allow_html=True)

                for i, mat in enumerate(recs[:3]):
                    rank_color = SCORE_COLORS[i]
                    score = mat.get("tradeoff_score", 0)
                    bar_w = min(int(score / 6 * 100), 100)  # max score ~6
                    st.markdown(f"""
                    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                                padding:16px;position:relative">
                        <div style="position:absolute;top:12px;right:12px;width:26px;height:26px;
                                    border-radius:50%;background:{rank_color}18;
                                    border:2px solid {rank_color};
                                    display:flex;align-items:center;justify-content:center;
                                    font-size:11px;font-weight:800;color:{rank_color}">
                            #{mat.get('rank',i+1)}
                        </div>
                        <div style="font-size:14px;font-weight:700;color:#0f172a;
                                    margin-bottom:10px;padding-right:32px">
                            {mat.get('name','')}
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;
                                    gap:6px;margin-bottom:12px">
                            <div style="text-align:center;background:white;border-radius:8px;
                                        padding:6px 4px;border:1px solid #e2e8f0">
                                <div style="font-size:10px;color:#94a3b8;font-weight:600">STRENGTH</div>
                                <div style="font-size:12px;font-weight:700;color:#1e40af">{mat.get('strength_raw','')}</div>
                            </div>
                            <div style="text-align:center;background:white;border-radius:8px;
                                        padding:6px 4px;border:1px solid #e2e8f0">
                                <div style="font-size:10px;color:#94a3b8;font-weight:600">DURABILITY</div>
                                <div style="font-size:12px;font-weight:700;color:#059669">{mat.get('durability_raw','')}</div>
                            </div>
                            <div style="text-align:center;background:white;border-radius:8px;
                                        padding:6px 4px;border:1px solid #e2e8f0">
                                <div style="font-size:10px;color:#94a3b8;font-weight:600">COST</div>
                                <div style="font-size:12px;font-weight:700;color:#d97706">{mat.get('cost_raw','')}</div>
                            </div>
                        </div>
                        <div style="margin-bottom:6px">
                            <div style="display:flex;justify-content:space-between;
                                        font-size:11px;color:#64748b;margin-bottom:4px">
                                <span>Tradeoff Score</span>
                                <span style="font-weight:700;color:{rank_color}">{score}</span>
                            </div>
                            <div style="background:#e2e8f0;border-radius:4px;height:6px">
                                <div style="background:{rank_color};width:{bar_w}%;
                                            height:6px;border-radius:4px"></div>
                            </div>
                        </div>
                        <div style="font-size:11px;color:#64748b;line-height:1.5;
                                    border-top:1px solid #f1f5f9;padding-top:8px;margin-top:4px">
                            {mat.get('best_use','')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div></div>", unsafe_allow_html=True)

                # Explanation expander for top pick
                with st.expander(f"📋 Why {recs[0].get('name','')} for {label}?"):
                    st.markdown(f"> {recs[0].get('explanation','')}")
                    st.markdown(f"**Weight rationale:** {recs[0].get('weight_rationale','')}")

            
            # Display 3D model with material recommendations
            if st.session_state.material_3d_path and os.path.exists(st.session_state.material_3d_path):
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("""
                <div class="result-box">
                    <div class="result-title">🧊 3D Model with Material Colors</div>
                    <p style="color: #64748b; margin-bottom: 16px; font-size: 14px;">
                        Visualization showing recommended materials color-coded by structural element type
                    </p>
                """, unsafe_allow_html=True)
                
                with open(st.session_state.material_3d_path, "r") as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=700, scrolling=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_chrome, col_spacer = st.columns([1, 2])
                with col_chrome:
                    if st.button("🌐 Open 3D Model in Chrome", key="open_material_chrome", use_container_width=True):
                        abs_path = os.path.abspath(st.session_state.material_3d_path)
                        webbrowser.open(f"file:///{abs_path}", new=2)
                        st.success("✓ Opening in Chrome...")
        else:
            st.markdown("""
            <div class="info-box">
                <p><strong>ℹ️ Note:</strong> Material analysis database not available. Proceeding to AI report generation.</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", key="back_4", use_container_width=True):
            st.session_state.current_stage = 3
            st.rerun()
    with col2:
        st.markdown("")  # Spacer
    with col3:
        if st.button("➡️ Next: AI Report", key="next_4", use_container_width=True):
            st.session_state.current_stage = 5
            st.rerun()

# ─── STAGE 5 NEXT BUTTON → STAGE 6 ──────────────────────────────────────

# ─── STAGE 5: AI REPORT ──────────────────────────────────────────────────
elif st.session_state.current_stage == 5:
    # Breadcrumb
    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item active">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<h1 class="stage-header">🤖 AI Structural Report</h1>', unsafe_allow_html=True)
    st.markdown('Comprehensive analysis powered by Gemini AI', unsafe_allow_html=True)
    
    # Progress bar
    st.progress(5/7, text="Stage 5 of 7")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    if st.session_state.ai_report is None:
        with st.spinner("🔄 Generating AI-powered structural report..."):
            try:
                stage2_data = st.session_state.stage2_data
                material_data = st.session_state.material_decisions or {}

                stage2_for_prompt = {
                    "summary": stage2_data["summary"],
                    "image_size": stage2_data["image_size"],
                }

                prompt = build_prompt(stage2_for_prompt, material_data)
                ai_report = call_gemini(prompt, GEMINI_API_KEY, stream=False)
                st.session_state.ai_report = ai_report
                st.balloons()  # Celebration animation
                st.success("🎉 AI Report Generated!")
            except Exception as e:
                st.session_state.ai_report = f"Report generation encountered an issue: {str(e)}"
    
    if st.session_state.ai_report:
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <div class="result-box">
            <div class="result-title">📄 Structural Analysis Report</div>
        """, unsafe_allow_html=True)

        report = st.session_state.ai_report

        # Render each section with styled headers; let st.markdown handle inline markdown
        import re
        sections = re.split(r'(?m)^(#{1,3} .+|\d+\. [A-Z].+)$', report)
        output_parts = []
        i = 0
        while i < len(sections):
            part = sections[i].strip()
            if not part:
                i += 1
                continue
            # Section heading (numbered or markdown #)
            if re.match(r'^(#{1,3} |\d+\. [A-Z])', part):
                clean = re.sub(r'^#+\s*', '', part)
                output_parts.append(
                    f"<h3 style='color:#1e40af;margin-top:28px;margin-bottom:10px;"
                    f"border-bottom:2px solid #3b82f6;padding-bottom:6px;'>{clean}</h3>"
                )
            else:
                # Render body text as markdown (handles **bold**, bullet lists, etc.)
                st.markdown(
                    "\n".join(output_parts) if output_parts else "",
                    unsafe_allow_html=True
                )
                output_parts = []
                st.markdown(part)
            i += 1

        if output_parts:
            st.markdown("\n".join(output_parts), unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", key="back_5", use_container_width=True):
            st.session_state.current_stage = 4
            st.rerun()
    with col2:
        if st.button("🔄 Start New Analysis", key="restart_5", use_container_width=True):
            for key in ["current_stage","uploaded_file_path","ocr_results","vision_results",
                        "model_3d_path","stage2_data","material_results","material_3d_path",
                        "material_decisions","ai_report","blockchain_result","floor_hash"]:
                st.session_state[key] = None
            st.session_state.current_stage = 0
            st.rerun()
    with col3:
        if st.button("➡️ Next: Blockchain", key="next_5", use_container_width=True):
            st.session_state.current_stage = 6
            st.rerun()

# ─── STAGE 6: BLOCKCHAIN ─────────────────────────────────────────────────
elif st.session_state.current_stage == 6:
    import hashlib
    import requests as req

    st.markdown("""
<div class="stage-breadcrumb">
    <div class="breadcrumb-item">Upload</div>
    <span>→</span>
    <div class="breadcrumb-item">OCR Detection</div>
    <span>→</span>
    <div class="breadcrumb-item">Vision Analysis</div>
    <span>→</span>
    <div class="breadcrumb-item">3D Model</div>
    <span>→</span>
    <div class="breadcrumb-item">Materials</div>
    <span>→</span>
    <div class="breadcrumb-item">AI Report</div>
    <span>→</span>
    <div class="breadcrumb-item active">⛓ Blockchain</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<h1 class="stage-header">⛓ Blockchain Audit — Stellar Soroban</h1>', unsafe_allow_html=True)
    st.markdown('Anchor your structural analysis permanently on the Stellar blockchain', unsafe_allow_html=True)
    st.progress(7/7, text="Stage 7 of 7 — Complete!")

    CONTRACT_ID = "CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J"
    FLASK_URL   = "http://localhost:5050"

    # ── Auto-populate from pipeline ──────────────────────────────
    stage2   = st.session_state.stage2_data or {}
    summary  = stage2.get("summary", {})
    mat      = st.session_state.material_decisions or {}
    report   = st.session_state.ai_report or ""

    def _top(element):
        recs = mat.get(element, [])
        return recs[0]["name"] if recs and isinstance(recs, list) and len(recs) > 0 else "N/A"

    # Generate floor hash from uploaded image
    if st.session_state.floor_hash is None and st.session_state.uploaded_file_path:
        with open(st.session_state.uploaded_file_path, "rb") as f:
            st.session_state.floor_hash = hashlib.sha256(f.read()).hexdigest()[:32]

    floor_hash = st.session_state.floor_hash or "no-hash"

    # ── Contract Info Bar ────────────────────────────────────────
    st.markdown(f"""
    <div style="background:var(--beige-light);border:1px solid var(--border);border-radius:12px;
                padding:14px 20px;margin-bottom:24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
        <span style="font-size:12px;font-weight:700;color:var(--text-secondary);text-transform:uppercase">Contract ID</span>
        <code style="background:var(--off-white);color:var(--primary-dark);padding:4px 10px;border-radius:6px;
                     border:1px solid var(--border);font-size:13px">{CONTRACT_ID}</code>
        <a href="https://stellar.expert/explorer/testnet/contract/{CONTRACT_ID}"
           target="_blank"
           style="color:var(--primary);font-size:13px;margin-left:auto">View on Stellar Explorer ↗</a>
    </div>
    """, unsafe_allow_html=True)

    # ── What can you do here? ────────────────────────────────────
    st.components.v1.html("""
<div style="background:linear-gradient(135deg,var(--beige-light) 0%,var(--beige-medium) 100%);border:1px solid var(--border);border-radius:16px;padding:28px;margin-bottom:28px;font-family:Georgia,serif">
<p style="color:var(--primary-dark);font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:18px;margin-top:0">&#9939; What can you do on this page?</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">

<div style="background:var(--off-white);border:1px solid var(--primary-light);border-radius:12px;padding:18px">
<div style="font-size:22px;margin-bottom:8px">&#128228;</div>
<div style="color:var(--text-primary);font-weight:700;font-size:14px;margin-bottom:6px">Anchor Report</div>
<div style="color:var(--text-secondary);font-size:13px;line-height:1.6">Permanently record your AI structural analysis on the Stellar blockchain. Once anchored, the report hash, materials, wall counts and your wallet address are stored forever — nobody can alter or dispute them.</div>
<div style="margin-top:10px;padding:8px 12px;background:var(--beige-light);border-radius:8px;border:1px solid var(--primary-light)"><span style="color:var(--primary);font-size:12px">&#128073; Use this after completing Stage 5 to certify your report</span></div>
</div>

<div style="background:var(--off-white);border:1px solid var(--accent);border-radius:12px;padding:18px">
<div style="font-size:22px;margin-bottom:8px">&#128269;</div>
<div style="color:var(--text-primary);font-weight:700;font-size:14px;margin-bottom:6px">Verify Certificate</div>
<div style="color:var(--text-secondary);font-size:13px;line-height:1.6">Anyone — a client, bank, inspector or regulator — can paste a floor plan hash and instantly verify the report exists on-chain and was not tampered with. No trust required. The blockchain answers.</div>
<div style="margin-top:10px;padding:8px 12px;background:var(--beige-light);border-radius:8px;border:1px solid var(--accent)"><span style="color:var(--accent);font-size:12px">&#128073; Use this to prove your report is authentic to any third party</span></div>
</div>

<div style="background:var(--off-white);border:1px solid var(--success);border-radius:12px;padding:18px">
<div style="font-size:22px;margin-bottom:8px">&#128100;</div>
<div style="color:var(--text-primary);font-weight:700;font-size:14px;margin-bottom:6px">Ownership Registry</div>
<div style="color:var(--text-secondary);font-size:13px;line-height:1.6">Look up which wallet address registered a floor plan design on-chain. Proves who submitted which design and when — immutable IP ownership proof for architects and structural engineers.</div>
<div style="margin-top:10px;padding:8px 12px;background:var(--beige-light);border-radius:8px;border:1px solid var(--success)"><span style="color:var(--success);font-size:12px">&#128073; Use this to prove you own the floor plan design</span></div>
</div>

<div style="background:var(--off-white);border:1px solid var(--warning);border-radius:12px;padding:18px">
<div style="font-size:22px;margin-bottom:8px">&#128218;</div>
<div style="color:var(--text-primary);font-weight:700;font-size:14px;margin-bottom:6px">On-Chain Registry</div>
<div style="color:var(--text-secondary);font-size:13px;line-height:1.6">Browse every floor plan analysis ever anchored on Stellar. A complete, tamper-proof audit trail of all projects — useful for regulators, construction companies and compliance audits.</div>
<div style="margin-top:10px;padding:8px 12px;background:var(--beige-light);border-radius:8px;border:1px solid var(--warning)"><span style="color:var(--warning);font-size:12px">&#128073; Use this to show all projects went through proper analysis</span></div>
</div>

</div>
<div style="margin-top:18px;padding:14px 18px;background:var(--beige-light);border-radius:10px;border:1px solid var(--border);display:flex;align-items:center;gap:12px">
<span style="font-size:20px">&#128161;</span>
<span style="color:var(--text-secondary);font-size:13px"><strong style="color:var(--text-primary)">Flask server must be running</strong> for blockchain features to work. Open a separate terminal and run: <code style="background:var(--beige-medium);color:var(--primary);padding:2px 8px;border-radius:4px;margin-left:6px">cd web3 && python app.py</code> — then come back here.</span>
</div>
</div>
""", height=420)

        # ── Tabs ─────────────────────────────────────────────────────
    tab_anchor, tab_verify, tab_owner, tab_registry = st.tabs([
        "📤 Anchor Report", "🔍 Verify Certificate", "👤 Ownership Registry", "📚 On-Chain Registry"
    ])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — ANCHOR REPORT (Feature A + B + C)
    # ════════════════════════════════════════════════════════════
    with tab_anchor:
        st.markdown("### 📤 Anchor Analysis on Stellar Blockchain")
        st.markdown("All fields are auto-filled from your pipeline. Review and click Anchor.")
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔐 Floor Plan Hash (SHA-256)**")
            st.code(floor_hash, language=None)
            outer_walls = st.number_input("Outer Walls", value=summary.get("load_bearing_outer", 0), min_value=0)
            spine_walls = st.number_input("Spine Walls", value=summary.get("load_bearing_spine", 0), min_value=0)
            partitions  = st.number_input("Partition Walls", value=summary.get("partition", 0), min_value=0)

        with col2:
            mat_outer = st.text_input("Top Material — Outer Walls",  value=_top("load_bearing_outer"))
            mat_spine = st.text_input("Top Material — Spine Walls",  value=_top("load_bearing_spine"))
            mat_part  = st.text_input("Top Material — Partitions",   value=_top("partition"))
            mat_slab  = st.text_input("Top Material — Slab",         value=_top("slab"))
            mat_col   = st.text_input("Top Material — Columns",      value=_top("column"))

        report_summary = st.text_area("AI Report Summary (first 200 chars)",
                                      value=report[:200], height=80)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("⛓ Anchor on Stellar Blockchain", key="anchor_btn", use_container_width=True):
            with st.spinner("Sending transaction to Stellar testnet..."):
                try:
                    payload = {
                        "floor_hash":         floor_hash,
                        "outer_walls":        int(outer_walls),
                        "spine_walls":        int(spine_walls),
                        "partitions":         int(partitions),
                        "top_material_outer": mat_outer,
                        "top_material_spine": mat_spine,
                        "top_material_part":  mat_part,
                        "top_material_slab":  mat_slab,
                        "top_material_col":   mat_col,
                        "report_summary":     report_summary[:200],
                    }
                    r = req.post(f"{FLASK_URL}/api/store_report", json=payload, timeout=60)
                    data = r.json()
                    st.session_state.blockchain_result = data

                    if data.get("success"):
                        tx = data.get("tx_hash", "")
                        compliance = data.get("compliance", False)
                        st.success("✅ Report anchored on Stellar blockchain!")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Floor Hash", floor_hash[:16] + "...")
                        col_b.metric("Compliance", "✅ PASS" if compliance else "⚠️ REVIEW")
                        col_c.metric("Network", "Stellar Testnet")
                        st.markdown(f"""
                        <div style="background:#0f2a1a;border:1px solid #10b981;border-radius:12px;padding:20px;margin-top:16px">
                            <p style="color:#6ee7b7;margin:0 0 8px 0">⛓ <strong>Transaction Hash</strong></p>
                            <code style="color:#a7f3d0;font-size:13px">{tx}</code><br><br>
                            <a href="https://stellar.expert/explorer/testnet/tx/{tx}" target="_blank"
                               style="color:#06b6d4">View transaction on Stellar Explorer ↗</a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {data.get('error', 'Unknown error')}")
                        st.info("💡 Make sure the Flask blockchain server is running: `python web3/app.py`")
                except Exception as e:
                    st.error(f"❌ Could not connect to blockchain server: {e}")
                    st.info("💡 Start the Flask server first: `cd web3 && python app.py`")

    # ════════════════════════════════════════════════════════════
    # TAB 2 — VERIFY CERTIFICATE (Feature A)
    # ════════════════════════════════════════════════════════════
    with tab_verify:
        st.markdown("### 🔍 Verify Audit Certificate")
        st.markdown("Enter a floor plan hash to retrieve its on-chain audit certificate.")
        st.markdown("<br>", unsafe_allow_html=True)

        verify_hash = st.text_input("Floor Plan Hash", value=floor_hash,
                                    placeholder="32-char SHA-256 hash...")
        if st.button("🔍 Verify on Blockchain", key="verify_btn", use_container_width=True):
            with st.spinner("Querying Stellar blockchain..."):
                try:
                    r    = req.get(f"{FLASK_URL}/api/get_report/{verify_hash}", timeout=30)
                    data = r.json()
                    if data.get("success"):
                        st.success("✅ Audit Certificate Found on Stellar Blockchain")
                        st.markdown(f"""
                        <div style="background:var(--beige-light);border:1px solid var(--success);border-radius:12px;padding:24px;margin-top:12px">
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
                                <div style="background:var(--off-white);border-radius:10px;padding:14px">
                                    <div style="color:var(--success);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">🔐 Floor Hash</div>
                                    <div style="color:var(--text-primary);font-size:13px;font-family:monospace;word-break:break-all">{verify_hash}</div>
                                </div>
                                <div style="background:var(--off-white);border-radius:10px;padding:14px">
                                    <div style="color:var(--success);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">✅ Status</div>
                                    <div style="color:var(--success);font-size:14px;font-weight:700">Verified — Immutable on Stellar</div>
                                </div>
                            </div>
                            <div style="background:var(--off-white);border-radius:10px;padding:14px">
                                <div style="color:var(--success);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">🌐 Network</div>
                                <div style="color:var(--primary);font-size:13px">Stellar Testnet · Soroban Smart Contract</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {data.get('error', 'Not found')}")
                except Exception as e:
                    st.error(f"❌ {e}")
                    st.info("💡 Start the Flask server: `cd web3 && python app.py`")

    # ════════════════════════════════════════════════════════════
    # TAB 3 — OWNERSHIP REGISTRY (Feature C)
    # ════════════════════════════════════════════════════════════
    with tab_owner:
        st.markdown("### 👤 Floor Plan Ownership Registry")
        st.markdown("Check who registered a floor plan design on-chain. Immutable IP proof.")
        st.markdown("<br>", unsafe_allow_html=True)

        owner_hash = st.text_input("Floor Plan Hash", value=floor_hash,
                                   placeholder="32-char SHA-256 hash...", key="owner_hash_input")
        if st.button("👤 Check Ownership", key="owner_btn", use_container_width=True):
            with st.spinner("Looking up ownership registry..."):
                try:
                    r    = req.get(f"{FLASK_URL}/api/get_owner/{owner_hash}", timeout=30)
                    data = r.json()
                    if data.get("success"):
                        st.success("✅ Ownership Record Found")
                        wallet = data.get('result_xdr', 'N/A')
                        short_wallet = wallet[:16] + "..." + wallet[-8:] if len(wallet) > 28 else wallet
                        st.markdown(f"""
                        <div style="background:var(--beige-light);border:1px solid var(--success);border-radius:12px;padding:24px;margin-top:12px">
                            <div style="background:var(--off-white);border-radius:10px;padding:14px;margin-bottom:12px">
                                <div style="color:var(--success);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">📋 Floor Hash</div>
                                <div style="color:var(--text-primary);font-size:13px;font-family:monospace">{owner_hash}</div>
                            </div>
                            <div style="background:var(--off-white);border-radius:10px;padding:14px;margin-bottom:12px">
                                <div style="color:var(--success);font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:6px">👤 Registered Owner Wallet</div>
                                <div style="color:var(--success);font-size:14px;font-family:monospace;font-weight:700;word-break:break-all">{wallet}</div>
                            </div>
                            <div style="color:var(--text-secondary);font-size:12px;padding:10px 14px;background:var(--beige-medium);border-radius:8px">
                                ✅ Immutably recorded on Stellar Soroban — cannot be altered or disputed
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {data.get('error', 'Not found')}")
                except Exception as e:
                    st.error(f"❌ {e}")
                    st.info("💡 Start the Flask server: `cd web3 && python app.py`")

    # ════════════════════════════════════════════════════════════
    # TAB 4 — ON-CHAIN REGISTRY (Feature B)
    # ════════════════════════════════════════════════════════════
    with tab_registry:
        st.markdown("### 📚 On-Chain Material Procurement Registry")
        st.markdown("All material recommendations ever anchored on Stellar — the immutable procurement ledger.")
        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        col_b.metric("Network", "Stellar Testnet")
        col_c.metric("Contract", "Soroban")

        if st.button("🔄 Load Registry from Blockchain", key="registry_btn", use_container_width=True):
            with st.spinner("Fetching on-chain registry..."):
                try:
                    # Get count
                    rc   = req.get(f"{FLASK_URL}/api/report_count", timeout=30).json()
                    count = rc.get("result_xdr", "?") if rc.get("success") else "?"
                    col_a.metric("Reports On-Chain", count)

                    # Get all hashes
                    rh   = req.get(f"{FLASK_URL}/api/all_hashes", timeout=30).json()
                    if rh.get("success"):
                        st.success("✅ Registry loaded from Stellar blockchain")
                        raw_xdr = rh.get('result_xdr', '') or ''
                        # Try to split into individual hashes if comma/bracket separated
                        import re as _re
                        hash_list = _re.findall(r'[a-f0-9]{32}', raw_xdr)
                        if hash_list:
                            st.markdown(f"""
                            <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;
                                        padding:20px;margin-top:12px">
                                <div style="color:#94a3b8;font-size:12px;font-weight:700;
                                            text-transform:uppercase;margin-bottom:14px">
                                    📚 {len(hash_list)} Floor Plan{'s' if len(hash_list)!=1 else ''} Registered On-Chain
                                </div>
                            """, unsafe_allow_html=True)
                            for idx, h in enumerate(hash_list):
                                st.markdown(f"""
                                <div style="display:flex;align-items:center;gap:12px;
                                            padding:10px 14px;margin-bottom:8px;
                                            background:#1e293b;border-radius:8px;
                                            border:1px solid #334155">
                                    <span style="color:#64748b;font-size:12px;min-width:24px">#{idx+1}</span>
                                    <code style="color:#67e8f9;font-size:12px;flex:1">{h}</code>
                                </div>
                                """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background:var(--beige-light);border:1px solid var(--border);border-radius:12px;
                                        padding:20px;margin-top:12px">
                                <div style="color:var(--text-secondary);font-size:13px;margin-bottom:8px">📚 On-Chain Registry Data</div>
                                <div style="color:var(--primary);font-size:12px;font-family:monospace;
                                            word-break:break-all">{raw_xdr[:300]}{'...' if len(raw_xdr)>300 else ''}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {rh.get('error')}")
                except Exception as e:
                    st.error(f"❌ {e}")
                    st.info("💡 Start the Flask server: `cd web3 && python app.py`")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:var(--beige-light);border:1px solid var(--border);border-radius:12px;padding:20px">
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:8px">🔗 <strong style='color:var(--text-primary)'>Block Explorer</strong></p>
            <a href="https://stellar.expert/explorer/testnet/contract/{CONTRACT_ID}" target="_blank"
               style="color:var(--primary);font-size:14px">stellar.expert/explorer/testnet/contract/{CONTRACT_ID} ↗</a>
        </div>
        """, unsafe_allow_html=True)

    # ── Navigation ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", key="back_6", use_container_width=True):
            st.session_state.current_stage = 5
            st.rerun()
    with col2:
        if st.button("🔄 Start New Analysis", key="restart", use_container_width=True):
            for key in ["current_stage","uploaded_file_path","ocr_results","vision_results",
                        "model_3d_path","stage2_data","material_results","material_3d_path",
                        "material_decisions","ai_report","blockchain_result","floor_hash"]:
                st.session_state[key] = None
            st.session_state.current_stage = 0
            st.rerun()
    with col3:
        if st.button("💾 Download Report", key="download", use_container_width=True):
            if st.session_state.ai_report:
                st.download_button(
                    label="📄 Download as .txt",
                    data=st.session_state.ai_report,
                    file_name=f"ASIS_report_{floor_hash[:8]}.txt",
                    mime="text/plain",
                    key="dl_btn"
                )
