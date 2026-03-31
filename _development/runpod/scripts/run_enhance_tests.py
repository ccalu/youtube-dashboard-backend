#!/usr/bin/env python3
"""Run 5 enhance tests - same workflow, different prompts"""
import json, urllib.request, time

COMFY = "http://localhost:3000"

def convert(wf):
    data = json.dumps(wf).encode()
    req = urllib.request.Request(COMFY+"/workflow/convert", data=data, headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def queue(api):
    data = json.dumps({"prompt": api}).encode()
    req = urllib.request.Request(COMFY+"/prompt", data=data, headers={"Content-Type":"application/json"})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        print(f"  Queue error: {e.read().decode()[:300]}")
        return None

def wait(pid, timeout=1200):
    t0 = time.time()
    while time.time()-t0 < timeout:
        try:
            h = json.loads(urllib.request.urlopen(COMFY+"/history/"+pid).read())
            if pid in h:
                return h[pid], time.time()-t0
        except:
            pass
        time.sleep(5)
    return None, time.time()-t0

# Load base workflow
with open("/workspace/EN_P1_ultracurto.json", encoding="utf-8") as f:
    base_wf = json.load(f)

prompts = [
    ("EN_P1_ultracurto", "Two soldiers fighting brutally in the snow, camera push in, close-up shot, background explosions and gunfire"),
    ("EN_P2_slow", "Two soldiers in a slow heavy grapple in the snow, grabbing each other tightly, camera push in, medium shot, burning ruins behind, distant artillery sounds"),
    ("EN_P3_textura", "Two soldiers wrestling in deep snow, detailed wool uniforms, weathered helmets, close-up handheld camera, snowy battlefield, black smoke rising, war documentary footage"),
    ("EN_P4_direcao", "Handheld camera, two soldiers locked in brutal close combat in the snow. One grabs the other by the collar and shoves him. Snow kicks up from their boots. Burning buildings and thick smoke behind them. 35mm war film, gritty and raw"),
    ("EN_P5_atmosfera", "Shaky close-up camera, two soldiers struggling against each other in a snow-covered battlefield. Slow heavy physical combat. Heavy breathing visible in cold air. Fires flickering in destroyed buildings. Tank engine rumbling. Cinematic war documentary, desaturated winter colors, film grain"),
]

print("=" * 60)
print("LTX 2.3 ENHANCE TESTS — 5 prompts, enhance ON, 241 frames")
print("=" * 60)

results = []
for i, (name, prompt) in enumerate(prompts):
    print(f"\n[{i+1}/5] {name}")
    print(f"  Prompt: {prompt[:80]}...")

    # Clone base workflow and change prompt + save name
    wf = json.loads(json.dumps(base_wf))
    for n in wf["nodes"]:
        if n.get("type") == "PrimitiveStringMultiline" and n.get("title") == "Prompt":
            n["widgets_values"][0] = prompt
        if n.get("type") == "SaveVideo":
            n["widgets_values"][0] = name

    # Convert and queue
    try:
        api = convert(wf)
        print(f"  Converted: {len(api)} nodes")
    except Exception as e:
        print(f"  Convert FAIL")
        results.append((name, "FAIL", 0))
        continue

    r = queue(api)
    if not r:
        results.append((name, "FAIL", 0))
        continue

    pid = r["prompt_id"]
    print(f"  Generating...", end="", flush=True)

    completion, elapsed = wait(pid, 1200)
    if completion and completion["status"]["status_str"] == "success":
        files = []
        for nid, o in completion.get("outputs", {}).items():
            for k in ["gifs", "videos"]:
                if k in o:
                    for f in o[k]:
                        files.append(f["filename"])
        print(f" DONE! {elapsed:.0f}s ({elapsed/60:.1f}min)")
        for f in files:
            print(f"  >> {f}")
        results.append((name, "OK", elapsed))
    else:
        print(f" FAIL {elapsed:.0f}s")
        results.append((name, "FAIL", elapsed))

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
total = sum(t for _,_,t in results)
for name, status, t in results:
    ts = f"{t:.0f}s ({t/60:.1f}min)" if t > 0 else "-"
    print(f"  {name:<25} {status:<6} {ts}")
print(f"  TOTAL: {total:.0f}s ({total/60:.1f}min) | Cost: ${total/3600*0.89:.2f}")
print("=" * 60)
