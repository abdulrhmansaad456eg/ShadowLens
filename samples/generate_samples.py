"""
Sample Generator for ShadowLens
Creates test images with and without hidden data
"""

import sys
import io
import wave
import struct
import random
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embedder import Embedder


def generate_solid_color(size, color, filename):
    """Generate a solid color image."""
    img = Image.new('RGB', size, color)
    img.save(filename)
    return filename


def generate_gradient(size, direction='horizontal', filename=None):
    """Generate a gradient image."""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    
    if direction == 'horizontal':
        for x in range(size[0]):
            color = int(255 * x / size[0])
            draw.line([(x, 0), (x, size[1])], fill=(color, color, color))
    else:
        for y in range(size[1]):
            color = int(255 * y / size[1])
            draw.line([(0, y), (size[0], y)], fill=(color, color, color))
    
    if filename:
        img.save(filename)
    return img


def generate_checkerboard(size, squares=8, filename=None):
    """Generate a checkerboard pattern."""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    
    square_size = size[0] // squares
    
    for row in range(squares):
        for col in range(squares):
            color = (255, 255, 255) if (row + col) % 2 == 0 else (0, 0, 0)
            x1 = col * square_size
            y1 = row * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size
            draw.rectangle([x1, y1, x2, y2], fill=color)
    
    if filename:
        img.save(filename)
    return img


def generate_noise(size, filename=None):
    """Generate random noise image."""
    arr = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    
    if filename:
        img.save(filename)
    return img


def generate_rainbow(size, filename=None):
    """Generate rainbow gradient."""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    
    for x in range(size[0]):
        hue = int(360 * x / size[0])
        # Simple HSV-like conversion for visualization
        if hue < 60:
            r, g, b = 255, int(255 * hue / 60), 0
        elif hue < 120:
            r, g, b = int(255 * (120 - hue) / 60), 255, 0
        elif hue < 180:
            r, g, b = 0, 255, int(255 * (hue - 120) / 60)
        elif hue < 240:
            r, g, b = 0, int(255 * (240 - hue) / 60), 255
        elif hue < 300:
            r, g, b = int(255 * (hue - 240) / 60), 0, 255
        else:
            r, g, b = 255, 0, int(255 * (360 - hue) / 60)
        
        draw.line([(x, 0), (x, size[1])], fill=(r, g, b))
    
    if filename:
        img.save(filename)
    return img


def generate_wav(duration=3, sample_rate=44100, frequency=440, filename=None):
    """Generate a simple sine wave WAV file."""
    num_samples = int(duration * sample_rate)
    
    # Generate sine wave
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(32767 * 0.5 * (1 + np.sin(2 * np.pi * frequency * t)))
        samples.append(sample)
    
    if filename:
        with wave.open(str(filename), 'w') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            
            # Pack samples
            data = struct.pack(f'<{len(samples)}h', *samples)
            wav.writeframes(data)
    
    return samples


def main():
    """Generate all test samples."""
    
    print("=" * 60)
    print("🔍 ShadowLens Sample Generator")
    print("=" * 60)
    
    # Create directories
    clean_dir = Path("samples/clean")
    stego_dir = Path("samples/stego")
    clean_dir.mkdir(parents=True, exist_ok=True)
    stego_dir.mkdir(parents=True, exist_ok=True)
    
    image_size = (400, 300)
    
    print("\n📁 Creating directories...")
    print(f"   Clean: {clean_dir}")
    print(f"   Stego: {stego_dir}")
    
    # Generate 5 clean images
    print("\n🎨 Generating CLEAN images...")
    
    clean_configs = [
        ("clean_solid_red.png", lambda path: generate_solid_color(image_size, (200, 50, 50), path)),
        ("clean_gradient.png", lambda path: generate_gradient(image_size, 'horizontal', path)),
        ("clean_checkerboard.png", lambda path: generate_checkerboard(image_size, 8, path)),
        ("clean_noise.png", lambda path: generate_noise(image_size, path)),
        ("clean_rainbow.png", lambda path: generate_rainbow(image_size, path))
    ]
    
    # Generate and save clean images
    clean_files = []
    for name, generator in clean_configs:
        filepath = clean_dir / name
        generator(filepath)
        clean_files.append(filepath)
        print(f"   ✅ {name}")
    
    # Generate 5 stego images with hidden messages
    print("\n🔒 Generating STEGO images (with hidden data)...")
    
    embedder = Embedder()
    hidden_messages = [
        b"Hello from ShadowLens! This is a hidden message.",
        b"The quick brown fox jumps over the lazy dog.",
        b"Secret data embedded using LSB steganography.",
        b"https://github.com/ShadowLens/steganography",
        b"Password: Sup3rS3cur3P@ss! Don't share this!"
    ]
    
    stego_files = []
    manifest = []
    
    for i, (clean_file, message) in enumerate(zip(clean_files, hidden_messages)):
        stego_name = f"stego_{clean_file.stem.replace('clean_', '')}.png"
        stego_path = stego_dir / stego_name
        
        # Embed message
        try:
            stego_img, meta = embedder.embed_lsb(
                clean_file, 
                message,
                bits_per_channel=1,
                channels='rgb'
            )
            stego_img.save(stego_path)
            
            stego_files.append(stego_path)
            manifest.append({
                'filename': stego_name,
                'source': clean_file.name,
                'method': 'LSB',
                'message': message.decode('utf-8'),
                'payload_size': len(message),
                'psnr': meta.get('psnr', 0)
            })
            print(f"   ✅ {stego_name}")
        except Exception as e:
            print(f"   ❌ {stego_name}: {e}")
    
    # Generate encrypted stego image
    print("\n🔐 Generating encrypted STEGO image...")
    try:
        secret_msg = b"This message is encrypted with AES-256-GCM!"
        stego_path = stego_dir / "stego_encrypted.png"
        
        stego_img, meta = embedder.embed_lsb(
            clean_files[0],
            secret_msg,
            bits_per_channel=1,
            channels='rgb',
            password="ShadowLens2024"
        )
        stego_img.save(stego_path)
        
        manifest.append({
            'filename': stego_path.name,
            'source': clean_files[0].name,
            'method': 'Encrypted LSB (AES-256-GCM)',
            'message': secret_msg.decode('utf-8'),
            'password': 'ShadowLens2024',
            'payload_size': len(secret_msg),
            'psnr': meta.get('psnr', 0)
        })
        print(f"   ✅ {stego_path.name}")
    except Exception as e:
        print(f"   ❌ Failed to create encrypted stego: {e}")
    
    # Generate WAV files
    print("\n🎵 Generating audio samples...")
    
    # Clean WAV
    clean_wav = clean_dir / "clean_audio.wav"
    generate_wav(duration=2, filename=clean_wav)
    print(f"   ✅ {clean_wav.name}")
    
    # Stego WAV
    stego_wav = stego_dir / "stego_audio.wav"
    try:
        # Create stego audio
        audio_msg = b"Hidden in audio!"
        stego_wav_bytes, meta = embedder.embed_audio_lsb(
            clean_wav,
            audio_msg
        )
        
        with open(stego_wav, 'wb') as f:
            f.write(stego_wav_bytes)
        
        manifest.append({
            'filename': stego_wav.name,
            'source': clean_wav.name,
            'method': 'Audio LSB',
            'message': audio_msg.decode('utf-8'),
            'payload_size': len(audio_msg)
        })
        print(f"   ✅ {stego_wav.name}")
    except Exception as e:
        print(f"   ❌ Failed to create stego audio: {e}")
    
    # Print manifest
    print("\n" + "=" * 60)
    print("📋 SAMPLE MANIFEST")
    print("=" * 60)
    
    print("\n🟢 CLEAN FILES:")
    for f in sorted(clean_dir.glob('*')):
        size = f.stat().st_size
        print(f"   • {f.name} ({size:,} bytes)")
    
    print("\n🔴 STEGO FILES (with hidden data):")
    for item in manifest:
        print(f"\n   📄 {item['filename']}")
        print(f"      Method: {item['method']}")
        print(f"      Hidden: \"{item['message']}\"")
        print(f"      Size: {item['payload_size']} bytes")
        if 'password' in item:
            print(f"      Password: {item['password']}")
        if 'psnr' in item:
            print(f"      PSNR: {item['psnr']:.2f} dB")
    
    print("\n" + "=" * 60)
    print("✅ Sample generation complete!")
    print(f"   Clean samples: {len(list(clean_dir.glob('*')))}")
    print(f"   Stego samples: {len(manifest)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
