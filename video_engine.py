# -*- coding: utf-8 -*-
"""
High-Performance TikTok Video Rendering Engine for 104 Talking Animals.
Renders true vertical 9:16 MP4 videos (720x1280 at 30 fps, H.264 / AAC).
Features:
- Animated Talking Animal: mouth and jaw opening/closing with speech rhythm
- Natural eye blinking and head breathing motion
- Animated speech sound rings radiating from the talking mouth
- Ken Burns smooth cinematic zoom & pan
- Animated sound waveform visualizer
- Dynamic TikTok subtitle overlays with glowing active text
- Top animal badges (Emoji, Common Name, Latin name, Superpower tag)
- Bottom progress bar
- Strictly under 1 minute (< 60s)
- NO Arena logo added!
"""

import os
import math
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from talking_engine import apply_talking_animal_motion

WIDTH = 720
HEIGHT = 1280
FPS = 30
FFMPEG_BIN = '/home/user/.local/bin/ffmpeg'

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_caption = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        font_emoji = font_title = font_sub = font_tag = font_caption = ImageFont.load_default()
    return font_emoji, font_title, font_sub, font_tag, font_caption

def get_current_caption(captions, current_time):
    for cap in captions:
        if cap['start'] <= current_time <= cap['end'] + 0.3:
            return cap['text']
    return ""

def wrap_text(text, max_chars_per_line=30):
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    for w in words:
        if current_len + len(w) + 1 <= max_chars_per_line:
            current_line.append(w)
            current_len += len(w) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def get_audio_duration(audio_file):
    try:
        cmd = [FFMPEG_BIN, '-i', audio_file]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                return float(h)*3600 + float(m)*60 + float(s)
    except Exception:
        pass
    return 26.0

def render_animal_video(animal, output_mp4, duration_limit=None):
    """
    Renders a complete vertical 9:16 TikTok video for the given TALKING animal.
    Duration is strictly under 1 minute.
    """
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)

    image_path = f"images/{animal['id']}.png"
    audio_path = f"audio/{animal['id']}.mp3"

    if not os.path.exists(image_path):
        from artwork_engine import generate_animal_artwork
        generate_animal_artwork(animal, image_path)

    if not os.path.exists(audio_path):
        from audio_engine import generate_animal_audio
        generate_animal_audio(animal, audio_path)

    audio_dur = get_audio_duration(audio_path)
    captions = animal.get('captions', [])
    if captions:
        cap_dur = captions[-1]['end'] + 1.0
    else:
        cap_dur = audio_dur

    duration = max(audio_dur, cap_dur)
    duration = min(duration, 58.0)
    if duration_limit:
        duration = min(duration, duration_limit)

    total_frames = int(duration * FPS)

    # Load and prepare base image
    base_img = Image.open(image_path).convert('RGB')
    if base_img.size != (WIDTH, HEIGHT):
        base_img = base_img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # Pre-render top header badge and decorative static elements
    header_overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(header_overlay)

    font_emoji, font_title, font_sub, font_tag, font_caption = load_fonts()

    c_primary = hex_to_rgb(animal.get('color_primary', '#F59E0B'))
    c_secondary = hex_to_rgb(animal.get('color_secondary', '#1E293B'))

    # Top Header Pill Container
    top_box = [30, 40, WIDTH - 30, 140]
    h_draw.rounded_rectangle(top_box, radius=24, fill=(15, 23, 42, 215), outline=(*c_primary, 220), width=2)

    # Emoji & Title
    emoji_str = animal.get('emoji', '🐾')
    h_draw.text((60, 90), emoji_str, fill=(255, 255, 255, 255), font=font_emoji, anchor="mm")
    
    title_text = animal.get('name', '').upper()
    h_draw.text((105, 70), title_text, fill=(255, 255, 255, 255), font=font_title, anchor="lm")
    
    sub_text = f"« {animal.get('title', '')} » • {animal.get('latin', '')}"
    h_draw.text((105, 105), sub_text, fill=(*c_primary, 240), font=font_sub, anchor="lm")

    # Superpower Pill below header
    tag_text = f"✨ {animal.get('superpower', '')}"
    tag_w = min(len(tag_text) * 9 + 40, WIDTH - 60)
    tag_box = [(WIDTH - tag_w) // 2, 155, (WIDTH + tag_w) // 2, 195]
    h_draw.rounded_rectangle(tag_box, radius=18, fill=(30, 41, 59, 200), outline=(*c_primary, 160), width=1)
    h_draw.text((WIDTH // 2, 175), tag_text[:50], fill=(240, 240, 240, 240), font=font_tag, anchor="mm")

    # Category Pill
    cat_text = f"📍 {animal.get('category', '')} • 🗣️ Animal Parlant • ⏱️ {int(duration)}s"
    h_draw.text((WIDTH // 2, 220), cat_text, fill=(200, 200, 200, 200), font=font_tag, anchor="mm")

    # Setup FFmpeg Subprocess Pipe
    ffmpeg_cmd = [
        FFMPEG_BIN, '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}',
        '-pix_fmt', 'rgb24',
        '-r', str(FPS),
        '-i', '-',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-t', str(duration),
        '-movflags', '+faststart',
        output_mp4
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # Frame by Frame Rendering Loop
    num_bars = 22
    bar_width = 12
    bar_spacing = 8
    total_bars_width = num_bars * bar_width + (num_bars - 1) * bar_spacing
    bar_start_x = (WIDTH - total_bars_width) // 2
    wave_y_base = HEIGHT - 90

    # Oversized base for smooth Ken Burns zoom
    scale_factor = 1.10
    zoomed_w = int(WIDTH * scale_factor)
    zoomed_h = int(HEIGHT * scale_factor)
    oversized_base = base_img.resize((zoomed_w, zoomed_h), Image.Resampling.BILINEAR)

    for frame_idx in range(total_frames):
        if process.poll() is not None:
            break

        current_time = frame_idx / float(FPS)
        progress = min(current_time / duration, 1.0)

        # Ken Burns subtle zoom and pan calculation
        crop_x = int((zoomed_w - WIDTH) * (0.5 + 0.25 * math.sin(current_time * 0.35)))
        crop_y = int((zoomed_h - HEIGHT) * (0.5 + 0.25 * math.cos(current_time * 0.25)))
        crop_x = max(0, min(crop_x, zoomed_w - WIDTH))
        crop_y = max(0, min(crop_y, zoomed_h - HEIGHT))

        frame_img = oversized_base.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT))

        # ANIMATED TALKING ANIMAL MOUTH, JAW, BLINK & RESONANCE RINGS
        frame_img = apply_talking_animal_motion(frame_img, current_time, captions, duration, c_primary)

        # Dynamic overlay for subtitle, visualizer, and progress bar
        frame_overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame_overlay)

        # 1. Paste pre-rendered header
        frame_img.paste(header_overlay, (0, 0), header_overlay)

        # 2. Dynamic TikTok Subtitles
        caption_text = get_current_caption(captions, current_time)
        if caption_text:
            lines = wrap_text(caption_text, max_chars_per_line=28)
            line_height = 36
            box_h = len(lines) * line_height + 36
            sub_y = HEIGHT - 270 - box_h // 2

            # Frosted glass subtitle pill
            sub_box = [30, sub_y, WIDTH - 30, sub_y + box_h]
            d.rounded_rectangle(sub_box, radius=22, fill=(10, 15, 30, 225), outline=(*c_primary, 230), width=2)

            for i, line in enumerate(lines):
                ly = sub_y + 20 + i * line_height
                # Shadow
                d.text((WIDTH // 2 + 1, ly + 1), line, fill=(0, 0, 0, 240), font=font_caption, anchor="mm")
                # Glowing main text
                d.text((WIDTH // 2, ly), line, fill=(255, 255, 255, 255), font=font_caption, anchor="mm")

        # 3. Audio Waveform Visualizer
        for b in range(num_bars):
            bx = bar_start_x + b * (bar_width + bar_spacing)
            phase = current_time * 7.5 + b * 0.45
            bar_h = int(12 + 42 * abs(math.sin(phase) * math.cos(phase * 0.7 + b * 0.2)))
            bar_color = (*c_primary, 220) if (b % 2 == 0) else (255, 255, 255, 200)
            d.rounded_rectangle([bx, wave_y_base - bar_h, bx + bar_width, wave_y_base], radius=4, fill=bar_color)

        # 4. TikTok Video Bottom Progress Bar
        bar_y = HEIGHT - 14
        d.line([(0, bar_y), (WIDTH, bar_y)], fill=(50, 50, 60, 180), width=6)
        active_w = int(WIDTH * progress)
        if active_w > 0:
            d.line([(0, bar_y), (active_w, bar_y)], fill=(*c_primary, 255), width=6)

        # Composite and pipe to ffmpeg
        final_frame = Image.alpha_composite(frame_img.convert('RGBA'), frame_overlay).convert('RGB')
        try:
            process.stdin.write(final_frame.tobytes())
        except (BrokenPipeError, IOError):
            break

    try:
        process.stdin.close()
    except Exception:
        pass
    process.wait()
    return output_mp4

if __name__ == "__main__":
    with open("animals_dataset.json", "r", encoding="utf-8") as f:
        animals = json.load(f)
    print("Testing talking animal render for lion...")
    render_animal_video(animals[0], "videos/lion.mp4")
    print("Talking lion video rendered successfully!")
