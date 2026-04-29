"""
ShadowLens — Advanced Steganography Analysis & Detection Suite
Main Streamlit Application
"""

import io
import base64
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="ShadowLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Modern Color Palette - Cyberpunk/Dark Professional */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-tertiary: #1f2937;
        --bg-card: #161b2e;
        --accent-primary: #00d4aa;
        --accent-secondary: #06b6d4;
        --accent-glow: rgba(0, 212, 170, 0.3);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
        --border: #2d3748;
        --gradient-1: linear-gradient(135deg, #00d4aa 0%, #06b6d4 100%);
        --gradient-2: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Global Reset */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Typography - Bigger and bolder */
    h1 {
        font-family: 'Inter', sans-serif !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        background: var(--gradient-1) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.02em !important;
    }
    
    h2 {
        font-family: 'Inter', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        border-left: 4px solid var(--accent-primary);
        padding-left: 1rem;
    }
    
    h3 {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: var(--accent-secondary) !important;
        margin-top: 1.5rem !important;
    }
    
    p, li {
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        color: var(--text-secondary);
    }
    
    /* Sidebar - Modern Glassmorphism */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    /* Sidebar Title */
    .sidebar-title {
        font-size: 2rem;
        font-weight: 700;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Navigation Radio - Bigger */
    .stRadio > label {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        border-radius: 12px !important;
        transition: all 0.2s ease !important;
    }
    
    .stRadio > div[role="radiogroup"] > label {
        background: var(--bg-tertiary) !important;
        border: 2px solid transparent !important;
    }
    
    .stRadio > div[role="radiogroup"] > label:hover {
        background: var(--bg-card) !important;
        border-color: var(--accent-primary) !important;
        transform: translateX(4px);
    }
    
    /* Buttons - Modern and bigger */
    .stButton > button {
        background: var(--gradient-1) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 0.875rem 2rem !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px var(--accent-glow) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px var(--accent-glow) !important;
        filter: brightness(1.1) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 2px solid var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        box-shadow: none !important;
    }
    
    /* File uploader - Modern styling */
    .stFileUploader {
        background: var(--bg-tertiary) !important;
        border: 2px dashed var(--accent-secondary) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader:hover {
        border-color: var(--accent-primary) !important;
        background: var(--bg-card) !important;
        box-shadow: 0 0 30px var(--accent-glow) !important;
    }
    
    /* Input fields - Bigger */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-tertiary) !important;
        border: 2px solid var(--border) !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1rem !important;
        color: var(--text-primary) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    
    /* Selectbox - Bigger */
    .stSelectbox > div > div > div {
        background: var(--bg-tertiary) !important;
        border: 2px solid var(--border) !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
    }
    
    /* Metric cards - Glassmorphism style */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(31, 41, 55, 0.8) 0%, rgba(17, 24, 39, 0.9) 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stMetric"] > div:first-child {
        font-size: 0.9rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }
    
    [data-testid="stMetric"] > div:last-child {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Status banners - Enhanced with icons and gradients */
    .status-clean {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 2px solid var(--success);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
    }
    
    .status-suspicious {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
        border: 2px solid var(--warning);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
    }
    
    .status-danger {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%);
        border: 2px solid var(--danger);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
    }
    
    /* Code blocks - Modern terminal style */
    code {
        background: var(--bg-tertiary) !important;
        color: var(--accent-primary) !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 6px !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.95rem !important;
        border: 1px solid var(--border);
    }
    
    pre code {
        display: block;
        padding: 1rem !important;
        overflow-x: auto;
    }
    
    /* Expanders - Modern cards */
    .streamlit-expander {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 1rem 1.25rem !important;
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Progress bars - Animated gradient */
    .stProgress > div > div {
        background: var(--gradient-1) !important;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 2rem 0;
    }
    
    /* Info boxes */
    .stInfo, .stWarning, .stError, .stSuccess {
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-size: 1.05rem !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid var(--info) !important;
    }
    
    /* Image containers */
    [data-testid="stImage"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Data frames / Tables */
    .dataframe {
        font-size: 1rem !important;
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid var(--border) !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main > div {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Glow effects for important elements */
    .glow-text {
        text-shadow: 0 0 20px var(--accent-glow);
    }
    
    /* Card component style */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        border-color: var(--accent-primary);
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Import core modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer import Steganalyzer
from core.embedder import Embedder
from core.extractor import Extractor
from core.report import ReportGenerator
from core.utils import (
    get_all_bit_planes, calculate_file_hash, format_bytes_readable,
    image_to_bytes, calculate_image_capacity
)


def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'stego_image' not in st.session_state:
        st.session_state.stego_image = None


def render_sidebar():
    """Render the sidebar with navigation and file upload."""
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 2rem 1rem 1.5rem; margin-bottom: 1rem;">
        <div style="font-size: 3.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 15px rgba(0, 212, 170, 0.5));">🔍</div>
        <h1 style="
            font-family: 'Inter', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00d4aa 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.02em;
        ">ShadowLens</h1>
        <p style="color: #64748b; font-size: 1rem; font-weight: 500; margin: 0;">
            Steganography Suite
        </p>
        <div style="
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: rgba(0, 212, 170, 0.1);
            border: 1px solid rgba(0, 212, 170, 0.3);
            border-radius: 20px;
            display: inline-block;
        ">
            <span style="color: #00d4aa; font-size: 0.85rem; font-weight: 600;">v1.0</span>
        </div>
    </div>
    
    <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, #2d3748, transparent); margin: 1rem 0;">
    
    <div style="padding: 0 0.5rem;">
        <p style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 1rem 1rem;">Navigation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    page = st.sidebar.radio(
        "",
        ["📊 Analyze", "📝 Hide", "🔓 Extract", "🔬 Bit Planes", "ℹ️ About"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # File uploader (common across most pages)
    if page != "ℹ️ About":
        st.sidebar.markdown("""
        <div style="padding: 0 0.5rem; margin-bottom: 1rem;">
            <p style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 1rem 0.5rem;">
                📁 File Upload
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        accepted_types = ['png', 'bmp', 'tiff', 'tif', 'jpg', 'jpeg', 'wav', 'txt']
        uploaded = st.sidebar.file_uploader(
            "📂 Drop file or click to browse",
            type=accepted_types,
            help="Supports: PNG, BMP, TIFF, JPG, WAV, TXT"
        )
        
        if uploaded:
            st.session_state.uploaded_file = uploaded
            
            # Show file info in modern card style
            st.sidebar.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(31, 41, 55, 0.8) 0%, rgba(17, 24, 39, 0.9) 100%);
                border: 1px solid #2d3748;
                border-radius: 12px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <p style="color: #64748b; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 0.75rem 0;">📊 File Information</p>
            """, unsafe_allow_html=True)
            
            st.sidebar.markdown(f"<p style='margin: 0.25rem 0; font-size: 0.9rem;'><span style='color: #94a3b8;'>Name:</span> <code style='font-size: 0.8rem;'>{uploaded.name}</code></p>", unsafe_allow_html=True)
            st.sidebar.markdown(f"<p style='margin: 0.25rem 0; font-size: 0.9rem;'><span style='color: #94a3b8;'>Size:</span> <span style='color: #00d4aa; font-weight: 600;'>{format_bytes_readable(len(uploaded.getvalue()))}</span></p>", unsafe_allow_html=True)
            
            # Calculate hash - save to temp file first
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = Path(tmp.name)
            file_hash = calculate_file_hash(tmp_path)
            st.sidebar.markdown(f"<p style='margin: 0.25rem 0; font-size: 0.9rem;'><span style='color: #94a3b8;'>MD5:</span> <code style='font-size: 0.75rem;'>{file_hash[:16]}...</code></p>", unsafe_allow_html=True)
            # Clean up temp file
            try:
                tmp_path.unlink()
            except:
                pass
            
            # Image-specific info
            if uploaded.name.lower().endswith(('.png', '.bmp', '.tiff', '.tif', '.jpg', '.jpeg')):
                try:
                    img = Image.open(io.BytesIO(uploaded.getvalue()))
                    st.sidebar.markdown(f"<p style='margin: 0.25rem 0; font-size: 0.9rem;'><span style='color: #94a3b8;'>Dimensions:</span> <span style='color: #f1f5f9;'>{img.size[0]} × {img.size[1]}</span></p>", unsafe_allow_html=True)
                    st.sidebar.markdown(f"<p style='margin: 0.25rem 0; font-size: 0.9rem;'><span style='color: #94a3b8;'>Mode:</span> <span style='color: #f1f5f9;'>{img.mode}</span></p>", unsafe_allow_html=True)
                except Exception:
                    pass
            
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem; margin-top: 1rem;">
        <p style="color: #475569; font-size: 0.8rem; font-weight: 500; margin: 0;">
            <span style="color: #00d4aa;">●</span> ShadowLens v1.0
        </p>
        <p style="color: #334155; font-size: 0.7rem; margin: 0.25rem 0 0 0;">
            Advanced Steganography Suite
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    return page


def render_analyze_page():
    """Render the Analyze page."""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin: 0; font-size: 3rem;">📊 Steganalysis</h1>
        <p style="font-size: 1.25rem; color: #94a3b8; margin: 0.5rem 0 0 0; line-height: 1.6;">
            Detect and analyze hidden data using <strong style="color: #00d4aa;">9 professional algorithms</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.uploaded_file is None:
        st.info("👆 Upload an image in the sidebar to begin analysis.")
        return
    
    uploaded = st.session_state.uploaded_file
    
    # Only process images on this page
    if not uploaded.name.lower().endswith(('.png', '.bmp', '.tiff', '.tif', '.jpg', '.jpeg')):
        st.warning("⚠️ This page only supports image files. Please upload an image.")
        return
    
    # Analysis button
    if st.button("🔍 Run Full Analysis", type="primary", use_container_width=True):
        with st.spinner("Running steganalysis... This may take a moment."):
            progress_bar = st.progress(0)
            
            # Save to temp file
            temp_path = Path("temp_analyze.png")
            with open(temp_path, "wb") as f:
                f.write(uploaded.getvalue())
            
            # Run analysis
            analyzer = Steganalyzer()
            progress_bar.progress(30)
            
            results = analyzer.analyze(temp_path)
            progress_bar.progress(80)
            
            st.session_state.analysis_results = results
            
            progress_bar.progress(100)
            progress_bar.empty()
        
        st.success("✅ Analysis complete!")
    
    # Display results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Verdict banner
        verdict = results.get('verdict', {})
        classification = verdict.get('classification', 'UNKNOWN')
        confidence = verdict.get('confidence', 0.0) * 100
        description = verdict.get('description', '')
        color = verdict.get('color', 'gray')
        
        if color == 'green':
            st.markdown(f"""
            <div class="status-clean">
                <h2 style="color: #00ff88; margin: 0;">✅ {classification}</h2>
                <p style="margin: 5px 0 0 0;"><strong>Confidence:</strong> {confidence:.1f}%</p>
                <p style="margin: 5px 0 0 0; color: #8b949e;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
        elif color == 'yellow':
            st.markdown(f"""
            <div class="status-suspicious">
                <h2 style="color: #ffd700; margin: 0;">⚠️ {classification}</h2>
                <p style="margin: 5px 0 0 0;"><strong>Confidence:</strong> {confidence:.1f}%</p>
                <p style="margin: 5px 0 0 0; color: #8b949e;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-danger">
                <h2 style="color: #ff4444; margin: 0;">🚨 {classification}</h2>
                <p style="margin: 5px 0 0 0;"><strong>Confidence:</strong> {confidence:.1f}%</p>
                <p style="margin: 5px 0 0 0; color: #8b949e;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Combined score
        score = results.get('combined_score', 0.0) * 100
        st.markdown("### Overall Suspicion Score")
        st.progress(score / 100)
        st.markdown(f"**{score:.1f}%** suspicion indicator")
        
        st.markdown("---")
        
        # Individual test results
        st.markdown("### 🔬 Detailed Test Results")
        
        tests = [
            ('lsb_analysis', 'LSB Analysis', 'Analyzes LSB randomness across channels'),
            ('chi_square', 'Chi-Square Attack', 'Statistical test for LSB steganography'),
            ('rs_analysis', 'RS Analysis', 'Fridrich et al. RS steganalysis'),
            ('sample_pairs', 'Sample Pairs', 'Dumitrescu et al. pair analysis'),
            ('histogram', 'Histogram Analysis', 'Detects histogram anomalies'),
            ('noise', 'Noise Estimation', 'Laplacian variance analysis'),
            ('dct_analysis', 'DCT Analysis', 'JPEG coefficient analysis'),
            ('metadata', 'Metadata Analysis', 'EXIF and file structure check')
        ]
        
        cols = st.columns(2)
        
        for idx, (key, name, desc) in enumerate(tests):
            with cols[idx % 2]:
                if key in results and isinstance(results[key], dict):
                    result = results[key]
                    
                    detected = result.get('detected', False)
                    suspicious = result.get('suspicious', False)
                    
                    # Determine status
                    if detected or suspicious:
                        status_icon = "🚨"
                        status_color = "#ff4444"
                        status_text = "SUSPICIOUS"
                    else:
                        status_icon = "✅"
                        status_color = "#00ff88"
                        status_text = "PASS"
                    
                    with st.expander(f"{status_icon} {name}"):
                        st.markdown(f"<span style='color: {status_color}; font-weight: bold;'>{status_text}</span>", unsafe_allow_html=True)
                        st.markdown(f"*{desc}*")
                        
                        # Show specific metrics
                        if key == 'lsb_analysis' and 'overall_suspicion' in result:
                            st.markdown(f"**Overall Suspicion:** {result['overall_suspicion']*100:.1f}%")
                        elif key == 'chi_square' and 'overall_confidence' in result:
                            st.markdown(f"**Confidence:** {result['overall_confidence']*100:.1f}%")
                        elif key == 'rs_analysis' and 'estimated_payload_percent' in result:
                            st.markdown(f"**Estimated Payload:** {result['estimated_payload_percent']:.2f}%")
                        elif key == 'sample_pairs' and 'estimated_embedding_rate' in result:
                            st.markdown(f"**Embedding Rate:** {result['estimated_embedding_rate']*100:.2f}%")
        
        # Histogram visualization
        st.markdown("---")
        st.markdown("### 📊 Histogram Analysis")
        
        if 'histogram' in results:
            hist_data = results['histogram'].get('histogram_data', {})
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Red Channel', 'Green Channel', 'Blue Channel')
            )
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            
            for idx, (ch_name, data) in enumerate(hist_data.items()):
                if idx >= 3:
                    break
                
                fig.add_trace(
                    go.Histogram(
                        x=data,
                        nbinsx=50,
                        name=f'{ch_name}',
                        marker_color=colors[idx],
                        opacity=0.75
                    ),
                    row=1, col=idx + 1
                )
            
            fig.update_layout(
                height=300,
                template='plotly_dark',
                paper_bgcolor='#161b22',
                plot_bgcolor='#0d1117',
                font=dict(color='#c9d1d9'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Download report button
        st.markdown("---")
        if st.button("📄 Generate HTML Report", use_container_width=True):
            with st.spinner("Generating report..."):
                generator = ReportGenerator()
                temp_path = Path("temp_analyze.png")
                html = generator.generate_analysis_report(temp_path, results)
                
                # Provide download
                b64 = base64.b64encode(html.encode()).decode()
                filename = f"shadowlens_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                
                st.markdown(
                    f'<a href="data:text/html;base64,{b64}" download="{filename}" '
                    f'style="text-decoration: none;">'
                    f'<button style="background-color: #00ff88; color: #0d1117; '
                    f'padding: 10px 20px; border: none; border-radius: 5px; '
                    f'cursor: pointer; font-weight: bold;">'
                    f'⬇️ Download Report</button></a>',
                    unsafe_allow_html=True
                )


def render_hide_page():
    """Render the Hide (Embed) page."""
    st.markdown("# 📝 Hide Data")
    st.markdown("Embed secret messages or files using various steganography methods.")
    
    if st.session_state.uploaded_file is None:
        st.info("👆 Upload a cover image in the sidebar to begin.")
        return
    
    uploaded = st.session_state.uploaded_file
    
    if not uploaded.name.lower().endswith(('.png', '.bmp', '.tiff', '.tif')):
        st.warning("⚠️ For embedding, please use lossless formats (PNG, BMP, TIFF). JPEG is not recommended.")
    
    # Method selection
    method = st.selectbox(
        "Select Embedding Method",
        [
            "LSB Steganography",
            "Encrypted LSB (AES-256-GCM)",
            "Spread Spectrum",
            "Audio LSB (WAV)",
            "Text - Zero Width Characters",
            "Text - Whitespace",
            "Image in Alpha Channel"
        ]
    )
    
    # Message input
    st.markdown("### Message to Hide")
    message_type = st.radio("Input type", ["Text", "File"], horizontal=True)
    
    if message_type == "Text":
        message = st.text_area("Enter secret message", height=100)
        message_bytes = message.encode('utf-8') if message else None
    else:
        message_file = st.file_uploader("Upload secret file", type=None)
        if message_file:
            message_bytes = message_file.read()
            st.markdown(f"📎 Loaded: `{message_file.name}` ({format_bytes_readable(len(message_bytes))})")
        else:
            message_bytes = None
    
    # Method-specific options
    st.markdown("### Options")
    
    password = None
    bits_per_channel = 1
    channels = 'rgb'
    
    if "Encrypted" in method or "Spread Spectrum" in method:
        password = st.text_input("Password", type="password", 
                                  help="Required for encryption/PRNG seed")
    
    if "LSB" in method and "Audio" not in method:
        col1, col2 = st.columns(2)
        with col1:
            bits_per_channel = st.slider("LSB bits", 1, 3, 1,
                                         help="More bits = more capacity, less stealth")
        with col2:
            channels = st.selectbox(
                "Channels",
                ['rgb', 'r', 'g', 'b', 'rgba', 'all'],
                help="Which color channels to use"
            )
    
    # Capacity display
    if message_bytes:
        try:
            temp_path = Path("temp_hide.png")
            with open(temp_path, "wb") as f:
                f.write(uploaded.getvalue())
            
            from core.embedder import Embedder
            embedder = Embedder()
            
            capacity = embedder.calculate_capacity(
                temp_path, 'lsb', bits_per_channel, channels
            )
            
            if 'usable_bytes' in capacity:
                used = len(message_bytes)
                max_cap = capacity['usable_bytes']
                pct = min(100, used / max(max_cap, 1) * 100)
                
                st.markdown(f"**Capacity:** {format_bytes_readable(used)} / {format_bytes_readable(max_cap)}")
                st.progress(pct / 100)
                
                if used > max_cap:
                    st.error("🚨 Message too large for selected options!")
        except Exception as e:
            st.warning(f"Could not calculate capacity: {e}")
    
    # Embed button
    if st.button("🔒 Embed Data", type="primary", use_container_width=True,
                 disabled=(message_bytes is None)):
        if message_bytes is None:
            st.error("Please provide a message to hide.")
            return
        
        if "Encrypted" in method and not password:
            st.error("Password required for encrypted embedding.")
            return
        
        if "Spread Spectrum" in method and not password:
            st.error("Password required for spread spectrum.")
            return
        
        with st.spinner("Embedding data..."):
            try:
                temp_path = Path("temp_hide.png")
                with open(temp_path, "wb") as f:
                    f.write(uploaded.getvalue())
                
                embedder = Embedder()
                
                if method == "LSB Steganography":
                    stego, meta = embedder.embed_lsb(
                        temp_path, message_bytes, bits_per_channel, channels
                    )
                elif method == "Encrypted LSB (AES-256-GCM)":
                    stego, meta = embedder.embed_lsb(
                        temp_path, message_bytes, bits_per_channel, channels, password
                    )
                elif method == "Spread Spectrum":
                    stego, meta = embedder.embed_spread_spectrum(
                        temp_path, message_bytes, password
                    )
                elif method == "Image in Alpha Channel":
                    hidden_img = Image.open(io.BytesIO(message_bytes))
                    stego, meta = embedder.embed_alpha_channel(temp_path, hidden_img)
                else:
                    st.error(f"Method '{method}' not yet implemented in UI.")
                    return
                
                st.session_state.stego_image = stego
                
                # Display results
                st.success("✅ Data embedded successfully!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Original**")
                    original = Image.open(io.BytesIO(uploaded.getvalue()))
                    st.image(original, use_container_width=True)
                
                with col2:
                    st.markdown("**Stego Image**")
                    st.image(stego, use_container_width=True)
                
                # Metadata
                st.markdown("### Embedding Details")
                for key, value in meta.items():
                    if isinstance(value, float):
                        st.markdown(f"- **{key.replace('_', ' ').title()}:** {value:.2f}")
                    else:
                        st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")
                
                # Download button
                buffer = io.BytesIO()
                stego.save(buffer, format='PNG')
                buffer.seek(0)
                
                st.download_button(
                    "⬇️ Download Stego Image",
                    buffer.getvalue(),
                    file_name=f"stego_{uploaded.name}",
                    mime="image/png",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Embedding failed: {str(e)}")


def render_extract_page():
    """Render the Extract page."""
    st.markdown("# 🔓 Extract Data")
    st.markdown("Recover hidden messages from stego files.")
    
    if st.session_state.uploaded_file is None:
        st.info("👆 Upload a suspected stego file in the sidebar.")
        return
    
    uploaded = st.session_state.uploaded_file
    
    # Extraction method
    extraction_method = st.selectbox(
        "Extraction Method",
        ["Auto-detect", "LSB", "Spread Spectrum", "Audio LSB", 
         "Text Zero-Width", "Text Whitespace", "Alpha Channel"]
    )
    
    # Password input if needed
    password = st.text_input("Password (if encrypted)", type="password")
    
    if st.button("🔓 Extract Data", type="primary", use_container_width=True):
        with st.spinner("Attempting extraction..."):
            try:
                temp_path = Path("temp_extract" + Path(uploaded.name).suffix)
                with open(temp_path, "wb") as f:
                    f.write(uploaded.getvalue())
                
                extractor = Extractor()
                
                if extraction_method == "Auto-detect":
                    results = extractor.auto_detect_and_extract(temp_path, password or None)
                elif extraction_method == "LSB":
                    results = extractor.extract_lsb(temp_path, password or None, try_all_channels=True)
                elif extraction_method == "Spread Spectrum":
                    if not password:
                        st.error("Password required for spread spectrum extraction.")
                        return
                    results = extractor.extract_spread_spectrum(temp_path, password)
                elif extraction_method == "Audio LSB":
                    results = extractor.extract_audio_lsb(temp_path, password or None)
                elif extraction_method == "Text Zero-Width":
                    results = extractor.extract_text_zero_width(temp_path)
                elif extraction_method == "Text Whitespace":
                    results = extractor.extract_text_whitespace(temp_path)
                elif extraction_method == "Alpha Channel":
                    results = extractor.extract_alpha_channel(temp_path)
                else:
                    st.error(f"Method not implemented: {extraction_method}")
                    return
                
                # Display results
                if results.get('success'):
                    st.success("✅ Data extracted successfully!")
                    
                    # Show extraction info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Method", results.get('detected_method', 'Unknown'))
                    with col2:
                        st.metric("Confidence", f"{results.get('confidence', 0)*100:.0f}%")
                    with col3:
                        st.metric("Encrypted", "Yes" if results.get('encrypted') else "No")
                    
                    # Display extracted data
                    data = results.get('data')
                    
                    # Check if it's an image
                    if results.get('is_image'):
                        try:
                            img = Image.open(io.BytesIO(data))
                            st.markdown("### Extracted Hidden Image")
                            st.image(img, use_container_width=True)
                            
                            # Download
                            st.download_button(
                                "⬇️ Download Hidden Image",
                                data,
                                file_name="extracted_hidden.png",
                                mime="image/png"
                            )
                        except Exception:
                            pass
                    else:
                        # Try to display as text
                        st.markdown("### Extracted Data")
                        try:
                            text = data.decode('utf-8')
                            st.text_area("Content", text, height=200)
                        except UnicodeDecodeError:
                            # Binary data
                            st.markdown(f"**Binary data:** {format_bytes_readable(len(data))}")
                            st.markdown(f"**Hex preview:** `{data[:32].hex()}...`")
                        
                        # Download
                        st.download_button(
                            "⬇️ Download Extracted Data",
                            data,
                            file_name="extracted_data.bin"
                        )
                else:
                    st.error(f"❌ Extraction failed: {results.get('error', 'Unknown error')}")
                    
                    # Show attempts if available
                    if 'attempts' in results:
                        with st.expander("View all attempts"):
                            for attempt in results['attempts']:
                                if 'error' in attempt:
                                    st.markdown(f"- ❌ {attempt.get('method', 'Unknown')}: {attempt['error']}")
                                else:
                                    st.markdown(f"- ✅ {attempt.get('method', 'Unknown')}: Success")
                    
            except Exception as e:
                st.error(f"Extraction error: {str(e)}")


def render_bit_planes_page():
    """Render the Bit Planes page."""
    st.markdown("# 🔬 Bit Plane Analysis")
    st.markdown("Visualize individual bit planes to identify steganography.")
    
    if st.session_state.uploaded_file is None:
        st.info("👆 Upload an image in the sidebar to view bit planes.")
        return
    
    uploaded = st.session_state.uploaded_file
    
    if not uploaded.name.lower().endswith(('.png', '.bmp', '.tiff', '.tif', '.jpg', '.jpeg')):
        st.warning("⚠️ This page only supports image files.")
        return
    
    try:
        img = Image.open(io.BytesIO(uploaded.getvalue()))
        
        st.markdown(f"**Image:** `{uploaded.name}` | **Mode:** `{img.mode}` | **Size:** `{img.size}`")
        
        # Convert for processing
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        # Get bit planes
        bit_planes = get_all_bit_planes(img)
        
        # Display bit planes
        st.markdown("### Individual Bit Planes")
        st.markdown("*LSB (bit 0) is most commonly used for steganography*")
        
        for channel_name, planes in bit_planes.items():
            st.markdown(f"#### {channel_name} Channel")
            
            cols = st.columns(4)
            for bit_idx in range(8):
                with cols[bit_idx % 4]:
                    # Reverse order so LSB is first
                    plane = planes[bit_idx]
                    plane_img = Image.fromarray(plane)
                    
                    # Highlight LSB
                    if bit_idx == 0:
                        st.markdown(f"**Bit {bit_idx} (LSB)** 🎯")
                    else:
                        st.markdown(f"Bit {bit_idx}")
                    
                    st.image(plane_img, use_container_width=True)
        
        # Educational info
        with st.expander("📚 Understanding Bit Planes"):
            st.markdown("""
            **What are bit planes?**
            
            Each pixel value (0-255) can be represented as 8 bits. A bit plane is the collection 
            of one specific bit position across all pixels in an image.
            
            - **Bit 7 (MSB)**: Most significant bit - carries most visual information
            - **Bit 0 (LSB)**: Least significant bit - carries least visual information
            
            **Steganography Signatures:**
            
            - **Clean Image**: LSB planes look noisy/random but with some structure
            - **LSB Stego**: LSB plane looks MORE random/flat due to embedded data
            - **Bit 1-2 Stego**: Higher planes show patterns or reduced noise
            
            **Analysis Tips:**
            - Compare LSB plane smoothness across different images
            - Look for unnatural uniformity in LSB distribution
            - Check if higher bit planes were modified (indicates aggressive embedding)
            """)
        
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")


def render_about_page():
    """Render the About page."""
    st.markdown("# ℹ️ About ShadowLens")
    
    st.markdown("""
    ## 🔍 ShadowLens — Advanced Steganography Analysis Suite
    
    ShadowLens is a professional-grade steganography detection and analysis tool designed 
    for cybersecurity researchers, digital forensics specialists, and security professionals.
    
    ### ✨ Key Features
    
    **9 Detection Algorithms:**
    - **LSB Analysis**: Extracts and analyzes least significant bit patterns
    - **Chi-Square Attack**: Statistical detection of LSB embedding
    - **RS Analysis**: Fridrich et al.'s Regular-Singular analysis
    - **Sample Pairs**: Dumitrescu et al. pair relationship analysis
    - **Histogram Analysis**: Detects characteristic histogram artifacts
    - **Noise Estimation**: Laplacian variance analysis
    - **DCT Analysis**: JPEG coefficient distribution analysis
    - **Metadata Analysis**: EXIF and file structure inspection
    
    **6 Embedding Methods:**
    - LSB Steganography (1-3 bits, channel selection)
    - Encrypted LSB (AES-256-GCM with PBKDF2)
    - Spread Spectrum (password-seeded PRNG)
    - Audio LSB (WAV files)
    - Text Zero-Width Characters
    - Image in Alpha Channel
    
    ### 🔬 Technical Details
    
    **Cryptography:**
    - AES-256-GCM for authenticated encryption
    - PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
    - Random 32-byte salt and 12-byte IV per encryption
    
    **Analysis Scoring:**
    - Weighted combination of all detection methods
    - Confidence-based verdict system
    - Per-channel and overall analysis
    
    ### 📚 References
    
    1. **Westfeld, A., & Pfitzmann, A.** (1999). Attacks on Steganographic Systems. 
       *Information Hiding, LNCS 1768*, 61-76.
    
    2. **Fridrich, J., Goljan, M., & Du, R.** (2001). Detecting LSB Steganography 
       in Color and Gray-Scale Images. *IEEE Multimedia*, 8(4), 22-28.
    
    3. **Dumitrescu, S., Wu, X., & Wang, Z.** (2002). Detection of LSB Steganography 
       via Sample Pair Analysis. *IEEE Trans. Signal Processing*, 51(7), 1995-2007.
    
    ### ⚖️ Ethical Use Statement
    
    ShadowLens is designed for legitimate security research, digital forensics, and 
    educational purposes. Users are responsible for complying with all applicable laws 
    and regulations. The developers assume no liability for misuse.
    
    ### 🛠️ Architecture
    
    ```
    ShadowLens/
    ├── app.py              # Streamlit UI
    ├── core/
    │   ├── analyzer.py     # Detection algorithms
    │   ├── embedder.py     # Steganography methods
    │   ├── extractor.py    # Data extraction
    │   ├── crypto.py       # Encryption layer
    │   ├── report.py       # Report generation
    │   └── utils.py        # Shared utilities
    └── samples/            # Test samples
    ```
    
    ### 📄 License
    
    MIT License — See GitHub repository for full license text.
    
    ---
    
    **Version:** 1.0.0 | **Released:** 2024
    """)


def main():
    """Main application entry point."""
    init_session_state()
    
    page = render_sidebar()
    
    # Route to appropriate page
    if page == "📊 Analyze":
        render_analyze_page()
    elif page == "📝 Hide":
        render_hide_page()
    elif page == "🔓 Extract":
        render_extract_page()
    elif page == "🔬 Bit Planes":
        render_bit_planes_page()
    elif page == "ℹ️ About":
        render_about_page()


if __name__ == "__main__":
    main()
