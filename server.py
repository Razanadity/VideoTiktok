# -*- coding: utf-8 -*-
"""
High-Performance Multi-Threaded HTTP Server for VideoTiktok Studio.
Supports:
- HTTP 206 Partial Content (Range requests) for smooth video seeking & streaming
- REST API for listing, generating, and exporting 104 animal videos and subtitles
- Zero Arena branding anywhere
"""

import os
import sys
import json
import time
import mimetypes
import threading
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add cwd to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video_engine import render_animal_video
from audio_engine import generate_animal_audio
from artwork_engine import generate_animal_artwork

PORT = 8080
DATASET_FILE = "animals_dataset.json"

# Load animals dataset
if os.path.exists(DATASET_FILE):
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        ANIMALS_DATA = json.load(f)
else:
    ANIMALS_DATA = []

ANIMALS_MAP = {a["id"]: a for a in ANIMALS_DATA}

# Render lock and status tracker
RENDER_STATUS = {}
RENDER_QUEUE = []
RENDER_LOCK = threading.Lock()

def bg_render_worker():
    while True:
        task = None
        with RENDER_LOCK:
            if RENDER_QUEUE:
                task = RENDER_QUEUE.pop(0)
        if task:
            animal_id = task
            RENDER_STATUS[animal_id] = "rendering"
            try:
                animal = ANIMALS_MAP.get(animal_id)
                if animal:
                    out_path = f"videos/{animal_id}.mp4"
                    render_animal_video(animal, out_path)
                    RENDER_STATUS[animal_id] = "ready"
                else:
                    RENDER_STATUS[animal_id] = "error"
            except Exception as e:
                print(f"Error rendering {animal_id}: {e}")
                RENDER_STATUS[animal_id] = "error"
        else:
            time.sleep(0.5)

# Start background rendering thread
render_thread = threading.Thread(target=bg_render_worker, daemon=True)
render_thread.start()

def generate_srt(animal):
    """Generates SubRip (.srt) format subtitles for the animal story."""
    captions = animal.get('captions', [])
    lines = []
    for idx, cap in enumerate(captions, 1):
        s = cap['start']
        e = cap['end']
        s_h, s_m, s_s = int(s // 3600), int((s % 3600) // 60), int(s % 60)
        s_ms = int((s - int(s)) * 1000)
        e_h, e_m, e_s = int(e // 3600), int((e % 3600) // 60), int(e % 60)
        e_ms = int((e - int(e)) * 1000)
        time_str = f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}"
        lines.append(f"{idx}\n{time_str}\n{cap['text']}\n")
    return "\n".join(lines)

def generate_vtt(animal):
    """Generates WebVTT format subtitles for HTML5 video players."""
    captions = animal.get('captions', [])
    lines = ["WEBVTT\n"]
    for idx, cap in enumerate(captions, 1):
        s = cap['start']
        e = cap['end']
        s_h, s_m, s_s = int(s // 3600), int((s % 3600) // 60), int(s % 60)
        s_ms = int((s - int(s)) * 1000)
        e_h, e_m, e_s = int(e // 3600), int((e % 3600) // 60), int(e % 60)
        e_ms = int((e - int(e)) * 1000)
        time_str = f"{s_h:02d}:{s_m:02d}:{s_s:02d}.{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d}.{e_ms:03d}"
        lines.append(f"{idx}\n{time_str}\n{cap['text']}\n")
    return "\n".join(lines)

class VideoStudioHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow cross-origin and iframe embedding in Arena live preview
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        url = self.path.split('?')[0]

        # API: list all animals
        if url == '/api/animals':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            
            # Enrich with video status
            enriched = []
            for a in ANIMALS_DATA:
                item = dict(a)
                v_path = f"videos/{a['id']}.mp4"
                if os.path.exists(v_path):
                    item['video_status'] = 'ready'
                    item['video_url'] = f"/videos/{a['id']}.mp4"
                    item['video_size'] = os.path.getsize(v_path)
                elif a['id'] in RENDER_STATUS:
                    item['video_status'] = RENDER_STATUS[a['id']]
                else:
                    item['video_status'] = 'pending'
                
                item['audio_url'] = f"/audio/{a['id']}.mp3"
                item['image_url'] = f"/images/{a['id']}.png"
                enriched.append(item)
                
            self.wfile.write(json.dumps(enriched, ensure_ascii=False).encode('utf-8'))
            return

        # API: single animal
        if url.startswith('/api/animal/'):
            animal_id = url.split('/')[-1]
            animal = ANIMALS_MAP.get(animal_id)
            if animal:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                item = dict(animal)
                v_path = f"videos/{animal_id}.mp4"
                item['video_status'] = 'ready' if os.path.exists(v_path) else RENDER_STATUS.get(animal_id, 'pending')
                self.wfile.write(json.dumps(item, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
            return

        # API: SRT Subtitles
        if url.startswith('/api/srt/'):
            animal_id = url.split('/')[-1].replace('.srt', '')
            animal = ANIMALS_MAP.get(animal_id)
            if animal:
                srt_content = generate_srt(animal)
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{animal_id}_subtitles.srt"')
                self.end_headers()
                self.wfile.write(srt_content.encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
            return

        # API: WebVTT Subtitles
        if url.startswith('/api/vtt/'):
            animal_id = url.split('/')[-1].replace('.vtt', '')
            animal = ANIMALS_MAP.get(animal_id)
            if animal:
                vtt_content = generate_vtt(animal)
                self.send_response(200)
                self.send_header('Content-Type', 'text/vtt; charset=utf-8')
                self.end_headers()
                self.wfile.write(vtt_content.encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
            return

        # API: Batch Status
        if url == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            ready_count = sum(1 for a in ANIMALS_DATA if os.path.exists(f"videos/{a['id']}.mp4"))
            status_data = {
                "total": len(ANIMALS_DATA),
                "ready": ready_count,
                "queue": len(RENDER_QUEUE),
                "status_map": RENDER_STATUS
            }
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
            return

        # Serve static file with Range support (for smooth MP4 video playback)
        clean_path = url.lstrip('/')
        if clean_path == '' or clean_path == 'index.html':
            clean_path = 'public/index.html'

        if os.path.exists(clean_path) and os.path.isfile(clean_path):
            self.serve_file_with_range(clean_path)
            return

        # Fallback to standard handler
        super().do_GET()

    def do_POST(self):
        url = self.path.split('?')[0]

        # Trigger on-demand video render for an animal
        if url.startswith('/api/generate/'):
            animal_id = url.split('/')[-1]
            animal = ANIMALS_MAP.get(animal_id)
            if animal:
                with RENDER_LOCK:
                    if animal_id not in RENDER_QUEUE:
                        RENDER_QUEUE.insert(0, animal_id)
                        RENDER_STATUS[animal_id] = "queued"
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "queued", "id": animal_id}).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
            return

        # Trigger batch render for all or category
        if url == '/api/generate-all':
            with RENDER_LOCK:
                for a in ANIMALS_DATA:
                    aid = a['id']
                    if not os.path.exists(f"videos/{aid}.mp4") and aid not in RENDER_QUEUE:
                        RENDER_QUEUE.append(aid)
                        RENDER_STATUS[aid] = "queued"
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "batch_queued", "count": len(RENDER_QUEUE)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def serve_file_with_range(self, file_path):
        """Streams files with support for HTTP 206 Partial Content (Range header)."""
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        range_header = self.headers.get('Range')
        if not range_header:
            # Full file
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
            return

        # Handle range header (bytes=start-end)
        try:
            byte_range = range_header.strip().split('=')[1]
            parts = byte_range.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            end = min(end, file_size - 1)
            content_length = end - start + 1

            self.send_response(206)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(content_length))
            self.end_headers()

            with open(file_path, 'rb') as f:
                f.seek(start)
                bytes_to_send = content_length
                while bytes_to_send > 0:
                    chunk_size = min(65536, bytes_to_send)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    bytes_to_send -= len(chunk)
        except Exception as e:
            # Fallback if range fails
            pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = ThreadedHTTPServer(server_address, VideoStudioHandler)
    print(f"🎬 VideoTiktok Server listening on http://0.0.0.0:{PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
