#!/usr/bin/env python3
"""LTX 2.3 DEV — Sweet Spot Tests
   Workflow correto: CFGGuider + KSamplerSelect(euler) + LTXVScheduler + SamplerCustomAdvanced
   Baseado no workflow funcional do Lucca (ltx2_i2v_dev_fp8.json)
"""
import json, urllib.request, time

COMFY_URL = "http://localhost:3000"

def queue(prompt):
    data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except Exception as e:
        if hasattr(e, 'read'):
            print(f"  API Error: {e.read().decode()[:400]}")
        else:
            print(f"  Error: {e}")
        return None

def wait(pid, timeout=1200):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFY_URL}/history/{pid}").read())
            if pid in h: return h[pid]
        except: pass
        time.sleep(5)
    return None

def build_dev_i2v(img, prompt, neg, steps, cfg, strength, w, h, num_frames, name):
    """Workflow CORRETO para DEV model.
    Pipeline: Checkpoint → LTXAVTextEncoderLoader → CLIPTextEncode →
              LTXVPreprocess → LTXVImgToVideo → CFGGuider →
              KSamplerSelect(euler) → LTXVScheduler → RandomNoise →
              SamplerCustomAdvanced → VAEDecode → VHS_VideoCombine
    """
    return {
        # 1. Load DEV checkpoint
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}
        },
        # 2. Load text encoder (Gemma + embeddings from checkpoint)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it_heretic_fp8.safetensors",
                "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors",
                "device": "default"
            }
        },
        # 3. Positive prompt
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]}
        },
        # 4. Negative prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": neg, "clip": ["2", 0]}
        },
        # 5. Load image
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": img, "upload": "image"}
        },
        # 6. Preprocess image for LTX (img_compression=35 default balanced)
        "6": {
            "class_type": "LTXVPreprocess",
            "inputs": {"image": ["5", 0], "img_compression": 35}
        },
        # 7. Image to Video conditioning
        "7": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["3", 0],
                "negative": ["4", 0],
                "vae": ["1", 2],
                "image": ["6", 0],
                "width": w,
                "height": h,
                "length": num_frames,
                "batch_size": 1,
                "strength": strength
            }
        },
        # 8. CFG Guider (NOT KSampler's built-in CFG)
        "8": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["1", 0],
                "positive": ["7", 0],
                "negative": ["7", 1],
                "cfg": cfg
            }
        },
        # 9. Sampler select: euler (NOT euler_ancestral!)
        "9": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # 10. LTXVScheduler (proper sigma schedule for DEV)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": steps,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1
            }
        },
        # 11. Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": 42}
        },
        # 12. SamplerCustomAdvanced (proper sampling pipeline)
        "12": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0],
                "guider": ["8", 0],
                "sampler": ["9", 0],
                "sigmas": ["10", 0],
                "latent_image": ["7", 2]
            }
        },
        # 13. VAE Decode
        "13": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["12", 1],
                "vae": ["1", 2]
            }
        },
        # 14. Save video
        "14": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["13", 0],
                "frame_rate": 25,
                "loop_count": 0,
                "filename_prefix": name,
                "format": "video/h264-mp4",
                "save_output": True,
                "pingpong": False,
                "crf": 19
            }
        }
    }

# Same prompt for ALL tests
PROMPT = "The two soldiers erupt into vicious hand-to-hand combat. The soldier on the left throws a powerful right hook while the other blocks with his forearm and counters with a knee strike to the ribs. They grapple and shove each other through the deep snow, boots kicking up white powder with every violent step. Their breath forms thick clouds in the freezing air. Burning embers drift down from the destroyed buildings behind them. The distant tank turret rotates slowly as black smoke billows upward into the grey winter sky. Heavy snowfall intensifies throughout the scene. Handheld camera, close tracking shot, gritty desaturated war film cinematography, 35mm lens."

NEG = "worst quality, inconsistent motion, blurry, jittery, distorted, watermarks, morphing, flicker, text, logo, cartoon, CGI, 3D render, anime, still image, static, frozen"

# 6 tests: 3 with 25 steps, 3 with 30 steps, varying CFG
# strength=0.55 (Lucca's proven value), 720x1280, 161 frames
tests = [
    # 25 steps - varying CFG
    (25, 3.0, 0.55, "T1_25steps_cfg3.0"),
    (25, 4.0, 0.55, "T2_25steps_cfg4.0"),
    (25, 5.0, 0.55, "T3_25steps_cfg5.0"),
    # 30 steps - varying CFG
    (30, 3.0, 0.55, "T4_30steps_cfg3.0"),
    (30, 4.0, 0.55, "T5_30steps_cfg4.0"),
    (30, 5.0, 0.55, "T6_30steps_cfg5.0"),
]

print("=" * 65)
print("LTX 2.3 DEV — SWEET SPOT TESTS on RTX 5090")
print("Workflow: CFGGuider + euler + LTXVScheduler + SamplerCustomAdvanced")
print("Fixed: img1.png | 720x1280 | 161 frames (~6.4s) | strength=0.55")
print("Variable: steps (25/30) x cfg (3.0/4.0/5.0)")
print("=" * 65)

results = []
for i, (steps, cfg, strength, name) in enumerate(tests):
    print(f"\n[{i+1}/{len(tests)}] {name} — {steps} steps, cfg={cfg}, str={strength}")
    wf = build_dev_i2v("img1.png", PROMPT, NEG, steps, cfg, strength, 720, 1280, 161, name)
    t0 = time.time()
    r = queue(wf)
    if not r:
        results.append((name, steps, cfg, strength, "FAIL", 0))
        continue
    pid = r["prompt_id"]
    print(f"  Queued: {pid[:12]}...")
    print(f"  Generating...", end="", flush=True)
    c = wait(pid, 1200)
    elapsed = time.time() - t0
    if c and c["status"]["status_str"] == "success":
        for nid, o in c.get("outputs", {}).items():
            for k in ["gifs", "videos"]:
                if k in o:
                    for f in o[k]:
                        print(f" DONE! {elapsed:.0f}s ({elapsed/60:.1f}min) >> {f['filename']}")
        results.append((name, steps, cfg, strength, "OK", elapsed))
    else:
        print(f" FAILED {elapsed:.0f}s")
        if c:
            for m in c["status"].get("messages", []):
                if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict):
                    print(f"  Error: {m[1].get('exception_message', '?')[:300]}")
        results.append((name, steps, cfg, strength, "FAIL", elapsed))

print("\n" + "=" * 65)
print("RESULTS — LTX 2.3 DEV Sweet Spot Tests")
print("=" * 65)
print(f"{'Test':<25} {'Steps':>5} {'CFG':>5} {'Str':>5} {'Status':>7} {'Time':>12}")
print("-" * 65)
total = 0
for name, steps, cfg, strength, status, t in results:
    total += t
    ts = f"{t:.0f}s ({t/60:.1f}m)" if t > 0 else "-"
    print(f"{name:<25} {steps:>5} {cfg:>5.1f} {strength:>5.2f} {status:>7} {ts:>12}")
print("-" * 65)
print(f"TOTAL: {total:.0f}s ({total/60:.1f}min) | Pod cost: ${total/3600 * 0.69:.3f}")
print("=" * 65)
