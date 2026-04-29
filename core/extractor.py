"""
Steganography Extraction Engine for ShadowLens
Auto-detects and extracts hidden data from various steganography methods
"""

import io
import wave
import struct
import random
from typing import Optional, Tuple, Union, Dict
from pathlib import Path
from PIL import Image
import numpy as np

from .crypto import CryptoManager
from .utils import (
    load_image, get_lsb, bits_to_bytes, parse_payload_header,
    bytes_to_image
)


class Extractor:
    """
    Extraction engine for recovering hidden data from stego files.
    Supports auto-detection and multiple extraction methods.
    """
    
    def __init__(self):
        """Initialize the extractor with crypto manager."""
        self.crypto = CryptoManager()
    
    def auto_detect_and_extract(self, stego_path: Path,
                                password: Optional[str] = None) -> Dict:
        """
        Attempt to auto-detect steganography method and extract data.
        
        Args:
            stego_path: Path to suspected stego file
            password: Optional password for encrypted payloads
            
        Returns:
            Dictionary with extraction results
        """
        results = {
            'filename': stego_path.name,
            'attempts': [],
            'success': False,
            'extracted_data': None,
            'method': None,
            'confidence': 0.0
        }
        
        ext = stego_path.suffix.lower()
        
        # Try methods based on file type
        if ext in ('.png', '.bmp', '.tiff', '.tif'):
            # Try LSB extraction from all channels
            for method in ['lsb', 'spread']:
                try:
                    result = self._try_extraction(stego_path, method, password)
                    results['attempts'].append(result)
                    
                    if result.get('success'):
                        results['success'] = True
                        results['extracted_data'] = result['data']
                        results['method'] = result['detected_method']
                        results['confidence'] = result['confidence']
                        results['metadata'] = result.get('metadata', {})
                        return results
                        
                except Exception as e:
                    results['attempts'].append({
                        'method': method,
                        'error': str(e)
                    })
            
            # Try alpha channel extraction for RGBA images
            try:
                result = self.extract_alpha_channel(stego_path)
                if result.get('success'):
                    results['success'] = True
                    results['extracted_data'] = result['data']
                    results['method'] = 'alpha_channel'
                    results['confidence'] = 0.9
                    results['metadata'] = result.get('metadata', {})
                    return results
            except Exception as e:
                results['attempts'].append({
                    'method': 'alpha_channel',
                    'error': str(e)
                })
        
        elif ext == '.wav':
            # Try audio LSB extraction
            try:
                result = self.extract_audio_lsb(stego_path, password)
                if result.get('success'):
                    results['success'] = True
                    results['extracted_data'] = result['data']
                    results['method'] = 'audio_lsb'
                    results['confidence'] = 0.85
                    results['metadata'] = result.get('metadata', {})
                    return results
            except Exception as e:
                results['attempts'].append({
                    'method': 'audio_lsb',
                    'error': str(e)
                })
        
        elif ext == '.txt':
            # Try text steganography extraction
            try:
                result = self.extract_text_zero_width(stego_path)
                if result.get('success'):
                    results['success'] = True
                    results['extracted_data'] = result['data']
                    results['method'] = 'text_zero_width'
                    results['confidence'] = 0.8
                    results['metadata'] = result.get('metadata', {})
                    return result
            except Exception as e:
                results['attempts'].append({
                    'method': 'text_zero_width',
                    'error': str(e)
                })
        
        return results
    
    def _try_extraction(self, stego_path: Path, method: str,
                       password: Optional[str]) -> Dict:
        """Try a specific extraction method."""
        if method == 'lsb':
            return self.extract_lsb(stego_path, password, try_all_channels=True)
        elif method == 'spread':
            if password:
                return self.extract_spread_spectrum(stego_path, password)
            else:
                return {'success': False, 'error': 'Password required for spread spectrum'}
        return {'success': False, 'error': f'Unknown method: {method}'}
    
    def extract_lsb(self, stego_path: Path, 
                   password: Optional[str] = None,
                   bits_per_channel: int = 1,
                   channels: str = 'rgb',
                   try_all_channels: bool = True) -> Dict:
        """
        Extract hidden data using LSB steganography.
        
        Args:
            stego_path: Path to stego image
            password: Optional decryption password
            bits_per_channel: Number of LSBs used (1-3)
            channels: Channel configuration used
            try_all_channels: If True, try all channel combinations
            
        Returns:
            Dictionary with extraction results
        """
        img = load_image(stego_path)
        if img is None:
            return {'success': False, 'error': 'Could not load image'}
        
        img_array = np.array(img)
        h, w, c = img_array.shape
        
        channel_configs = []
        if try_all_channels:
            # Try common configurations
            if c >= 3:
                channel_configs = [
                    [0, 1, 2],  # RGB
                    [0],        # R only
                    [1],        # G only
                    [2],        # B only
                ]
            if c == 4:
                channel_configs.append([3])  # Alpha
                channel_configs.append([0, 1, 2, 3])  # RGBA
        else:
            # Use specified channels
            if channels == 'rgb':
                channel_configs = [[0, 1, 2]]
            elif channels == 'r':
                channel_configs = [[0]]
            elif channels == 'g':
                channel_configs = [[1]]
            elif channels == 'b':
                channel_configs = [[2]]
            elif channels == 'rgba' and c == 4:
                channel_configs = [[0, 1, 2, 3]]
            else:
                channel_configs = [[0, 1, 2]]
        
        # Try each channel configuration
        for config in channel_configs:
            try:
                bits = []
                
                for i in config:
                    if i >= c:
                        continue
                    for y in range(h):
                        for x in range(w):
                            if bits_per_channel == 1:
                                bits.append(get_lsb(int(img_array[y, x, i])))
                            else:
                                val = int(img_array[y, x, i])
                                for b in range(bits_per_channel - 1, -1, -1):
                                    bits.append((val >> b) & 1)
                
                # Convert to bytes
                data = bits_to_bytes(bits)
                
                # Try to parse header
                header = parse_payload_header(data)
                
                if header:
                    payload_len = header['length']
                    header_size = header['header_size']
                    
                    if len(data) >= header_size + payload_len:
                        payload = data[header_size:header_size + payload_len]
                        
                        # Decrypt if needed
                        if header['encrypted'] and password:
                            decrypted = self.crypto.decrypt(payload, password)
                            if decrypted:
                                return {
                                    'success': True,
                                    'data': decrypted,
                                    'detected_method': header['method'],
                                    'encrypted': True,
                                    'confidence': 0.95,
                                    'metadata': {
                                        'channels': config,
                                        'bits_per_channel': bits_per_channel
                                    }
                                }
                            else:
                                return {
                                    'success': False,
                                    'error': 'Decryption failed - wrong password?'
                                }
                        elif header['encrypted'] and not password:
                            return {
                                'success': False,
                                'error': 'Payload is encrypted - password required'
                            }
                        else:
                            return {
                                'success': True,
                                'data': payload,
                                'detected_method': header['method'],
                                'encrypted': False,
                                'confidence': 0.95,
                                'metadata': {
                                    'channels': config,
                                    'bits_per_channel': bits_per_channel
                                }
                            }
                
            except Exception as e:
                continue
        
        return {
            'success': False,
            'error': 'No valid payload found with any channel configuration'
        }
    
    def extract_spread_spectrum(self, stego_path: Path, 
                                password: str) -> Dict:
        """
        Extract data from spread spectrum embedding.
        
        Args:
            stego_path: Path to stego image
            password: Password for PRNG seed (required)
            
        Returns:
            Dictionary with extraction results
        """
        if not password:
            return {'success': False, 'error': 'Password required'}
        
        img = load_image(stego_path)
        if img is None:
            return {'success': False, 'error': 'Could not load image'}
        
        img_array = np.array(img)
        h, w, c = img_array.shape
        
        # Initialize PRNG
        seed = hash(password) % (2**32)
        rng = random.Random(seed)
        
        total_pixels = h * w * c
        
        # We need to read enough bits for header + some payload
        # Try different payload sizes
        for max_bits in [1024 * 8, 1024 * 64, 1024 * 256, total_pixels]:
            try:
                positions = rng.sample(range(total_pixels), min(max_bits, total_pixels))
                
                bits = []
                for pos in positions:
                    y = pos // (w * c)
                    x = (pos % (w * c)) // c
                    ch = pos % c
                    bits.append(get_lsb(int(img_array[y, x, ch])))
                
                data = bits_to_bytes(bits)
                header = parse_payload_header(data)
                
                if header:
                    payload_len = header['length']
                    
                    # Re-extract with correct size
                    required_bits = (13 + payload_len) * 8
                    if required_bits <= total_pixels:
                        positions = rng.sample(range(total_pixels), required_bits)
                        
                        bits = []
                        for pos in positions:
                            y = pos // (w * c)
                            x = (pos % (w * c)) // c
                            ch = pos % c
                            bits.append(get_lsb(int(img_array[y, x, ch])))
                        
                        data = bits_to_bytes(bits)
                        payload = data[13:13 + payload_len]
                        
                        # Decrypt
                        decrypted = self.crypto.decrypt(payload, password)
                        if decrypted:
                            return {
                                'success': True,
                                'data': decrypted,
                                'detected_method': 'spread_spectrum',
                                'encrypted': True,
                                'confidence': 0.95
                            }
                
            except Exception as e:
                continue
        
        return {'success': False, 'error': 'Could not extract spread spectrum payload'}
    
    def extract_audio_lsb(self, stego_path: Path,
                         password: Optional[str] = None) -> Dict:
        """
        Extract hidden data from WAV audio file.
        
        Args:
            stego_path: Path to stego WAV file
            password: Optional decryption password
            
        Returns:
            Dictionary with extraction results
        """
        with wave.open(str(stego_path), 'rb') as wav:
            n_channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            n_frames = wav.getnframes()
            
            if sample_width != 2:
                return {'success': False, 'error': 'Only 16-bit WAV supported'}
            
            frames = wav.readframes(n_frames)
        
        sample_count = n_frames * n_channels
        fmt = f"<{sample_count}h"
        samples = struct.unpack(fmt, frames)
        
        # Extract LSBs
        bits = [s & 1 for s in samples]
        
        # Read enough for header + max reasonable payload
        max_bits = min(len(bits), 1024 * 1024 * 8)  # Max 1MB
        data = bits_to_bytes(bits[:max_bits])
        
        # Try to find header
        header = parse_payload_header(data)
        
        if header:
            payload_len = header['length']
            
            if len(data) >= 13 + payload_len:
                payload = data[13:13 + payload_len]
                
                if header['encrypted'] and password:
                    decrypted = self.crypto.decrypt(payload, password)
                    if decrypted:
                        return {
                            'success': True,
                            'data': decrypted,
                            'detected_method': 'audio_lsb',
                            'encrypted': True,
                            'confidence': 0.9
                        }
                    else:
                        return {'success': False, 'error': 'Decryption failed'}
                elif header['encrypted']:
                    return {'success': False, 'error': 'Encrypted payload - password required'}
                else:
                    return {
                        'success': True,
                        'data': payload,
                        'detected_method': 'audio_lsb',
                        'encrypted': False,
                        'confidence': 0.9
                    }
        
        return {'success': False, 'error': 'No valid payload header found'}
    
    def extract_text_zero_width(self, stego_path: Path) -> Dict:
        """
        Extract hidden data from zero-width character steganography.
        
        Args:
            stego_path: Path to text file
            
        Returns:
            Dictionary with extraction results
        """
        with open(stego_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Zero-width characters
        ZW_SPACE = '\u200B'    # Zero Width Space = 0
        ZW_NO_JOIN = '\u200C'  # Zero Width Non-Joiner = 1
        
        # Extract bits
        bits = []
        for char in text:
            if char == ZW_SPACE:
                bits.append(0)
            elif char == ZW_NO_JOIN:
                bits.append(1)
        
        if len(bits) < 16:  # Need at least 2 bytes for any meaningful data
            return {'success': False, 'error': 'No zero-width characters found'}
        
        # Convert to bytes
        data = bits_to_bytes(bits)
        
        return {
            'success': True,
            'data': data,
            'detected_method': 'zero_width',
            'encrypted': False,
            'confidence': 0.8,
            'metadata': {
                'bits_extracted': len(bits),
                'bytes_extracted': len(data)
            }
        }
    
    def extract_text_whitespace(self, stego_path: Path) -> Dict:
        """
        Extract hidden data from trailing whitespace steganography.
        
        Args:
            stego_path: Path to text file
            
        Returns:
            Dictionary with extraction results
        """
        with open(stego_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        bits = []
        for line in lines:
            if line.endswith(' \n') or line.endswith(' '):
                bits.append(0)  # Space = 0
            elif line.endswith('\t\n') or line.endswith('\t'):
                bits.append(1)  # Tab = 1
        
        if not bits:
            return {'success': False, 'error': 'No trailing whitespace found'}
        
        data = bits_to_bytes(bits)
        
        return {
            'success': True,
            'data': data,
            'detected_method': 'whitespace',
            'encrypted': False,
            'confidence': 0.75,
            'metadata': {
                'lines_analyzed': len(lines),
                'bits_extracted': len(bits)
            }
        }
    
    def extract_alpha_channel(self, stego_path: Path) -> Dict:
        """
        Extract hidden image from alpha channel.
        
        Args:
            stego_path: Path to RGBA image
            
        Returns:
            Dictionary with extraction results
        """
        img = load_image(stego_path)
        if img is None:
            return {'success': False, 'error': 'Could not load image'}
        
        if img.mode != 'RGBA':
            return {'success': False, 'error': 'Image must have alpha channel'}
        
        img_array = np.array(img)
        
        # Extract alpha channel as grayscale image
        alpha = img_array[:, :, 3]
        
        # Check if there's meaningful data (not all 255 or 0)
        unique_values = len(np.unique(alpha))
        
        if unique_values < 10:
            return {
                'success': False,
                'error': 'Alpha channel appears empty or uniform'
            }
        
        # Create grayscale image from alpha
        hidden_img = Image.fromarray(alpha, 'L')
        
        # Convert to bytes for return
        buffer = io.BytesIO()
        hidden_img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        
        return {
            'success': True,
            'data': img_bytes,
            'is_image': True,
            'detected_method': 'alpha_channel',
            'encrypted': False,
            'confidence': 0.9,
            'metadata': {
                'dimensions': hidden_img.size,
                'unique_values': unique_values
            }
        }
