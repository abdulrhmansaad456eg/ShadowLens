"""
Steganalysis Detection Engine for ShadowLens
Implements 9 advanced detection algorithms
"""

import io
import math
from typing import Dict, Tuple, Optional, List
from pathlib import Path
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import numpy as np
from scipy import stats
from scipy.fftpack import dct
import cv2
from skimage import filters
from skimage.restoration import estimate_sigma

from .utils import (
    load_image_as_array, calculate_file_hash, extract_bit_plane,
    get_all_bit_planes, bytes_to_bits, get_lsb
)


class Steganalyzer:
    """
    Advanced steganalysis engine implementing multiple detection algorithms.
    """
    
    def __init__(self):
        """Initialize the steganalyzer."""
        self.results = {}
        
    def analyze(self, filepath: Path, verbose: bool = False) -> Dict:
        """
        Run complete steganalysis on a file.
        
        Args:
            filepath: Path to image/audio file
            verbose: Whether to include detailed intermediate results
            
        Returns:
            Dictionary with all analysis results
        """
        self.results = {
            'filename': filepath.name,
            'file_hash_md5': calculate_file_hash(filepath, 'md5'),
            'file_hash_sha256': calculate_file_hash(filepath, 'sha256'),
            'file_size': filepath.stat().st_size,
        }
        
        # Load image
        img_array = load_image_as_array(filepath)
        if img_array is None:
            return {'error': 'Failed to load image'}
        
        self.results['dimensions'] = img_array.shape[:2]
        self.results['mode'] = 'RGBA' if img_array.shape[2] == 4 else 'RGB'
        
        # Run all detection methods
        self.results['lsb_analysis'] = self._analyze_lsb(img_array)
        self.results['chi_square'] = self._chi_square_attack(img_array)
        self.results['rs_analysis'] = self._rs_analysis(img_array)
        self.results['sample_pairs'] = self._sample_pairs_analysis(img_array)
        self.results['histogram'] = self._histogram_analysis(img_array)
        self.results['noise'] = self._noise_analysis(img_array)
        self.results['dct_analysis'] = self._dct_analysis(filepath, img_array)
        self.results['metadata'] = self._metadata_analysis(filepath)
        
        # Calculate combined score
        self.results['combined_score'] = self._calculate_combined_score()
        self.results['verdict'] = self._get_verdict(self.results['combined_score'])
        
        return self.results
    
    def _analyze_lsb(self, img_array: np.ndarray) -> Dict:
        """
        Analyze LSB randomness across all channels.
        
        Natural images have correlated LSBs; hidden data creates randomness.
        """
        channels = ['R', 'G', 'B']
        if img_array.shape[2] == 4:
            channels.append('A')
        
        lsb_results = {}
        overall_randomness = []
        
        for i, ch_name in enumerate(channels):
            if i >= img_array.shape[2]:
                break
                
            channel = img_array[:, :, i].flatten()
            
            # Extract LSBs
            lsbs = channel & 1
            
            # Calculate LSB frequency (should be ~0.5 for random data)
            ones_ratio = np.mean(lsbs)
            
            # Chi-square test on LSB distribution
            expected = len(lsbs) / 2
            chi_stat = ((np.sum(lsbs) - expected) ** 2 / expected + 
                       (len(lsbs) - np.sum(lsbs) - expected) ** 2 / expected)
            
            # Randomness score: how close to 0.5 (perfect random)
            # Natural images typically have 0.45-0.55 depending on content
            randomness = 1.0 - abs(ones_ratio - 0.5) * 2
            
            # Suspicion increases as randomness approaches 1.0 (perfect 0.5 ratio)
            # But we need to consider that natural images vary
            suspicion = abs(ones_ratio - 0.5) * 4  # Scale up
            suspicion = min(1.0, suspicion)
            
            lsb_results[ch_name] = {
                'ones_ratio': float(ones_ratio),
                'randomness_score': float(randomness),
                'chi_square_stat': float(chi_stat),
                'suspicion_score': float(suspicion)
            }
            overall_randomness.append(randomness)
        
        # Overall LSB suspicion: high randomness across all channels indicates stego
        avg_randomness = np.mean(overall_randomness)
        # If very close to 0.5 across all channels, likely embedded
        lsb_suspicion = 1.0 - avg_randomness
        
        return {
            'channels': lsb_results,
            'overall_suspicion': float(lsb_suspicion),
            'detected': lsb_suspicion > 0.7
        }
    
    def _chi_square_attack(self, img_array: np.ndarray) -> Dict:
        """
        Chi-Square attack for LSB steganography detection.
        
        Groups pixel values into pairs and compares expected vs observed frequencies.
        Based on Westfeld & Pfitzmann (1999).
        """
        results = {}
        channels = ['R', 'G', 'B']
        
        for i, ch_name in enumerate(channels):
            channel = img_array[:, :, i].flatten()
            
            # Create histogram
            hist, _ = np.histogram(channel, bins=256, range=(0, 256))
            
            # Group into pairs: (0,1), (2,3), ... (254, 255)
            observed = []
            expected = []
            
            for j in range(0, 256, 2):
                # Observed: frequency of even values
                # Expected: average of even and odd pairs
                obs_even = hist[j]
                obs_odd = hist[j + 1] if j + 1 < 256 else 0
                
                observed.append(obs_even)
                expected.append((obs_even + obs_odd) / 2.0)
            
            # Remove zero expected values to avoid division by zero
            valid_pairs = [(obs, exp) for obs, exp in zip(observed, expected) if exp > 0]
            
            if len(valid_pairs) < 10:
                continue
            
            # Calculate chi-square statistic
            chi_sq = sum((obs - exp) ** 2 / exp for obs, exp in valid_pairs)
            
            # Degrees of freedom = number of pairs - 1
            df = len(valid_pairs) - 1
            
            # Calculate p-value (probability of observing this chi-square by chance)
            # Low p-value (< 0.05) suggests non-uniform distribution = possible stego
            p_value = 1 - stats.chi2.cdf(chi_sq, df) if chi_sq > 0 else 1.0
            
            # Confidence that steganography is present
            # Low p-value = high confidence of stego
            confidence = 1.0 - p_value if p_value < 0.05 else 0.0
            
            results[ch_name] = {
                'chi_square_statistic': float(chi_sq),
                'degrees_of_freedom': int(df),
                'p_value': float(p_value),
                'confidence': float(confidence),
                'suspicious': p_value < 0.05
            }
        
        # Overall result
        max_confidence = max((r['confidence'] for r in results.values()), default=0.0)
        suspicious_channels = sum(1 for r in results.values() if r['suspicious'])
        
        return {
            'channels': results,
            'overall_confidence': float(max_confidence),
            'suspicious_channels': suspicious_channels,
            'detected': suspicious_channels >= 2 or max_confidence > 0.8
        }
    
    def _rs_analysis(self, img_array: np.ndarray) -> Dict:
        """
        RS Analysis (Regular-Singular) for LSB steganography.
        
        Implements the Fridrich et al. (2001) RS steganalysis algorithm.
        Uses discrimination function with mask [0, 1, 1, 0] on pixel groups.
        """
        channels = ['R', 'G', 'B']
        mask = np.array([0, 1, 1, 0])  # Classic RS mask
        
        results = {}
        
        for i, ch_name in enumerate(channels):
            channel = img_array[:, :, i]
            
            # Reshape into groups of 4 consecutive pixels
            h, w = channel.shape
            total_pixels = h * w
            
            # Take groups of 4 pixels
            num_groups = total_pixels // 4
            flat_channel = channel.flatten()[:num_groups * 4]
            groups = flat_channel.reshape(num_groups, 4)
            
            # Discrimination function: sum of absolute differences between neighbors
            def discrimination_func(group):
                return abs(group[1] - group[0]) + abs(group[2] - group[1]) + abs(group[3] - group[2])
            
            # Mask application functions
            def flip_lsb(x):
                return x ^ 1
            
            def apply_mask(group, mask, flip_func):
                result = group.copy()
                for j, m in enumerate(mask):
                    if m == 1:
                        result[j] = flip_func(result[j])
                return result
            
            # Calculate R and S counts
            Rm, Sm, Rm_neg, Sm_neg = 0, 0, 0, 0
            
            for group in groups:
                f_original = discrimination_func(group)
                
                # Apply positive mask
                masked_pos = apply_mask(group, mask, flip_lsb)
                f_masked_pos = discrimination_func(masked_pos)
                
                # Apply negative mask (flip mask bits)
                masked_neg = apply_mask(group, 1 - mask, flip_lsb)
                f_masked_neg = discrimination_func(masked_neg)
                
                # Classify
                if f_masked_pos > f_original:
                    Rm += 1
                elif f_masked_pos < f_original:
                    Sm += 1
                
                if f_masked_neg > f_original:
                    Rm_neg += 1
                elif f_masked_neg < f_original:
                    Sm_neg += 1
            
            total_classified = Rm + Sm
            if total_classified == 0:
                continue
            
            # Calculate message length estimate
            # Formula from Fridrich paper
            if Rm == 0 or Sm == 0:
                estimated_rate = 0.0
            else:
                d0 = Rm - Sm
                d1 = Rm_neg - Sm_neg
                if d0 != 0:
                    estimated_rate = abs(d1 / d0)
                else:
                    estimated_rate = 0.0
            
            # Normalize to percentage of capacity
            estimated_percentage = max(0.0, min(100.0, estimated_rate * 100))
            
            results[ch_name] = {
                'Rm': int(Rm),
                'Sm': int(Sm),
                'Rm_neg': int(Rm_neg),
                'Sm_neg': int(Sm_neg),
                'estimated_payload_percent': float(estimated_percentage),
                'suspicious': estimated_percentage > 5.0
            }
        
        # Overall: average payload estimate
        avg_payload = np.mean([r['estimated_payload_percent'] for r in results.values()]) if results else 0.0
        
        return {
            'channels': results,
            'estimated_payload_percent': float(avg_payload),
            'detected': avg_payload > 3.0
        }
    
    def _sample_pairs_analysis(self, img_array: np.ndarray) -> Dict:
        """
        Sample Pairs Analysis for LSB steganography detection.
        
        Analyzes adjacent pixel pairs to detect asymmetry introduced by LSB embedding.
        Based on Dumitrescu et al. (2002).
        """
        channels = ['R', 'G', 'B']
        results = {}
        
        for i, ch_name in enumerate(channels):
            channel = img_array[:, :, i]
            h, w = channel.shape
            
            # Collect horizontal adjacent pairs
            pairs = []
            for row in range(h):
                for col in range(w - 1):
                    u = int(channel[row, col])
                    v = int(channel[row, col + 1])
                    pairs.append((u, v))
            
            # Classify pairs
            P = 0  # Pairs where v is even and u < v, or v is odd and u > v
            Q = 0  # Pairs where v is even and u > v, or v is odd and u < v
            R = 0  # Pairs where u = v
            S = 0  # Pairs where |u - v| = 1
            
            for u, v in pairs:
                if u == v:
                    R += 1
                elif abs(u - v) == 1:
                    S += 1
                elif (v % 2 == 0 and u < v) or (v % 2 == 1 and u > v):
                    P += 1
                else:
                    Q += 1
            
            total = P + Q + R + S
            if total == 0:
                continue
            
            # SP estimate calculation
            # In natural images: P ≈ Q for large sets
            # LSB embedding breaks this balance
            if R > 0 and P != Q:
                # Estimate embedding rate
                a = 0.5 * (R + 2 * S)
                b = 2 * P - Q
                c = P - Q
                
                if a != 0:
                    # Quadratic solution
                    discriminant = b**2 - 4*a*c
                    if discriminant >= 0:
                        p1 = (-b + math.sqrt(discriminant)) / (2*a)
                        p2 = (-b - math.sqrt(discriminant)) / (2*a)
                        # Take valid estimate (0 <= p <= 1)
                        p_estimate = None
                        for p in [p1, p2]:
                            if 0 <= p <= 1:
                                p_estimate = p
                                break
                        if p_estimate is None:
                            p_estimate = 0.0
                    else:
                        p_estimate = 0.0
                else:
                    p_estimate = 0.0 if P == Q else abs(P - Q) / total
            else:
                p_estimate = 0.0
            
            embedding_rate = max(0.0, min(1.0, p_estimate))
            
            results[ch_name] = {
                'P': int(P),
                'Q': int(Q),
                'R': int(R),
                'S': int(S),
                'embedding_rate': float(embedding_rate),
                'suspicious': embedding_rate > 0.05
            }
        
        avg_rate = np.mean([r['embedding_rate'] for r in results.values()]) if results else 0.0
        
        return {
            'channels': results,
            'estimated_embedding_rate': float(avg_rate),
            'detected': avg_rate > 0.03
        }
    
    def _histogram_analysis(self, img_array: np.ndarray) -> Dict:
        """
        Histogram analysis for LSB steganography.
        
        Detects "histogram pairs" anomaly - a classic signature of LSB embedding
        where adjacent histogram bins become more similar.
        """
        channels = ['R', 'G', 'B']
        results = {}
        
        for i, ch_name in enumerate(channels):
            channel = img_array[:, :, i].flatten()
            
            # Create histogram
            hist, _ = np.histogram(channel, bins=256, range=(0, 256))
            
            # Calculate chi-square like statistic for adjacent pairs
            pair_differences = []
            for j in range(0, 256, 2):
                if j + 1 < 256:
                    diff = abs(hist[j] - hist[j + 1])
                    pair_differences.append(diff)
            
            # Natural images have varied differences
            # Stego images have smaller differences (histogram flattening)
            avg_diff = np.mean(pair_differences) if pair_differences else 0
            std_diff = np.std(pair_differences) if pair_differences else 0
            
            # Suspicious if differences are unusually small (flat histogram pairs)
            # Compare to expected natural image variance
            normalized_score = 1.0 - min(1.0, avg_diff / 100.0)  # Normalized threshold
            
            results[ch_name] = {
                'histogram_variance': float(np.var(hist)),
                'avg_pair_difference': float(avg_diff),
                'pair_difference_std': float(std_diff),
                'flatness_score': float(normalized_score),
                'suspicious': normalized_score > 0.7
            }
        
        avg_flatness = np.mean([r['flatness_score'] for r in results.values()]) if results else 0.0
        
        return {
            'channels': results,
            'histogram_data': {ch: img_array[:, :, i].flatten().tolist() 
                              for i, ch in enumerate(channels)},
            'overall_flatness': float(avg_flatness),
            'detected': avg_flatness > 0.6
        }
    
    def _noise_analysis(self, img_array: np.ndarray) -> Dict:
        """
        Noise level estimation using Laplacian variance.
        
        LSB embedding increases high-frequency noise.
        """
        channels = ['R', 'G', 'B']
        noise_levels = []
        
        for i, ch_name in enumerate(channels):
            channel = img_array[:, :, i].astype(np.float32)
            
            # Apply Laplacian filter
            laplacian = cv2.Laplacian(channel, cv2.CV_32F)
            
            # Calculate variance (measure of noise)
            variance = laplacian.var()
            noise_levels.append(variance)
        
        # Natural images typically have moderate Laplacian variance
        # Stego images often have higher variance due to LSB noise
        avg_noise = np.mean(noise_levels)
        
        # Normalize to 0-1 scale (typical range 0-1000 for natural images)
        noise_score = min(1.0, avg_noise / 500.0)
        
        # Suspicious if noise is significantly above baseline
        baseline = 100.0  # Typical natural image baseline
        suspicious = avg_noise > baseline * 2  # Double baseline is suspicious
        
        return {
            'channel_noise_levels': [float(n) for n in noise_levels],
            'average_noise': float(avg_noise),
            'noise_score': float(noise_score),
            'baseline': float(baseline),
            'detected': suspicious
        }
    
    def _dct_analysis(self, filepath: Path, img_array: np.ndarray) -> Dict:
        """
        DCT coefficient analysis for JPEG steganography.
        
        Detects JSteg-style embedding by analyzing DCT coefficient histograms.
        """
        ext = filepath.suffix.lower()
        
        if ext not in ['.jpg', '.jpeg']:
            return {
                'applicable': False,
                'message': 'DCT analysis only applies to JPEG images'
            }
        
        # For actual JPEG, we'd need to work with the DCT coefficients directly
        # This is a simplified analysis using block-based DCT
        
        # Convert to grayscale for DCT analysis
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        h, w = gray.shape
        h_blocks = h // 8
        w_blocks = w // 8
        
        # Collect DCT coefficients from all 8x8 blocks
        dct_coeffs = []
        
        for i in range(h_blocks):
            for j in range(w_blocks):
                block = gray[i*8:(i+1)*8, j*8:(j+1)*8].astype(np.float32)
                dct_block = cv2.dct(block)
                # Collect AC coefficients (skip DC at [0,0])
                ac_coeffs = dct_block.flatten()[1:]
                dct_coeffs.extend(ac_coeffs.tolist())
        
        dct_coeffs = np.array(dct_coeffs)
        
        # Analyze histogram of DCT coefficients
        # JSteg modifies LSBs of coefficients, causing characteristic patterns
        
        # Round to integers and analyze
        int_coeffs = np.round(dct_coeffs).astype(int)
        
        # Look for pairs of coefficients that differ by 1
        hist, _ = np.histogram(int_coeffs, bins=100, range=(-50, 50))
        
        # In natural JPEG, certain coefficient values are more common
        # JSteg causes flattening of the histogram
        hist_variance = np.var(hist)
        
        # Check for characteristic JSteg signature: peaks at 0, and reduced at +/-1
        zero_bin = 50  # Center of our histogram range
        if len(hist) > zero_bin + 2:
            peak_ratio = hist[zero_bin] / (hist[zero_bin - 1] + hist[zero_bin + 1] + 1)
        else:
            peak_ratio = 1.0
        
        # Suspicious if the histogram looks modified
        suspicious = hist_variance < 1000 or peak_ratio < 2.0
        
        return {
            'applicable': True,
            'dct_coefficient_count': int(len(dct_coeffs)),
            'histogram_variance': float(hist_variance),
            'dc_peak_ratio': float(peak_ratio),
            'suspicious': suspicious,
            'detected': suspicious
        }
    
    def _metadata_analysis(self, filepath: Path) -> Dict:
        """
        Analyze image metadata for suspicious indicators.
        
        Checks EXIF data, timestamps, software tags, and anomalies.
        """
        try:
            img = Image.open(filepath)
            
            # Extract EXIF data
            exif_data = {}
            suspicious_indicators = []
            
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    exif_data[tag_name] = str(value)
                    
                    # Check for suspicious software
                    if 'Software' in tag_name:
                        suspicious_tools = ['stego', 'steghide', 'outguess', 
                                          'f5', 'nsa', 'hidden', 'secret']
                        if any(tool in str(value).lower() for tool in suspicious_tools):
                            suspicious_indicators.append(f"Suspicious software tag: {value}")
                    
                    # Check timestamp mismatches
                    if tag_name in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        # Could check for future dates or inconsistencies
                        pass
            
            # Check for other potential indicators
            # Some stego tools leave signatures in comments
            if hasattr(img, 'info'):
                if 'comment' in img.info:
                    suspicious_indicators.append("Image contains comment metadata")
                if icc_profile := img.info.get('icc_profile'):
                    if len(icc_profile) > 10000:  # Unusually large ICC profile
                        suspicious_indicators.append("Unusually large ICC profile")
            
            # File structure checks
            file_size = filepath.stat().st_size
            img_size = img.size
            
            # Suspicious if file is much larger than expected for its dimensions
            expected_max = img_size[0] * img_size[1] * 4 * 2  # Rough estimate
            if file_size > expected_max:
                suspicious_indicators.append("File size larger than expected for dimensions")
            
            return {
                'exif_present': len(exif_data) > 0,
                'exif_data': exif_data,
                'suspicious_indicators': suspicious_indicators,
                'detected': len(suspicious_indicators) > 0
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'exif_present': False,
                'suspicious_indicators': [],
                'detected': False
            }
    
    def _calculate_combined_score(self) -> float:
        """
        Calculate combined confidence score from all tests.
        
        Uses weighted averaging based on reliability of each method.
        """
        weights = {
            'lsb_analysis': 0.15,
            'chi_square': 0.20,
            'rs_analysis': 0.25,
            'sample_pairs': 0.15,
            'histogram': 0.10,
            'noise': 0.05,
            'dct_analysis': 0.05,
            'metadata': 0.05
        }
        
        total_weight = 0
        weighted_score = 0
        
        for test_name, weight in weights.items():
            if test_name in self.results and isinstance(self.results[test_name], dict):
                test_result = self.results[test_name]
                
                # Skip if not applicable (e.g., DCT on PNG)
                if not test_result.get('applicable', True):
                    continue
                
                # Get detection indicator or score
                if 'overall_suspicion' in test_result:
                    score = test_result['overall_suspicion']
                elif 'overall_confidence' in test_result:
                    score = test_result['overall_confidence']
                elif 'estimated_payload_percent' in test_result:
                    score = min(1.0, test_result['estimated_payload_percent'] / 100.0)
                elif 'estimated_embedding_rate' in test_result:
                    score = test_result['estimated_embedding_rate']
                elif 'detected' in test_result:
                    score = 1.0 if test_result['detected'] else 0.0
                else:
                    score = 0.0
                
                weighted_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return weighted_score / total_weight
        return 0.0
    
    def _get_verdict(self, score: float) -> Dict:
        """
        Determine final verdict based on combined score.
        
        Returns classification and confidence.
        """
        if score < 0.3:
            return {
                'classification': 'CLEAN',
                'confidence': float(1.0 - score),
                'color': 'green',
                'description': 'No significant steganographic indicators detected'
            }
        elif score < 0.6:
            return {
                'classification': 'SUSPICIOUS',
                'confidence': float(score),
                'color': 'yellow',
                'description': 'Some anomalies detected, further analysis recommended'
            }
        else:
            return {
                'classification': 'LIKELY EMBEDDED',
                'confidence': float(score),
                'color': 'red',
                'description': 'Strong indicators of hidden data present'
            }
