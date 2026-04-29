"""
Report Generator for ShadowLens
Creates professional HTML analysis reports
"""

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .utils import calculate_file_hash, format_bytes_readable


class ReportGenerator:
    """
    Generates comprehensive HTML reports for steganalysis results.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.report_data = {}
    
    def generate_analysis_report(self, filepath: Path, 
                                  analysis_results: Dict,
                                  output_path: Optional[Path] = None) -> str:
        """
        Generate a full HTML steganalysis report.
        
        Args:
            filepath: Path to analyzed file
            analysis_results: Results from Steganalyzer.analyze()
            output_path: Optional path to save report
            
        Returns:
            HTML report as string
        """
        # Generate charts
        histogram_chart = self._create_histogram_chart(analysis_results)
        confidence_chart = self._create_confidence_chart(analysis_results)
        
        # Create HTML report
        html = self._build_html_report(
            filepath, 
            analysis_results,
            histogram_chart,
            confidence_chart
        )
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def _create_histogram_chart(self, results: Dict) -> str:
        """Create Plotly histogram chart for pixel distribution."""
        if 'histogram' not in results:
            return ""
        
        hist_data = results['histogram'].get('histogram_data', {})
        
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Red Channel', 'Green Channel', 'Blue Channel')
        )
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for idx, (ch_name, data) in enumerate(hist_data.items()):
            if idx >= 3:
                break
            
            # Create histogram
            fig.add_trace(
                go.Histogram(
                    x=data,
                    nbinsx=50,
                    name=f'{ch_name} Channel',
                    marker_color=colors[idx],
                    opacity=0.75
                ),
                row=1, col=idx + 1
            )
        
        fig.update_layout(
            title_text="Pixel Value Histograms",
            showlegend=False,
            height=300,
            template='plotly_dark',
            paper_bgcolor='#161b22',
            plot_bgcolor='#0d1117',
            font=dict(color='#c9d1d9')
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _create_confidence_chart(self, results: Dict) -> str:
        """Create confidence bar chart for all detection methods."""
        methods = []
        scores = []
        colors = []
        
        method_map = {
            'lsb_analysis': 'LSB Analysis',
            'chi_square': 'Chi-Square Attack',
            'rs_analysis': 'RS Analysis',
            'sample_pairs': 'Sample Pairs',
            'histogram': 'Histogram Analysis',
            'noise': 'Noise Estimation',
            'dct_analysis': 'DCT Analysis',
            'metadata': 'Metadata Analysis'
        }
        
        for key, label in method_map.items():
            if key in results and isinstance(results[key], dict):
                result = results[key]
                
                # Determine score based on available metrics
                if 'overall_suspicion' in result:
                    score = result['overall_suspicion'] * 100
                elif 'overall_confidence' in result:
                    score = result['overall_confidence'] * 100
                elif 'estimated_payload_percent' in result:
                    score = min(100, result['estimated_payload_percent'])
                elif 'estimated_embedding_rate' in result:
                    score = result['estimated_embedding_rate'] * 100
                elif result.get('detected'):
                    score = 80
                else:
                    score = 10
                
                methods.append(label)
                scores.append(score)
                
                # Color based on score
                if score < 30:
                    colors.append('#00ff88')  # Green
                elif score < 60:
                    colors.append('#ffd700')  # Yellow
                else:
                    colors.append('#ff4444')  # Red
        
        fig = go.Figure(data=[
            go.Bar(
                x=methods,
                y=scores,
                marker_color=colors,
                text=[f'{s:.1f}%' for s in scores],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Detection Method Confidence Scores',
            yaxis_title='Confidence (%)',
            height=400,
            template='plotly_dark',
            paper_bgcolor='#161b22',
            plot_bgcolor='#0d1117',
            font=dict(color='#c9d1d9'),
            xaxis_tickangle=-45
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _get_image_thumbnail(self, filepath: Path, max_size: int = 300) -> str:
        """Generate base64-encoded thumbnail of image."""
        try:
            img = Image.open(filepath)
            img.thumbnail((max_size, max_size))
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception:
            return ""
    
    def _build_html_report(self, filepath: Path, results: Dict,
                          histogram_chart: str, confidence_chart: str) -> str:
        """Build the complete HTML report."""
        
        # Get verdict info
        verdict = results.get('verdict', {})
        classification = verdict.get('classification', 'UNKNOWN')
        confidence = verdict.get('confidence', 0.0) * 100
        description = verdict.get('description', '')
        color = verdict.get('color', 'gray')
        
        # Color mapping
        color_hex = {
            'green': '#00ff88',
            'yellow': '#ffd700',
            'red': '#ff4444',
            'gray': '#888888'
        }.get(color, '#888888')
        
        # File info
        thumbnail = self._get_image_thumbnail(filepath)
        file_size = results.get('file_size', 0)
        dimensions = results.get('dimensions', (0, 0))
        
        # Build individual test results HTML
        test_results_html = self._build_test_results(results)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShadowLens Steganalysis Report - {filepath.name}</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent: #00ff88;
            --border: #30363d;
            --success: #00ff88;
            --warning: #ffd700;
            --danger: #ff4444;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid var(--accent);
            margin-bottom: 30px;
        }}
        
        .logo {{
            font-size: 2.5em;
            font-weight: bold;
            color: var(--accent);
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}
        
        .verdict-banner {{
            background: {color_hex}20;
            border: 2px solid {color_hex};
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .verdict-text {{
            font-size: 2em;
            font-weight: bold;
            color: {color_hex};
            margin-bottom: 10px;
        }}
        
        .verdict-confidence {{
            font-size: 1.3em;
            color: var(--text-primary);
        }}
        
        .verdict-description {{
            margin-top: 15px;
            color: var(--text-secondary);
        }}
        
        .section {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
        }}
        
        .section-title {{
            font-size: 1.3em;
            color: var(--accent);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }}
        
        .file-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .info-item {{
            background: var(--bg-tertiary);
            padding: 15px;
            border-radius: 5px;
        }}
        
        .info-label {{
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }}
        
        .thumbnail {{
            max-width: 100%;
            border-radius: 5px;
            border: 1px solid var(--border);
        }}
        
        .test-result {{
            background: var(--bg-tertiary);
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid var(--accent);
        }}
        
        .test-result.suspicious {{
            border-left-color: var(--danger);
        }}
        
        .test-result.clean {{
            border-left-color: var(--success);
        }}
        
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .test-name {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .status-pass {{
            background: var(--success)20;
            color: var(--success);
        }}
        
        .status-fail {{
            background: var(--danger)20;
            color: var(--danger);
        }}
        
        .test-details {{
            color: var(--text-secondary);
            font-size: 0.95em;
        }}
        
        .chart-container {{
            margin: 20px 0;
        }}
        
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }}
        
        .timestamp {{
            font-family: 'Courier New', monospace;
        }}
        
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .section {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🔍 ShadowLens</div>
            <div class="subtitle">Advanced Steganography Analysis & Detection Suite</div>
        </header>
        
        <div class="verdict-banner">
            <div class="verdict-text">{classification}</div>
            <div class="verdict-confidence">Confidence: {confidence:.1f}%</div>
            <div class="verdict-description">{description}</div>
        </div>
        
        <div class="section">
            <div class="section-title">📁 File Information</div>
            <div class="file-info">
                <div class="info-item">
                    <div class="info-label">Filename</div>
                    <div class="info-value">{filepath.name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Size</div>
                    <div class="info-value">{format_bytes_readable(file_size)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Dimensions</div>
                    <div class="info-value">{dimensions[0]} × {dimensions[1]}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MD5 Hash</div>
                    <div class="info-value">{results.get('file_hash_md5', 'N/A')[:16]}...</div>
                </div>
            </div>
            {f'<img src="{thumbnail}" class="thumbnail" alt="Analyzed image">' if thumbnail else ''}
        </div>
        
        <div class="section">
            <div class="section-title">📊 Detection Confidence</div>
            <div class="chart-container">
                {confidence_chart}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📈 Channel Histograms</div>
            <div class="chart-container">
                {histogram_chart}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🔬 Detailed Test Results</div>
            {test_results_html}
        </div>
        
        <footer>
            <p>Generated by ShadowLens v1.0</p>
            <p class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>'''
        
        return html
    
    def _build_test_results(self, results: Dict) -> str:
        """Build HTML for individual test results."""
        test_html = []
        
        tests = [
            ('lsb_analysis', 'LSB Analysis', 'overall_suspicion'),
            ('chi_square', 'Chi-Square Attack', 'overall_confidence'),
            ('rs_analysis', 'RS Analysis', 'estimated_payload_percent'),
            ('sample_pairs', 'Sample Pairs', 'estimated_embedding_rate'),
            ('histogram', 'Histogram Analysis', 'overall_flatness'),
            ('noise', 'Noise Estimation', 'noise_score'),
            ('dct_analysis', 'DCT Analysis', None),
            ('metadata', 'Metadata Analysis', None)
        ]
        
        for key, name, score_key in tests:
            if key not in results:
                continue
            
            result = results[key]
            if not isinstance(result, dict):
                continue
            
            # Determine status
            detected = result.get('detected', False)
            suspicious = result.get('suspicious', False)
            
            if detected or suspicious:
                status_class = 'status-fail'
                status_text = 'SUSPICIOUS'
                result_class = 'suspicious'
            else:
                status_class = 'status-pass'
                status_text = 'PASS'
                result_class = 'clean'
            
            # Build details string
            details = []
            
            if score_key and score_key in result:
                val = result[score_key]
                if isinstance(val, float):
                    details.append(f"Score: {val*100:.1f}%" if val <= 1 else f"Score: {val:.2f}")
            
            # Add specific details based on test type
            if key == 'lsb_analysis' and 'channels' in result:
                ch_info = result['channels']
                if isinstance(ch_info, dict):
                    for ch, data in ch_info.items():
                        if isinstance(data, dict) and 'ones_ratio' in data:
                            details.append(f"{ch}: {data['ones_ratio']*100:.1f}% LSB ones")
            
            elif key == 'rs_analysis' and 'estimated_payload_percent' in result:
                details.append(f"Estimated payload: {result['estimated_payload_percent']:.2f}%")
            
            elif key == 'sample_pairs' and 'estimated_embedding_rate' in result:
                rate = result['estimated_embedding_rate'] * 100
                details.append(f"Estimated embedding rate: {rate:.2f}%")
            
            elif key == 'metadata' and 'suspicious_indicators' in result:
                indicators = result['suspicious_indicators']
                if indicators:
                    details.extend(indicators)
            
            details_str = ' | '.join(details) if details else 'No anomalies detected'
            
            html = f'''
            <div class="test-result {result_class}">
                <div class="test-header">
                    <span class="test-name">{name}</span>
                    <span class="test-status {status_class}">{status_text}</span>
                </div>
                <div class="test-details">{details_str}</div>
            </div>
            '''
            test_html.append(html)
        
        return '\n'.join(test_html)
    
    def generate_extraction_report(self, filepath: Path,
                                    extraction_results: Dict) -> str:
        """Generate a report for extraction results."""
        # Simplified extraction report
        success = extraction_results.get('success', False)
        method = extraction_results.get('method', 'Unknown')
        confidence = extraction_results.get('confidence', 0.0) * 100
        
        color = '#00ff88' if success else '#ff4444'
        status = 'SUCCESS' if success else 'FAILED'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>ShadowLens Extraction Report</title>
    <style>
        body {{ font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .header {{ color: #00ff88; font-size: 1.5em; margin-bottom: 20px; }}
        .result {{ background: #161b22; padding: 20px; border-radius: 5px; border-left: 4px solid {color}; }}
        .status {{ color: {color}; font-size: 1.3em; font-weight: bold; }}
        .detail {{ margin: 10px 0; }}
        .label {{ color: #8b949e; }}
        pre {{ background: #21262d; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">🔓 ShadowLens Extraction Report</div>
    <div class="result">
        <div class="status">{status}</div>
        <div class="detail"><span class="label">File:</span> {filepath.name}</div>
        <div class="detail"><span class="label">Method Detected:</span> {method}</div>
        <div class="detail"><span class="label">Confidence:</span> {confidence:.1f}%</div>
        <div class="detail"><span class="label">Timestamp:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</body>
</html>'''
        
        return html
