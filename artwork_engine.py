# -*- coding: utf-8 -*-
"""
Artwork Generator for all 104 animals in 9:16 TikTok Vertical Format (720x1280).
Creates high-resolution visual backdrops, gradients, environmental particles,
cinematic lighting, and combines existing AI photos with stylized procedural art.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

WIDTH = 720
HEIGHT = 1280

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def create_vertical_gradient(width, height, color1, color2, color3=None):
    base = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(base)
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r3, g3, b3 = color3 if color3 else color2

    for y in range(height):
        factor = y / height
        if factor < 0.5:
            f = factor * 2
            r = int(r1 + (r2 - r1) * f)
            g = int(g1 + (g2 - g1) * f)
            b = int(b1 + (b2 - b1) * f)
        else:
            f = (factor - 0.5) * 2
            r = int(r2 + (r3 - r2) * f)
            g = int(g2 + (g3 - g2) * f)
            b = int(b2 + (b3 - b2) * f)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base

def draw_environmental_ambiance(img, category, color_primary, color_secondary):
    draw = ImageDraw.Draw(img, 'RGBA')
    random.seed(42)

    # Ambient light rays from top corners
    ray_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ray_draw = ImageDraw.Draw(ray_overlay)

    r_p, g_p, b_p = hex_to_rgb(color_primary)
    
    # Sunbeam / godrays effect
    for i in range(12):
        angle = -0.3 + i * 0.12
        x1 = WIDTH // 2 + int(math.sin(angle) * 100)
        y1 = -50
        x2 = WIDTH // 2 + int(math.sin(angle) * 1600)
        y2 = HEIGHT + 100
        alpha = random.randint(12, 35)
        ray_draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, alpha), width=random.randint(40, 90))

    ray_overlay = ray_overlay.filter(ImageFilter.GaussianBlur(18))
    img.paste(Image.alpha_composite(img.convert('RGBA'), ray_overlay).convert('RGB'))

    # Draw floating particles / bokeh
    bokeh_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bokeh_overlay)
    
    particle_count = 65
    for _ in range(particle_count):
        px = random.randint(20, WIDTH - 20)
        py = random.randint(50, HEIGHT - 150)
        radius = random.randint(3, 16)
        alpha = random.randint(25, 120)
        b_draw.ellipse(
            [(px - radius, py - radius), (px + radius, py + radius)],
            fill=(r_p, g_p, b_p, alpha)
        )
        # Inner bright core
        b_draw.ellipse(
            [(px - radius//2, py - radius//2), (px + radius//2, py + radius//2)],
            fill=(255, 255, 255, alpha + 30)
        )

    bokeh_overlay = bokeh_overlay.filter(ImageFilter.GaussianBlur(3))
    return Image.alpha_composite(img.convert('RGBA'), bokeh_overlay).convert('RGB')

def generate_animal_artwork(animal, output_path):
    """
    Generates or composites high resolution 9:16 vertical artwork for an animal.
    If a real AI photo exists in images/, crops and fits it with cinematic lighting.
    Otherwise generates an atmospheric cinematic poster with lighting & badge.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    existing_image = animal.get('image_file')

    c_primary = hex_to_rgb(animal.get('color_primary', '#3B82F6'))
    c_secondary = hex_to_rgb(animal.get('color_secondary', '#1E293B'))

    if existing_image and os.path.exists(existing_image):
        try:
            raw_img = Image.open(existing_image).convert('RGB')
            # Fit and fill to 720x1280 maintaining aspect ratio
            img_w, img_h = raw_img.size
            target_aspect = WIDTH / HEIGHT
            current_aspect = img_w / img_h

            if current_aspect > target_aspect:
                # Wider than target -> crop left/right
                new_w = int(img_h * target_aspect)
                left = (img_w - new_w) // 2
                raw_img = raw_img.crop((left, 0, left + new_w, img_h))
            else:
                # Taller than target -> crop top/bottom
                new_h = int(img_w / target_aspect)
                top = (img_h - new_h) // 2
                raw_img = raw_img.crop((0, top, img_w, top + new_h))

            final_img = raw_img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            
            # Apply slight contrast enhance and subtle dark gradient at top & bottom for TikTok UI
            enhancer = ImageEnhance.Contrast(final_img)
            final_img = enhancer.enhance(1.08)

            # Dark vignette top/bottom
            vignette = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
            v_draw = ImageDraw.Draw(vignette)
            for y in range(HEIGHT):
                if y < 240:
                    a = int((1.0 - (y / 240.0)) * 140)
                    v_draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))
                elif y > HEIGHT - 380:
                    a = int(((y - (HEIGHT - 380)) / 380.0) * 180)
                    v_draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))

            final_img = Image.alpha_composite(final_img.convert('RGBA'), vignette).convert('RGB')
            final_img.save(output_path, quality=95)
            return output_path
        except Exception as e:
            print(f"Error processing {existing_image}: {e}")

    # If no photo exists, generate artistic cinematic background with portrait badge
    bg = create_vertical_gradient(WIDTH, HEIGHT, (15, 23, 42), c_secondary, c_primary)
    bg = draw_environmental_ambiance(bg, animal.get('category'), animal.get('color_primary', '#E08709'), animal.get('color_secondary', '#78350F'))

    # Add artistic central circular avatar / glow emblem
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 80
    r_outer = 220
    r_inner = 200

    # Glow rings
    for r in range(r_outer, r_inner, -2):
        alpha = int((r - r_inner) / (r_outer - r_inner) * 120)
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*c_primary, alpha))

    # Inner disc
    d.ellipse([(cx - r_inner, cy - r_inner), (cx + r_inner, cy + r_inner)], fill=(*c_secondary, 220), outline=(*c_primary, 255), width=6)

    # Draw Emoji Icon in large format
    emoji_text = animal.get('emoji', '🐾')
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
    except:
        font_emoji = ImageFont.load_default()

    d.text((cx, cy), emoji_text, fill=(255, 255, 255, 255), font=font_emoji, anchor="mm")

    # Animal Name in emblem
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    d.text((cx, cy + r_inner + 45), animal.get('name', '').upper(), fill=(255, 255, 255, 255), font=font_title, anchor="mm")
    d.text((cx, cy + r_inner + 85), f"« {animal.get('title', '')} »", fill=(*c_primary, 255), font=font_sub, anchor="mm")

    # Dark gradient overlays for top & bottom captions
    for y in range(HEIGHT):
        if y < 220:
            a = int((1.0 - (y / 220.0)) * 150)
            d.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))
        elif y > HEIGHT - 360:
            a = int(((y - (HEIGHT - 360)) / 360.0) * 190)
            d.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, a))

    final_img = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
    final_img.save(output_path, quality=95)
    return output_path

if __name__ == "__main__":
    import json
    with open("animals_dataset.json", "r", encoding="utf-8") as f:
        animals = json.load(f)
    print(f"Generating artworks for {len(animals)} animals...")
    for a in animals:
        path = f"images/{a['id']}.png"
        generate_animal_artwork(a, path)
    print("All artworks generated successfully!")
