# -*- coding: utf-8 -*-
"""
Talking Animal Animation Engine:
Generates organic lip-sync, jaw articulation, breathing motion, eye blinking,
and sound resonance rings for talking animals in 9:16 vertical TikTok videos.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

WIDTH = 720
HEIGHT = 1280

def get_speech_envelope(current_time, captions, duration):
    """
    Computes real-time syllable intensity (0.0 to 1.0) based on current speech time.
    """
    # Check if inside an active subtitle phrase
    is_speaking_phrase = False
    phrase_progress = 0.0
    for cap in captions:
        if cap['start'] <= current_time <= cap['end']:
            is_speaking_phrase = True
            phrase_progress = (current_time - cap['start']) / (cap['end'] - cap['start'])
            break
            
    if not is_speaking_phrase:
        return 0.0
        
    # Syllable frequency modulation (approx 4.5 Hz speech rate)
    syllable_osc = (math.sin(current_time * 2 * math.pi * 4.8) + 1.0) * 0.5
    vowel_burst = (math.sin(current_time * 2 * math.pi * 9.6) + 1.0) * 0.3
    
    amp = syllable_osc * 0.75 + vowel_burst * 0.25
    return min(max(amp, 0.0), 1.0)

def apply_talking_animal_motion(base_img, current_time, captions, duration, color_primary=(245, 158, 11)):
    """
    Applies organic talking animation:
    1. Lower jaw and mouth articulation in sync with speech syllables
    2. Head breathing and subtle speaking sway
    3. Eye blinking every 3.5s
    4. Soundwave resonance rings radiating from the mouth
    """
    img = base_img.copy()
    amp = get_speech_envelope(current_time, captions, duration)
    
    # Center of animal face (typically around center of 720x1280)
    mouth_cx = WIDTH // 2
    mouth_cy = HEIGHT // 2 + 60
    
    # 1. Talking Mouth / Jaw Lip-Sync
    if amp > 0.08:
        jaw_drop = int(18 * amp)  # Jaw opens up to 18px
        mouth_w = 110
        mouth_h = 70
        
        # Crop lower jaw box
        jaw_box = (mouth_cx - mouth_w, mouth_cy - 10, mouth_cx + mouth_w, mouth_cy + mouth_h)
        jaw_patch = base_img.crop(jaw_box)
        
        # Draw dark inner mouth cavity under upper lip
        mouth_cavity = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        m_draw = ImageDraw.Draw(mouth_cavity)
        
        # Inner mouth dark reddish-black oval
        cavity_h = int(16 * amp)
        cavity_box = [mouth_cx - int(38 * amp), mouth_cy - 2, mouth_cx + int(38 * amp), mouth_cy + cavity_h]
        m_draw.ellipse(cavity_box, fill=(25, 10, 15, 230))
        
        # Subtle tongue / teeth highlight
        if amp > 0.4:
            tongue_box = [mouth_cx - int(20 * amp), mouth_cy + cavity_h - 4, mouth_cx + int(20 * amp), mouth_cy + cavity_h + 2]
            m_draw.ellipse(tongue_box, fill=(180, 50, 60, 200))
            
        mouth_cavity = mouth_cavity.filter(ImageFilter.GaussianBlur(1.5))
        img.paste(Image.alpha_composite(img.convert('RGBA'), mouth_cavity).convert('RGB'))
        
        # Paste displaced lower jaw
        img.paste(jaw_patch, (mouth_cx - mouth_w, mouth_cy - 10 + jaw_drop))
        
    # 2. Sound Resonance Rings radiating from mouth when speaking
    if amp > 0.25:
        ring_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        r_draw = ImageDraw.Draw(ring_layer)
        for i in range(3):
            ring_phase = (current_time * 3.5 + i * 0.33) % 1.0
            r_rad = int(35 + ring_phase * 90)
            r_alpha = int((1.0 - ring_phase) * 140 * amp)
            r_draw.ellipse(
                [(mouth_cx - r_rad, mouth_cy - r_rad//2), (mouth_cx + r_rad, mouth_cy + r_rad//2)],
                outline=(*color_primary, r_alpha),
                width=2
            )
        ring_layer = ring_layer.filter(ImageFilter.GaussianBlur(1.2))
        img = Image.alpha_composite(img.convert('RGBA'), ring_layer).convert('RGB')
        
    # 3. Eye Blinking (every 3.6 seconds for 0.16 seconds)
    blink_cycle = current_time % 3.6
    if 3.44 <= blink_cycle <= 3.60:
        blink_ratio = math.sin((blink_cycle - 3.44) / 0.16 * math.pi)
        blink_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(blink_layer)
        
        # Left and right eye locations
        eye_y = HEIGHT // 2 - 90
        eye_offset = 85
        eye_w = 40
        eye_h = int(18 * blink_ratio)
        
        # Eyelid patches
        b_draw.ellipse([mouth_cx - eye_offset - eye_w, eye_y - eye_h, mouth_cx - eye_offset + eye_w, eye_y + eye_h], fill=(40, 25, 20, int(220 * blink_ratio)))
        b_draw.ellipse([mouth_cx + eye_offset - eye_w, eye_y - eye_h, mouth_cx + eye_offset + eye_w, eye_y + eye_h], fill=(40, 25, 20, int(220 * blink_ratio)))
        
        blink_layer = blink_layer.filter(ImageFilter.GaussianBlur(1.0))
        img = Image.alpha_composite(img.convert('RGBA'), blink_layer).convert('RGB')
        
    return img
