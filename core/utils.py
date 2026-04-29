"""
Utility Functions for ShadowLens
Shared helpers for image processing, bit manipulation, and validation
"""

import io
import hashlib
import struct
from pathlib import Path
from typing import Tuple, Optional, Union, List
from PIL import Image
import numpy as np


# Supported file formats
SUPPORTED_IMAGE_FORMATS = {'.png', '.bmp', '.tiff', '.tif', '.jpg', '.jpeg'}
SUPPORTED_AUDIO_FORMATS = {'.wav'}
SUPPORTED_TEXT_FORMATS = {'.txt'}


def get_file_extension(filepath: Union[str, Path]) -> str:
    """Get lowercase file extension from path."""
    return Path(filepath).suffix.lower()


def is_supported_image(filepath: Union[str, Path]) -> bool:
    """Check if file is a supported image format."""
    return get_file_extension(filepath) in SUPPORTED_IMAGE_FORMATS


def is_supported_audio(filepath: Union[str, Path]) -> bool:
    """Check if file is a supported audio format."""
    return get_file_extension(filepath) in SUPPORTED_AUDIO_FORMATS


def is_supported_text(filepath: Union[str, Path]) -> bool:
    """Check if file is a supported text format."""
    return get_file_extension(filepath) in SUPPORTED_TEXT_FORMATS


def validate_file_type(filepath: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate that a file is of a supported type.
    
    Args:
        filepath: Path to file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    ext = get_file_extension(filepath)
    
    all_supported = SUPPORTED_IMAGE_FORMATS | SUPPORTED_AUDIO_FORMATS | SUPPORTED_TEXT_FORMATS
    
    if ext not in all_supported:
        return False, f"Unsupported file format: {ext}. Supported: {', '.join(sorted(all_supported))}"
    
    return True, ""


def load_image(filepath: Union[str, Path]) -> Optional[Image.Image]:
    """
    Load and validate an image file.
    
    Args:
        filepath: Path to image file
        
    Returns:
        PIL Image object or None if loading fails
    """
    try:
        img = Image.open(filepath)
        # Convert to RGB/RGBA for consistent processing
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        return img
    except Exception as e:
        return None


def load_image_as_array(filepath: Union[str, Path]) -> Optional[np.ndarray]:
    """
    Load image as numpy array for processing.
    
    Args:
        filepath: Path to image file
        
    Returns:
        Numpy array of shape (H, W, C) with dtype uint8, or None
    """
    img = load_image(filepath)
    if img is None:
        return None
    return np.array(img)


def calculate_file_hash(filepath: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    Calculate hash of a file.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm ('md5', 'sha256')
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def calculate_image_capacity(img: Image.Image, bits_per_channel: int = 1, 
                            channels: str = 'rgb') -> int:
    """
    Calculate maximum bytes that can be hidden in an image.
    
    Args:
        img: PIL Image
        bits_per_channel: Number of LSBs to use per channel (1-3)
        channels: Which channels to use ('r', 'g', 'b', 'rgb', 'rgba', 'all')
        
    Returns:
        Maximum bytes that can be stored
    """
    width, height = img.size
    
    # Determine number of channels
    if img.mode == 'RGBA':
        channel_count = 4 if channels in ('rgba', 'all') else 3
    else:
        channel_count = 3 if channels in ('rgb', 'all') else len(channels)
    
    # Total bits available
    total_bits = width * height * channel_count * bits_per_channel
    
    # Convert to bytes (rounded down)
    return total_bits // 8


def bytes_to_bits(data: bytes) -> List[int]:
    """Convert bytes to list of bits (0s and 1s)."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: List[int]) -> bytes:
    """Convert list of bits back to bytes."""
    if len(bits) % 8 != 0:
        # Pad to byte boundary
        bits.extend([0] * (8 - len(bits) % 8))
    
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        result.append(byte)
    return bytes(result)


def set_lsb(value: int, bit: int) -> int:
    """Set the least significant bit of a value."""
    return (value & 0xFE) | (bit & 1)


def set_n_lsb(value: int, bits: int, n: int) -> int:
    """
    Set the n least significant bits of a value.
    
    Args:
        value: Original pixel value (0-255)
        bits: New bits to set (0 to 2^n - 1)
        n: Number of LSBs to modify (1-3)
        
    Returns:
        Modified pixel value
    """
    mask = (0xFF << n) & 0xFF  # Mask to clear n LSBs
    return (value & mask) | (bits & ((1 << n) - 1))


def get_lsb(value: int) -> int:
    """Get the least significant bit of a value."""
    return value & 1


def get_n_lsb(value: int, n: int) -> int:
    """Get the n least significant bits of a value."""
    return value & ((1 << n) - 1)


def calculate_psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio between two images.
    
    Args:
        original: Original image array
        modified: Modified image array
        
    Returns:
        PSNR value in dB (higher is better, inf if identical)
    """
    if original.shape != modified.shape:
        raise ValueError("Image shapes must match for PSNR calculation")
    
    # Calculate mean squared error
    mse = np.mean((original.astype(float) - modified.astype(float)) ** 2)
    
    if mse == 0:
        return float('inf')  # Images are identical
    
    # PSNR formula: 20 * log10(MAX / sqrt(MSE))
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return float(psnr)


def extract_bit_plane(img_array: np.ndarray, channel: int, bit: int) -> np.ndarray:
    """
    Extract a specific bit plane from an image channel.
    
    Args:
        img_array: Image as numpy array (H, W, C)
        channel: Channel index (0=R, 1=G, 2=B, 3=A)
        bit: Bit position to extract (0=LSB, 7=MSB)
        
    Returns:
        Binary image of the extracted bit plane
    """
    if channel >= img_array.shape[2]:
        raise ValueError(f"Channel {channel} not available in image")
    
    # Extract channel and get specific bit
    channel_data = img_array[:, :, channel]
    bit_plane = ((channel_data >> bit) & 1) * 255
    
    return bit_plane.astype(np.uint8)


def get_all_bit_planes(img: Image.Image) -> dict:
    """
    Extract all 8 bit planes for each channel.
    
    Args:
        img: PIL Image
        
    Returns:
        Dictionary with channel names as keys, list of 8 bit planes as values
    """
    img_array = np.array(img)
    channels = {}
    
    channel_names = ['R', 'G', 'B']
    if img_array.shape[2] == 4:
        channel_names.append('A')
    
    for i, name in enumerate(channel_names):
        if i < img_array.shape[2]:
            channels[name] = []
            for bit in range(8):
                plane = extract_bit_plane(img_array, i, bit)
                channels[name].append(plane)
    
    return channels


def int_to_bytes(n: int, length: int = 4) -> bytes:
    """Convert integer to bytes (big-endian)."""
    return n.to_bytes(length, byteorder='big')


def bytes_to_int(data: bytes) -> int:
    """Convert bytes to integer (big-endian)."""
    return int.from_bytes(data, byteorder='big')


def format_bytes_readable(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


# Magic headers for detection
MAGIC_HEADER = b'SHADOW'
MAGIC_VERSION = b'\x01'


def create_payload_header(data_len: int, is_encrypted: bool = False, 
                         method: str = 'lsb') -> bytes:
    """
    Create a header for embedded payload.
    
    Format: MAGIC_HEADER (6) + VERSION (1) + FLAGS (1) + METHOD (1) + LENGTH (4)
    
    Args:
        data_len: Length of payload data
        is_encrypted: Whether payload is encrypted
        method: Embedding method code
        
    Returns:
        Header bytes
    """
    flags = 0x01 if is_encrypted else 0x00
    method_codes = {'lsb': 0x01, 'spread': 0x02, 'audio': 0x03, 'alpha': 0x04}
    method_byte = method_codes.get(method, 0x01)
    
    header = MAGIC_HEADER + MAGIC_VERSION + bytes([flags]) + bytes([method_byte])
    header += int_to_bytes(data_len, 4)
    
    return header


def parse_payload_header(data: bytes) -> Optional[dict]:
    """
    Parse payload header from embedded data.
    
    Args:
        data: Raw bytes starting with header
        
    Returns:
        Dictionary with header info or None if invalid
    """
    if len(data) < 13:  # Minimum header size
        return None
    
    if data[:6] != MAGIC_HEADER:
        return None
    
    version = data[6]
    flags = data[7]
    method = data[8]
    length = bytes_to_int(data[9:13])
    
    method_names = {0x01: 'lsb', 0x02: 'spread', 0x03: 'audio', 0x04: 'alpha'}
    
    return {
        'version': version,
        'encrypted': bool(flags & 0x01),
        'method': method_names.get(method, 'unknown'),
        'length': length,
        'header_size': 13
    }


def image_to_bytes(img: Image.Image, format: str = 'PNG') -> bytes:
    """Convert PIL Image to bytes."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def bytes_to_image(data: bytes) -> Optional[Image.Image]:
    """Convert bytes to PIL Image."""
    try:
        return Image.open(io.BytesIO(data))
    except Exception:
        return None
