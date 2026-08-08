# -*- coding: utf-8 -*-
"""
Fast Multi-Worker Video Batch Renderer for all 104 animals.
Renders all missing MP4 videos (< 1 min, vertical 9:16, no Arena logo).
"""

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from video_engine import render_animal_video
from audio_engine import generate_animal_audio
from artwork_engine import generate_animal_artwork

DATASET_FILE = "animals_dataset.json"

def render_one(animal):
    aid = animal['id']
    out_path = f"videos/{aid}.mp4"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500000:
        return aid, True, "Already exists"
    
    try:
        t0 = time.time()
        render_animal_video(animal, out_path)
        dt = time.time() - t0
        return aid, True, f"Rendered in {dt:.1f}s"
    except Exception as e:
        return aid, False, str(e)

def main():
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        animals = json.load(f)

    print(f"Checking {len(animals)} animals for MP4 video files...")
    missing = [a for a in animals if not os.path.exists(f"videos/{a['id']}.mp4") or os.path.getsize(f"videos/{a['id']}.mp4") < 500000]
    print(f"Missing videos to render: {len(missing)} out of {len(animals)}")

    if not missing:
        print("All 104 videos are already rendered and ready!")
        return

    # Use 3 concurrent workers
    workers = 3
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(render_one, a): a for a in missing}
        for future in as_completed(futures):
            a = futures[future]
            try:
                aid, ok, msg = future.result()
                if ok:
                    success_count += 1
                    print(f"[{success_count}/{len(missing)}] ✅ {a['name']} ({aid}) -> {msg}")
                else:
                    fail_count += 1
                    print(f"[FAIL] ❌ {a['name']} ({aid}) -> {msg}")
            except Exception as e:
                fail_count += 1
                print(f"[ERROR] ❌ {a['name']} -> {e}")

    total_ready = len([a for a in animals if os.path.exists(f"videos/{a['id']}.mp4")])
    print(f"\n==========================================")
    print(f"BATCH COMPLETE! Total Ready Videos: {total_ready} / {len(animals)}")
    print(f"==========================================")

if __name__ == "__main__":
    main()
