"""
Steganography Embedding Engine for ShadowLens
Implements 6 hiding methods: LSB, Encrypted LSB, Spread Spectrum, Audio, Text, Alpha Channel
"""

import io
import wave
import struct
import random
from typing import Optional, Tuple, Union
from pathlib import Path
from PIL import Image
import numpy as np

from .crypto import CryptoManager
from .utils import (
    load_image, calculate_image_capacity, bytes_to_bits, bits_to_bytes,
    set_lsb, set_n_lsb, get_lsb, create_payload_header, calculate_psnr,
    image_to_bytes, bytes_to_image
)


class Embedder:
    """
    Steganography embedding engine supporting multiple methods.
    """
    
    def __init__(self):
        """Initialize the embedder with crypto manager."""
        self.crypto = CryptoManager()
    
    def embed_lsb(self, cover_path: Path, message: bytes, 
                  bits_per_channel: int = 1, channels: str = 'rgb',
                  password: Optional[str] = None) -> Tuple[Image.Image, dict]:
        """
        Embed message using LSB steganography.
        
        Args:
            cover_path: Path to cover image (PNG, BMP, TIFF)
            message: Data to hide
            bits_per_channel: Number of LSBs to use (1-3)
            channels: Channel selection ('r', 'g', 'b', 'rgb', 'rgba', 'all')
            password: If provided, encrypt message before embedding
            
        Returns:
            Tuple of (stego_image, metadata_dict)
        """
        # Load cover image
        img = load_image(cover_path)
        if img is None:
            raise ValueError("Could not load cover image")
        
        # Ensure RGB/RGBA mode
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        img_array = np.array(img)
        h, w, c = img_array.shape
        
        # Determine which channels to use
        channel_indices = []
        if channels in ('all', 'rgba'):
            channel_indices = list(range(c))
        elif channels == 'rgb':
            channel_indices = [0, 1, 2]
        elif channels == 'r':
            channel_indices = [0]
        elif channels == 'g':
            channel_indices = [1]
        elif channels == 'b':
            channel_indices = [2]
        elif channels == 'alpha' and c == 4:
            channel_indices = [3]
        else:
            channel_indices = [0, 1, 2]  # Default to RGB
        
        # Filter valid indices
        channel_indices = [i for i in channel_indices if i < c]
        
        # Encrypt if password provided
        is_encrypted = password is not None
        if is_encrypted:
            payload = self.crypto.encrypt(message, password)
        else:
            payload = message
        
        # Create header
        header = create_payload_header(len(payload), is_encrypted, 'lsb')
        full_payload = header + payload
        
        # Check capacity
        capacity = h * w * len(channel_indices) * bits_per_channel // 8
        if len(full_payload) > capacity:
            raise ValueError(
                f"Message too large: {len(full_payload)} bytes, "
                f"capacity: {capacity} bytes"
            )
        
        # Convert to bits
        bits = bytes_to_bits(full_payload)
        
        # Embed bits
        bit_idx = 0
        total_bits = len(bits)
        
        for i in channel_indices:
            for y in range(h):
                for x in range(w):
                    if bit_idx >= total_bits:
                        break
                    
                    pixel = int(img_array[y, x, i])
                    
                    if bits_per_channel == 1:
                        # Single LSB
                        img_array[y, x, i] = set_lsb(pixel, bits[bit_idx])
                        bit_idx += 1
                    else:
                        # Multiple LSBs
                        bits_to_embed = bits[bit_idx:bit_idx + bits_per_channel]
                        if len(bits_to_embed) < bits_per_channel:
                            bits_to_embed.extend([0] * (bits_per_channel - len(bits_to_embed)))
                        
                        value = 0
                        for b in bits_to_embed:
                            value = (value << 1) | b
                        
                        img_array[y, x, i] = set_n_lsb(pixel, value, bits_per_channel)
                        bit_idx += bits_per_channel
                    
                    if bit_idx >= total_bits:
                        break
                if bit_idx >= total_bits:
                    break
            if bit_idx >= total_bits:
                break
        
        # Create stego image
        stego = Image.fromarray(img_array)
        
        # Calculate PSNR
        original_array = np.array(load_image(cover_path))
        psnr = calculate_psnr(original_array, img_array)
        
        metadata = {
            'method': 'LSB',
            'bits_per_channel': bits_per_channel,
            'channels_used': channels,
            'encrypted': is_encrypted,
            'payload_size': len(message),
            'total_embedded': len(full_payload),
            'capacity': capacity,
            'utilization': len(full_payload) / capacity * 100,
            'psnr': psnr
        }
        
        return stego, metadata
    
    def embed_spread_spectrum(self, cover_path: Path, message: bytes,
                             password: str) -> Tuple[Image.Image, dict]:
        """
        Embed using spread spectrum technique.
        
        Message bits are spread across the image using PRNG seeded by password.
        More resistant to detection than sequential LSB.
        
        Args:
            cover_path: Path to cover image
            message: Data to hide
            password: Seed for PRNG (required)
            
        Returns:
            Tuple of (stego_image, metadata_dict)
        """
        if not password:
            raise ValueError("Password required for spread spectrum embedding")
        
        img = load_image(cover_path)
        if img is None:
            raise ValueError("Could not load cover image")
        
        img_array = np.array(img)
        h, w, c = img_array.shape
        
        # Create payload
        payload = self.crypto.encrypt(message, password)
        header = create_payload_header(len(payload), True, 'spread')
        full_payload = header + payload
        
        bits = bytes_to_bits(full_payload)
        
        # Initialize PRNG with password
        seed = hash(password) % (2**32)
        rng = random.Random(seed)
        
        # Generate random embedding positions
        total_pixels = h * w * c
        if len(bits) > total_pixels:
            raise ValueError(f"Message too large: {len(bits)} bits, capacity: {total_pixels}")
        
        # Generate unique positions
        positions = rng.sample(range(total_pixels), len(bits))
        
        # Embed bits at random positions
        for bit, pos in zip(bits, positions):
            y = pos // (w * c)
            x = (pos % (w * c)) // c
            ch = pos % c
            
            img_array[y, x, ch] = set_lsb(int(img_array[y, x, ch]), bit)
        
        stego = Image.fromarray(img_array)
        
        original_array = np.array(load_image(cover_path))
        psnr = calculate_psnr(original_array, img_array)
        
        metadata = {
            'method': 'Spread Spectrum',
            'encrypted': True,
            'password_hash': hash(password) % 10000,  # For verification only
            'payload_size': len(message),
            'total_embedded': len(full_payload),
            'capacity': total_pixels // 8,
            'utilization': len(full_payload) / (total_pixels // 8) * 100,
            'psnr': psnr
        }
        
        return stego, metadata
    
    def embed_audio_lsb(self, cover_path: Path, message: bytes,
                       password: Optional[str] = None) -> Tuple[bytes, dict]:
        """
        Embed message in WAV audio file using LSB.
        
        Args:
            cover_path: Path to WAV file
            message: Data to hide
            password: Optional encryption password
            
        Returns:
            Tuple of (stego_wav_bytes, metadata_dict)
        """
        # Read WAV file
        with wave.open(str(cover_path), 'rb') as wav:
            n_channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            framerate = wav.getframerate()
            n_frames = wav.getnframes()
            
            # Read all frames
            frames = wav.readframes(n_frames)
        
        # Check format support
        if sample_width != 2:  # 16-bit only for now
            raise ValueError("Only 16-bit WAV files are supported")
        
        # Convert frames to samples
        sample_count = n_frames * n_channels
        fmt = f"<{sample_count}h"  # little-endian signed shorts
        samples = list(struct.unpack(fmt, frames))
        
        # Prepare payload
        is_encrypted = password is not None
        if is_encrypted:
            payload = self.crypto.encrypt(message, password)
        else:
            payload = message
        
        header = create_payload_header(len(payload), is_encrypted, 'audio')
        full_payload = header + payload
        bits = bytes_to_bits(full_payload)
        
        # Check capacity
        capacity_bits = len(samples)
        if len(bits) > capacity_bits:
            raise ValueError(
                f"Message too large: {len(bits)} bits, "
                f"capacity: {capacity_bits} bits"
            )
        
        # Embed LSBs
        for i, bit in enumerate(bits):
            # Clear LSB and set new bit
            samples[i] = (samples[i] & 0xFFFE) | bit
        
        # Repack samples
        new_frames = struct.pack(fmt, *samples)
        
        # Build output WAV
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav_out:
            wav_out.setnchannels(n_channels)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(framerate)
            wav_out.writeframes(new_frames)
        
        metadata = {
            'method': 'Audio LSB',
            'channels': n_channels,
            'sample_rate': framerate,
            'sample_width': sample_width,
            'encrypted': is_encrypted,
            'payload_size': len(message),
            'total_embedded': len(full_payload),
            'capacity_bytes': capacity_bits // 8,
            'utilization': len(full_payload) / (capacity_bits // 8) * 100,
            'duration_seconds': n_frames / framerate
        }
        
        return output.getvalue(), metadata
    
    def embed_text_zero_width(self, cover_text: str, message: bytes) -> str:
        """
        Hide message in text using zero-width characters.
        
        Encodes binary data in zero-width spaces and joiners between words.
        
        Args:
            cover_text: Original text
            message: Data to hide
            
        Returns:
            Stego text with hidden message
        """
        # Zero-width characters for encoding
        ZERO_WIDTH = {
            '0': '\u200B',  # Zero Width Space
            '1': '\u200C',  # Zero Width Non-Joiner
            'space': '\u200D'  # Zero Width Joiner (separator)
        }
        
        # Convert message to binary string
        bits = ''.join(format(b, '08b') for b in message)
        
        # Split cover text into words
        words = cover_text.split()
        
        if len(bits) > len(words) - 1:
            raise ValueError(f"Text too short to hide message. Need {len(bits)} words, have {len(words)}")
        
        # Embed bits between words
        result = []
        for i, word in enumerate(words):
            result.append(word)
            if i < len(bits):
                # Insert zero-width character based on bit
                result.append(ZERO_WIDTH[bits[i]])
            elif i < len(words) - 1:
                result.append(' ')
        
        return ''.join(result)
    
    def embed_text_whitespace(self, cover_text: str, message: bytes) -> str:
        """
        Hide message using trailing whitespace at line ends.
        
        Uses spaces (0) and tabs (1) at end of lines.
        
        Args:
            cover_text: Original text
            message: Data to hide
            
        Returns:
            Stego text with hidden message in trailing whitespace
        """
        lines = cover_text.split('\n')
        
        # Convert message to bits
        bits = bytes_to_bits(message)
        
        if len(bits) > len(lines):
            raise ValueError(f"Not enough lines: need {len(bits)}, have {len(lines)}")
        
        # Embed bits as trailing whitespace
        for i, bit in enumerate(bits):
            if bit == 0:
                lines[i] = lines[i] + ' '  # Space = 0
            else:
                lines[i] = lines[i] + '\t'  # Tab = 1
        
        return '\n'.join(lines)
    
    def create_text_acrostic(self, words: list, message: str) -> str:
        """
        Create first-letter acrostic hiding a message.
        
        Args:
            words: List of words to use (will be prefixed with message letters)
            message: Message to hide
            
        Returns:
            Acrostic text
        """
        message = message.upper()
        message = ''.join(c for c in message if c.isalpha())
        
        if len(words) < len(message):
            raise ValueError(f"Need at least {len(message)} words for message")
        
        lines = []
        for i, char in enumerate(message):
            # Find word starting with required letter (case insensitive)
            word = words[i]
            lines.append(f"{char}{word[1:]}")
        
        # Add remaining words unchanged
        lines.extend(words[len(message):])
        
        return ' '.join(lines)
    
    def embed_alpha_channel(self, cover_path: Path, 
                           hidden_image: Image.Image) -> Tuple[Image.Image, dict]:
        """
        Hide a grayscale image in the alpha channel of a PNG.
        
        Args:
            cover_path: Path to cover image (must support alpha)
            hidden_image: Grayscale image to hide
            
        Returns:
            Tuple of (stego_image, metadata_dict)
        """
        img = load_image(cover_path)
        if img is None:
            raise ValueError("Could not load cover image")
        
        # Convert to RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img_array = np.array(img)
        h, w, _ = img_array.shape
        
        # Prepare hidden image
        hidden_gray = hidden_image.convert('L')
        hidden_gray = hidden_gray.resize((w, h), Image.Resampling.LANCZOS)
        hidden_array = np.array(hidden_gray)
        
        # Store hidden image in alpha channel
        # We can store 8 bits per pixel in alpha
        # For simplicity, store the full grayscale value
        img_array[:, :, 3] = hidden_array
        
        stego = Image.fromarray(img_array, 'RGBA')
        
        metadata = {
            'method': 'Alpha Channel',
            'hidden_dimensions': hidden_image.size,
            'cover_dimensions': (w, h),
            'hidden_image_size': hidden_array.size
        }
        
        return stego, metadata
    
    def calculate_capacity(self, cover_path: Path, method: str = 'lsb',
                          bits_per_channel: int = 1, 
                          channels: str = 'rgb') -> dict:
        """
        Calculate maximum capacity for a given cover and method.
        
        Args:
            cover_path: Path to cover file
            method: Embedding method
            bits_per_channel: For LSB methods
            channels: Channel selection
            
        Returns:
            Capacity information dictionary
        """
        ext = cover_path.suffix.lower()
        
        if method in ('lsb', 'spread'):
            img = load_image(cover_path)
            if img is None:
                return {'error': 'Could not load image'}
            
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            img_array = np.array(img)
            h, w, c = img_array.shape
            
            # Determine channels
            if channels in ('all', 'rgba') and c == 4:
                channel_count = 4
            elif channels == 'rgb':
                channel_count = 3
            elif channels in ('r', 'g', 'b'):
                channel_count = 1
            else:
                channel_count = 3
            
            total_bits = h * w * channel_count * bits_per_channel
            
            # Account for header overhead
            header_overhead = 13  # bytes
            
            return {
                'total_bits': total_bits,
                'total_bytes': total_bits // 8,
                'usable_bytes': (total_bits // 8) - header_overhead,
                'dimensions': (w, h),
                'channels': channel_count,
                'bits_per_channel': bits_per_channel,
                'header_overhead': header_overhead
            }
        
        elif method == 'audio':
            if ext != '.wav':
                return {'error': 'Audio method requires WAV file'}
            
            with wave.open(str(cover_path), 'rb') as wav:
                n_channels = wav.getnchannels()
                n_frames = wav.getnframes()
                
                total_bits = n_frames * n_channels
                header_overhead = 13
                
                return {
                    'total_bits': total_bits,
                    'total_bytes': total_bits // 8,
                    'usable_bytes': (total_bits // 8) - header_overhead,
                    'duration_seconds': n_frames / wav.getframerate(),
                    'channels': n_channels,
                    'sample_rate': wav.getframerate()
                }
        
        return {'error': f'Unknown method: {method}'}
