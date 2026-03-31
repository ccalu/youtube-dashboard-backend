#!/usr/bin/env python3
"""LTX 2.3 I2V Animation Tests - Professional Prompts, 161 frames (~6.4s)"""
import json, urllib.request, time

COMFY_URL = "http://localhost:3000"

def queue(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except Exception as e:
        print(f"  Queue error: {e}")
        return None

def wait(pid, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFY_URL}/history/{pid}").read())
            if pid in h: return h[pid]
        except: pass
        time.sleep(5)
    return None

def wf(img, prompt, steps, w, h, name, num_frames=161):
    neg = "blurry, low quality, distorted, watermark, text, flickering, morphing, warping, shaky, cartoon, extra limbs, deformed"
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors"}},
        "2": {"class_type": "LTXAVTextEncoderLoader", "inputs": {"text_encoder": "gemma_3_12B_it_heretic_fp8.safetensors", "ckpt_name": "ltx-2.3-22b-distilled-fp8.safetensors", "device": "default"}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["2", 0]}},
        "5": {"class_type": "LoadImage", "inputs": {"image": img, "upload": "image"}},
        "6": {"class_type": "LTXVImgToVideo", "inputs": {
            "positive": ["3", 0], "negative": ["4", 0], "vae": ["1", 2],
            "image": ["5", 0], "width": w, "height": h,
            "length": num_frames, "batch_size": 1, "strength": 0.65
        }},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["6", 0], "negative": ["6", 1],
            "latent_image": ["6", 2], "seed": 42, "steps": steps,
            "cfg": 4.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0
        }},
        "8": {"class_type": "VAEDecodeTiled", "inputs": {
            "samples": ["7", 0], "vae": ["1", 2],
            "tile_size": 512, "overlap": 64, "temporal_size": 256, "temporal_overlap": 32
        }},
        "9": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["8", 0], "frame_rate": 25, "loop_count": 0,
            "filename_prefix": name, "format": "video/h264-mp4",
            "save_output": True, "pingpong": False, "crf": 19
        }}
    }

# Professional prompts
prompt_img1 = "The two soldiers erupt into vicious hand-to-hand combat. The soldier on the left throws a powerful right hook while the other blocks with his forearm and counters with a knee strike to the ribs. They grapple and shove each other through the deep snow, boots kicking up white powder with every violent step. Their breath forms thick clouds in the freezing air. Burning embers drift down from the destroyed buildings behind them. The distant tank turret rotates slowly as black smoke billows upward into the grey winter sky. Heavy snowfall intensifies throughout the scene. Handheld camera, close tracking shot, gritty desaturated war film cinematography, 35mm lens."

prompt_img2 = "The commanding officer strides forward with powerful deliberate steps through the muddy road, his boots splashing through shallow puddles. He raises his right arm and points forward, shouting orders to his men. His long military coat sways and flaps with each forceful stride. Behind him, the column of weary soldiers marches in tight formation, their helmets bobbing rhythmically, rifles gripped at their sides. Wind sweeps dust and debris across the devastated road. Dead tree branches sway in the background. Smoke rises lazily from the ruins of distant buildings. Steady forward tracking camera following the officer, black and white wartime documentary footage, grainy film texture, dramatic low-angle perspective."

tests = [
    ("img1.png", prompt_img1, 8,  720, 1280, "anim_img1_8steps_720p"),
    ("img1.png", prompt_img1, 14, 720, 1280, "anim_img1_14steps_720p"),
    ("img2.png", prompt_img2, 8,  720, 1280, "anim_img2_8steps_720p"),
    ("img2.png", prompt_img2, 14, 720, 1280, "anim_img2_14steps_720p"),
]

print("=" * 60)
print("LTX 2.3 ANIMATION TESTS — 161 frames (~6.4s)")
print("strength=0.65 | cfg=4.0 | 720x1280")
print("=" * 60)

results = []
for i, (img, p, steps, w, h, name) in enumerate(tests):
    print(f"\n[{i+1}/4] {name}")
    t0 = time.time()
    r = queue(wf(img, p, steps, w, h, name))
    if not r:
        results.append((name, "FAIL", 0))
        continue
    pid = r["prompt_id"]
    print(f"  Queued. Generating...", end="", flush=True)
    c = wait(pid, 900)
    elapsed = time.time() - t0
    if c and c["status"]["status_str"] == "success":
        for nid, o in c.get("outputs", {}).items():
            for k in ["gifs", "videos"]:
                if k in o:
                    for f in o[k]:
                        print(f" DONE! {elapsed:.0f}s ({elapsed/60:.1f}min) >> {f['filename']}")
        results.append((name, "OK", elapsed))
    else:
        print(f" FAILED {elapsed:.0f}s")
        if c:
            for m in c["status"].get("messages", []):
                if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict):
                    print(f"  Error: {m[1].get('exception_message', '?')[:200]}")
        results.append((name, "FAIL", elapsed))

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
total = sum(t for _, _, t in results)
for name, status, t in results:
    print(f"  {name:<30} {status:<6} {t:.0f}s ({t/60:.1f}min)")
print(f"  {'TOTAL':<30} {'':6} {total:.0f}s ({total/60:.1f}min)")
print(f"  Pod cost: ${total/3600 * 0.33:.3f}")
print("=" * 60)
