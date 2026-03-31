#!/usr/bin/env python3
"""LTX 2.3 I2V Test Suite — Content Factory"""

import json, urllib.request, time, sys, os

COMFY_URL = "http://localhost:8188"

def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  API Error {e.code}: {error_body[:500]}")
        return None

def wait_for_completion(prompt_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except:
            pass
        time.sleep(3)
    return None

def build_simple_i2v(image_name, prompt_text, steps, width, height, output_name):
    """Build a minimal I2V workflow using available nodes."""
    neg = "blurry, low quality, artifacts, watermark, text, logo, distorted, flickering, jittery, out of focus, overexposed, cartoon, ugly"

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors"}
        },
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it_heretic_fp8.safetensors",
                "ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors",
                "device": "default"
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt_text, "clip": ["2", 0]}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": neg, "clip": ["2", 0]}
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name, "upload": "image"}
        },
        "6": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["3", 0],
                "negative": ["4", 0],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": width,
                "height": height,
                "length": 81,
                "batch_size": 1,
                "strength": 0.85
            }
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "latent_image": ["6", 2],
                "seed": 42,
                "steps": steps,
                "cfg": 3.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["1", 2],
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 256,
                "temporal_overlap": 32
            }
        },
        "9": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["8", 0],
                "frame_rate": 25,
                "loop_count": 0,
                "filename_prefix": output_name,
                "format": "video/h264-mp4",
                "save_output": True,
                "pingpong": False,
                "crf": 19
            }
        }
    }
    return workflow

# Test configurations
tests = [
    ("img1.png",
     "Two soldiers grapple fiercely in brutal hand-to-hand combat, struggling and pushing each other violently through the snow. Their bodies twist and strain as fists connect. Snowflakes swirl around them. Flames flicker from burning ruins behind, thick smoke rises, distant soldiers charge. Tank turret rotates slowly. Cinematic war scene, gritty and visceral.",
     8, 720, 1280, "img1_8steps_720p"),
    ("img1.png",
     "Two soldiers grapple fiercely in brutal hand-to-hand combat, struggling and pushing each other violently through the snow. Their bodies twist and strain as fists connect. Snowflakes swirl around them. Flames flicker from burning ruins behind, thick smoke rises, distant soldiers charge. Tank turret rotates slowly. Cinematic war scene, gritty and visceral.",
     14, 720, 1280, "img1_14steps_720p"),
    ("img1.png",
     "Two soldiers grapple fiercely in brutal hand-to-hand combat, struggling and pushing each other violently through the snow. Their bodies twist and strain as fists connect. Snowflakes swirl around them. Flames flicker from burning ruins behind, thick smoke rises, distant soldiers charge. Tank turret rotates slowly. Cinematic war scene, gritty and visceral.",
     20, 720, 1280, "img1_20steps_720p"),
    ("img1.png",
     "Two soldiers grapple fiercely in brutal hand-to-hand combat, struggling and pushing each other violently through the snow. Their bodies twist and strain as fists connect. Snowflakes swirl around them. Flames flicker from burning ruins behind, thick smoke rises, distant soldiers charge. Tank turret rotates slowly. Cinematic war scene, gritty and visceral.",
     14, 1080, 1920, "img1_14steps_1080p"),
    ("img2.png",
     "A determined military officer strides forward through muddy terrain, boots splashing through puddles, gesturing commands with his outstretched arm as his coat sways with each powerful step. Behind him a column of weary soldiers marches in formation, rifles in hand, pushing through devastated landscape. Smoke drifts from destroyed buildings. Black and white documentary war footage, atmospheric and haunting.",
     8, 720, 1280, "img2_8steps_720p"),
    ("img2.png",
     "A determined military officer strides forward through muddy terrain, boots splashing through puddles, gesturing commands with his outstretched arm as his coat sways with each powerful step. Behind him a column of weary soldiers marches in formation, rifles in hand, pushing through devastated landscape. Smoke drifts from destroyed buildings. Black and white documentary war footage, atmospheric and haunting.",
     14, 720, 1280, "img2_14steps_720p"),
    ("img2.png",
     "A determined military officer strides forward through muddy terrain, boots splashing through puddles, gesturing commands with his outstretched arm as his coat sways with each powerful step. Behind him a column of weary soldiers marches in formation, rifles in hand, pushing through devastated landscape. Smoke drifts from destroyed buildings. Black and white documentary war footage, atmospheric and haunting.",
     20, 720, 1280, "img2_20steps_720p"),
    ("img2.png",
     "A determined military officer strides forward through muddy terrain, boots splashing through puddles, gesturing commands with his outstretched arm as his coat sways with each powerful step. Behind him a column of weary soldiers marches in formation, rifles in hand, pushing through devastated landscape. Smoke drifts from destroyed buildings. Black and white documentary war footage, atmospheric and haunting.",
     14, 1080, 1920, "img2_14steps_1080p"),
]

results = []
print("=" * 60)
print("LTX 2.3 I2V TEST SUITE - Content Factory")
print(f"GPU: RTX A6000 48GB | Pod cost: $0.33/hr")
print(f"Tests: {len(tests)} total")
print("=" * 60)

for i, (img, prompt, steps, w, h, name) in enumerate(tests):
    print(f"\n[{i+1}/{len(tests)}] {name}")
    print(f"  Image: {img} | Steps: {steps} | Res: {w}x{h}")

    workflow = build_simple_i2v(img, prompt, steps, w, h, name)

    start_time = time.time()
    result = queue_prompt(workflow)

    if not result:
        print("  FAILED to queue")
        results.append((name, "FAILED", 0))
        continue

    prompt_id = result.get("prompt_id", "")
    print(f"  Queued: {prompt_id}")
    print(f"  Generating...", end="", flush=True)

    completion = wait_for_completion(prompt_id, timeout=600)
    elapsed = time.time() - start_time

    if completion:
        status = completion.get("status", {})
        if status.get("status_str") == "success":
            print(f" DONE! {elapsed:.1f}s ({elapsed/60:.1f}min)")
            outputs = completion.get("outputs", {})
            for nid, output in outputs.items():
                for key in ["gifs", "videos", "images"]:
                    if key in output:
                        for item in output[key]:
                            fname = item.get("filename", "?")
                            print(f"  >> Saved: {fname}")
            results.append((name, "OK", elapsed))
        else:
            print(f" FAILED after {elapsed:.1f}s")
            msgs = status.get("messages", [])
            for msg in msgs:
                if isinstance(msg, list) and len(msg) > 1:
                    details = msg[1] if isinstance(msg[1], dict) else {}
                    print(f"  Error: {details.get('node_type','?')}: {details.get('exception_message','?')[:200]}")
            results.append((name, "FAILED", elapsed))
    else:
        print(f" TIMEOUT after {elapsed:.1f}s")
        results.append((name, "TIMEOUT", elapsed))

# Summary
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
total_time = sum(t for _, _, t in results if t > 0)
print(f"{'Test':<25} {'Status':<10} {'Time'}")
print("-" * 55)
for name, status, elapsed in results:
    time_str = f"{elapsed:.1f}s ({elapsed/60:.1f}min)" if elapsed > 0 else "-"
    print(f"{name:<25} {status:<10} {time_str}")
print("-" * 55)
print(f"{'TOTAL':<25} {'':10} {total_time:.1f}s ({total_time/60:.1f}min)")
print(f"Pod cost estimate: ${total_time/3600 * 0.33:.2f}")
print("=" * 60)
