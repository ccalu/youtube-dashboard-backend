#!/usr/bin/env python3
"""Run 3 img2 tests - enhance ON, 241 frames, ambient sounds only"""
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
    ("IMG2_P1_marcha", "A military officer walks forward through muddy road, coat swaying in the wind, soldiers marching behind him, camera tracking shot, boots stomping, wind blowing, black and white war documentary"),
    ("IMG2_P2_coluna", "Column of soldiers marching slowly through devastated landscape, rifles in hand, helmets bobbing with each step, smoke drifting from ruins, wind and distant rumbling, cinematic black and white footage"),
    ("IMG2_P3_comando", "Military commander pointing forward and striding through war-torn road, troops following in formation, dust and debris blowing across the path, heavy boots on gravel, atmospheric war documentary, film grain"),
]

print("=" * 60)
print("IMG2 TESTS — enhance ON, 241 frames, ambient sounds")
print("=" * 60)

results = []
for i, (name, prompt) in enumerate(prompts):
    print(f"\n[{i+1}/3] {name}")
    print(f"  Prompt: {prompt[:80]}...")

    wf = json.loads(json.dumps(base_wf))
    for n in wf["nodes"]:
        ntype = n.get("type", "")
        title = n.get("title", "")
        wv = n.get("widgets_values", [])
        nid = n.get("id", 0)

        # Image: img2
        if ntype == "LoadImage" and len(wv) >= 1:
            wv[0] = "img2.png"
        # Prompt
        if ntype == "PrimitiveStringMultiline" and title == "Prompt":
            wv[0] = prompt
        # Negative
        if nid == 315 and ntype == "CLIPTextEncode":
            wv[0] = "pc game, console game, video game, cartoon, childish, ugly"
        # Vertical
        if ntype == "PrimitiveInt" and title == "Width":
            wv[0] = 720
        if ntype == "PrimitiveInt" and title == "Height":
            wv[0] = 1280
        if ntype == "ImageResizeKJv2" and len(wv) >= 2:
            wv[0] = 720
            wv[1] = 1280
        # 241 frames
        if ntype == "PrimitiveInt" and title == "Length":
            wv[0] = 241
        # Enhance ON
        if ntype == "ComfySwitchNode" and title == "Switch (Enhance Prompt)":
            wv[0] = True
        # Save
        if ntype == "SaveVideo" and len(wv) >= 1:
            wv[0] = name

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
