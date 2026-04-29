"""
Generate ShadowLens banner using PIL
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create banner image
width, height = 1280, 640
img = Image.new('RGB', (width, height), '#0d1117')
draw = ImageDraw.Draw(img)

# Draw grid pattern for "digital" feel
for x in range(0, width, 40):
    draw.line([(x, 0), (x, height)], fill='#161b22', width=1)
for y in range(0, height, 40):
    draw.line([(0, y), (width, y)], fill='#161b22', width=1)

# Try to use a monospace font, fall back to default
try:
    # Try system fonts
    font_paths = [
        "C:/Windows/Fonts/consola.ttf",  # Consolas
        "C:/Windows/Fonts/cour.ttf",     # Courier
        "C:/Windows/Fonts/lucon.ttf",    # Lucida Console
    ]
    title_font = None
    subtitle_font = None
    
    for fp in font_paths:
        if os.path.exists(fp):
            title_font = ImageFont.truetype(fp, 120)
            subtitle_font = ImageFont.truetype(fp, 40)
            small_font = ImageFont.truetype(fp, 24)
            break
    
    if title_font is None:
        raise IOError("No suitable font found")
        
except Exception:
    title_font = ImageFont.load_default()
    subtitle_font = title_font
    small_font = title_font

# Draw "glowing" title effect
title_text = "🔍 ShadowLens"
x, y = width // 2, height // 2 - 50

# Glow layers
for offset in range(20, 0, -4):
    alpha = int(20 - offset)
    glow_color = (0, 255 - offset * 5, 136 - offset * 3)
    draw.text((x, y), title_text, font=title_font, fill=glow_color, anchor="mm")

# Main title
draw.text((x, y), title_text, font=title_font, fill='#00ff88', anchor="mm")

# Subtitle
subtitle = "Advanced Steganography Analysis & Detection Suite"
draw.text((width // 2, height // 2 + 80), subtitle, 
          font=subtitle_font, fill='#8b949e', anchor="mm")

# Bottom tagline
tagline = "Professional-grade tool for cybersecurity research & digital forensics"
draw.text((width // 2, height - 60), tagline, 
          font=small_font, fill='#30363d', anchor="mm")

# Add "matrix rain" effect on sides
import random
random.seed(42)
for _ in range(100):
    x = random.randint(0, width)
    y = random.randint(0, height)
    char = random.choice('01')
    size = random.randint(8, 16)
    opacity = random.randint(30, 100)
    color = (0, opacity, opacity // 2)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", size) if os.path.exists("C:/Windows/Fonts/consola.ttf") else ImageFont.load_default()
    except:
        f = ImageFont.load_default()
    draw.text((x, y), char, font=f, fill=color)

# Save banner
img.save('assets/banner.png', 'PNG')
print("✅ Banner created: assets/banner.png")
