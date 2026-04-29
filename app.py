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

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-tertiary: #21262d;
        --accent: #00ff88;
        --text-primary: #c9d1d9;
        --text-secondary: #8b949e;
        --success: #00ff88;
        --warning: #ffd700;
        --danger: #ff4444;
    }
    
    /* Override Streamlit defaults */
    .stApp {
        background-color: var(--bg-primary);
    }
    
    .css-1d391kg, .css-1lcbmhc {
        background-color: var(--bg-secondary);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--accent) !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Sidebar */
    .css-1cypcdb {
        background-color: var(--bg-secondary);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--bg-tertiary);
        color: var(--accent);
        border: 1px solid var(--accent);
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }
    
    .stButton > button:hover {
        background-color: var(--accent);
        color: var(--bg-primary);
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: var(--bg-secondary);
        border: 2px dashed var(--accent);
        border-radius: 10px;
    }
    
    /* Cards */
    .metric-card {
        background: var(--bg-secondary);
        border: 1px solid var(--bg-tertiary);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: var(--accent);
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.9em;
    }
    
    /* Status banners */
    .status-clean {
        background: linear-gradient(90deg, #00ff8820, #00ff8840);
        border-left: 4px solid var(--success);
        padding: 20px;
        border-radius: 5px;
    }
    
    .status-suspicious {
        background: linear-gradient(90deg, #ffd70020, #ffd70040);
        border-left: 4px solid var(--warning);
        padding: 20px;
        border-radius: 5px;
    }
    
    .status-danger {
        background: linear-gradient(90deg, #ff444420, #ff444440);
        border-left: 4px solid var(--danger);
        padding: 20px;
        border-radius: 5px;
    }
    
    /* Code blocks */
    code {
        background-color: var(--bg-tertiary);
        color: var(--accent);
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
    }
    
    /* Expanders */
    .streamlit-expander {
        border: 1px solid var(--bg-tertiary);
        border-radius: 5px;
        background: var(--bg-secondary);
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background-color: var(--accent);
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
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #00ff88; font-size: 1.8em; margin-bottom: 5px;">🔍 ShadowLens</h1>
        <p style="color: #8b949e; font-size: 0.9em;">Steganography Suite</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Analyze", "📝 Hide", "🔓 Extract", "🔬 Bit Planes", "ℹ️ About"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # File uploader (common across most pages)
    if page != "ℹ️ About":
        st.sidebar.markdown("### 📁 File Upload")
        
        accepted_types = ['png', 'bmp', 'tiff', 'tif', 'jpg', 'jpeg', 'wav', 'txt']
        uploaded = st.sidebar.file_uploader(
            "Drop file here",
            type=accepted_types,
            help="Supported: PNG, BMP, TIFF, JPG, WAV, TXT"
        )
        
        if uploaded:
            st.session_state.uploaded_file = uploaded
            
            # Show file info
            st.sidebar.markdown("#### File Information")
            st.sidebar.markdown(f"**Name:** `{uploaded.name}`")
            st.sidebar.markdown(f"**Size:** `{format_bytes_readable(len(uploaded.getvalue()))}`")
            
            # Calculate hash
            file_hash = calculate_file_hash(io.BytesIO(uploaded.getvalue()))
            st.sidebar.markdown(f"**MD5:** `{file_hash[:16]}...`")
            
            # Image-specific info
            if uploaded.name.lower().endswith(('.png', '.bmp', '.tiff', '.tif', '.jpg', '.jpeg')):
                try:
                    img = Image.open(io.BytesIO(uploaded.getvalue()))
                    st.sidebar.markdown(f"**Dimensions:** `{img.size[0]} × {img.size[1]}`")
                    st.sidebar.markdown(f"**Mode:** `{img.mode}`")
                except Exception:
                    pass
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.8em;'>ShadowLens v1.0</p>", unsafe_allow_html=True)
    
    return page


def render_analyze_page():
    """Render the Analyze page."""
    st.markdown("# 📊 Steganalysis")
    st.markdown("Detect and analyze hidden data in images using multiple algorithms.")
    
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
