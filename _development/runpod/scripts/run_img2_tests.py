#!/usr/bin/env python3
"""Run img2 tests only"""
import json, urllib.request, time

COMFY_URL = "http://localhost:8188"

def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except Exception as e:
        print(f"  Error: {e}")
        return None

def wait_done(pid, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFY_URL}/history/{pid}").read())
            if pid in h: return h[pid]
        except: pass
        time.sleep(3)
    return None

def wf(img, prompt, steps, w, h, name):
    neg = "blurry, low quality, artifacts, watermark, text, logo, distorted, flickering, cartoon, ugly"
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors"}},
        "2": {"class_type": "LTXAVTextEncoderLoader", "inputs": {"text_encoder": "gemma_3_12B_it_heretic_fp8.safetensors", "ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors", "device": "default"}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["2", 0]}},
        "5": {"class_type": "LoadImage", "inputs": {"image": img, "upload": "image"}},
        "6": {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["3", 0], "negative": ["4", 0], "vae": ["1", 2], "image": ["5", 0], "width": w, "height": h, "length": 81, "batch_size": 1, "strength": 0.85}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["6", 0], "negative": ["6", 1], "latent_image": ["6", 2], "seed": 42, "steps": steps, "cfg": 3.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "8": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["7", 0], "vae": ["1", 2], "tile_size": 512, "overlap": 64, "temporal_size": 256, "temporal_overlap": 32}},
        "9": {"class_type": "VHS_VideoCombine", "inputs": {"images": ["8", 0], "frame_rate": 25, "loop_count": 0, "filename_prefix": name, "format": "video/h264-mp4", "save_output": True, "pingpong": False, "crf": 19}}
    }

p = "A determined military officer strides forward through muddy terrain, boots splashing through puddles, gesturing commands with his outstretched arm as his coat sways. Behind him soldiers march in formation through devastated landscape. Smoke drifts from destroyed buildings. Black and white documentary war footage, atmospheric."

tests = [
    ("img2.png", p, 8, 720, 1280, "img2_8steps_720p"),
    ("img2.png", p, 14, 720, 1280, "img2_14steps_720p"),
    ("img2.png", p, 20, 720, 1280, "img2_20steps_720p"),
    ("img2.png", p, 14, 1080, 1920, "img2_14steps_1080p"),
]

for i, (img, prompt, steps, w, h, name) in enumerate(tests):
    print(f"[{i+1}/4] {name}")
    t0 = time.time()
    r = queue_prompt(wf(img, prompt, steps, w, h, name))
    if not r:
        print("  FAILED to queue")
        continue
    c = wait_done(r["prompt_id"], 600)
    elapsed = time.time() - t0
    if c and c["status"]["status_str"] == "success":
        for nid, o in c.get("outputs", {}).items():
            for k in ["gifs", "videos"]:
                if k in o:
                    for f in o[k]:
                        print(f"  OK {elapsed:.0f}s >> {f['filename']}")
    else:
        print(f"  FAILED {elapsed:.0f}s")
        if c:
            for m in c["status"].get("messages", []):
                if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict):
                    print(f"  {m[1].get('exception_message', '?')[:200]}")

print("\nDONE. All img2 tests complete.")
