#!/usr/bin/env python3
"""
LTX 2.3 — Executor de Workflows via ComfyUI API
Usa o endpoint /workflow/convert para conversao confiavel frontend→API.
"""
import json
import urllib.request
import time
import os
import sys

COMFY_URL = "http://localhost:3000"


def convert_workflow(frontend_json):
    """Convert frontend workflow to API format using Seth Robinson's converter."""
    data = json.dumps(frontend_json).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/workflow/convert",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  Convert error: {e.read().decode()[:300]}")
        return None
    except Exception as e:
        print(f"  Convert error: {e}")
        return None


def queue_prompt(api_workflow):
    """Submit API format workflow to ComfyUI."""
    data = json.dumps({"prompt": api_workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  Queue error {e.code}: {body[:500]}")
        return None


def wait_for_completion(prompt_id, timeout=1200):
    """Wait for workflow execution to complete."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except:
            pass
        time.sleep(5)
    return None


def run_test(workflow_path, test_name):
    """Load, convert, and execute a single workflow test."""
    print(f"\n{'='*60}")
    print(f"  {test_name}")
    print(f"  File: {os.path.basename(workflow_path)}")
    print(f"{'='*60}")

    # Load frontend workflow
    with open(workflow_path, encoding="utf-8") as f:
        frontend_wf = json.load(f)

    # Convert to API format
    print("  Converting frontend → API format...")
    api_wf = convert_workflow(frontend_wf)
    if not api_wf:
        print("  FAILED: conversion error")
        return "CONVERT_FAIL", 0

    print(f"  Converted: {len(api_wf)} nodes")

    # Queue execution
    print("  Submitting to ComfyUI...")
    t0 = time.time()
    result = queue_prompt(api_wf)

    if not result:
        print("  FAILED: queue error")
        return "QUEUE_FAIL", 0

    prompt_id = result.get("prompt_id", "")
    print(f"  Queued: {prompt_id[:16]}...")
    print(f"  Generating...", end="", flush=True)

    # Wait for completion
    completion = wait_for_completion(prompt_id, 1200)
    elapsed = time.time() - t0

    if completion:
        status = completion.get("status", {})
        if status.get("status_str") == "success":
            print(f"\n  DONE! {elapsed:.0f}s ({elapsed/60:.1f}min)")
            outputs = completion.get("outputs", {})
            for nid, output in outputs.items():
                for key in ["gifs", "videos", "images"]:
                    if key in output:
                        for item in output[key]:
                            fname = item.get("filename", "?")
                            print(f"  >> Saved: {fname}")
            return "OK", elapsed
        else:
            print(f"\n  FAILED after {elapsed:.0f}s")
            msgs = status.get("messages", [])
            for msg in msgs:
                if isinstance(msg, list) and len(msg) > 1 and isinstance(msg[1], dict):
                    err_msg = msg[1].get("exception_message", "?")
                    node_type = msg[1].get("node_type", "?")
                    print(f"  Error [{node_type}]: {err_msg[:300]}")
            return "EXEC_FAIL", elapsed
    else:
        print(f"\n  TIMEOUT after {elapsed:.0f}s")
        return "TIMEOUT", elapsed


if __name__ == "__main__":
    workflows_dir = "/workspace/workflows"

    tests = [
        (f"{workflows_dir}/TEST_A_two_stage_vertical.json",
         "TEST A: Lightricks Two-Stage (DEV + LoRA + latent upscale)"),
        (f"{workflows_dir}/TEST_C_runexx_vertical.json",
         "TEST C: RuneXX Single Pass (simplest, no ClownSampler)"),
    ]

    print("=" * 60)
    print("LTX 2.3 DEV — WORKFLOW TESTS (RTX 5090)")
    print("Using /workflow/convert for reliable execution")
    print("Resolution: 736x1280 vertical | 121 frames (~5s)")
    print("=" * 60)

    # Verify converter endpoint exists
    print("\nChecking converter endpoint...")
    try:
        req = urllib.request.Request(f"{COMFY_URL}/workflow/convert",
                                     data=b'{}',
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
        print("  Converter: OK")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print("  Converter: OK (400 = endpoint exists, empty input)")
        else:
            print(f"  Converter: ERROR {e.code} — may not be installed!")
            print("  Install: cd custom_nodes && git clone https://github.com/SethRobinson/comfyui-workflow-to-api-converter-endpoint.git")
            sys.exit(1)
    except Exception as e:
        print(f"  Converter: ERROR — {e}")
        sys.exit(1)

    results = []
    for wf_path, name in tests:
        status, elapsed = run_test(wf_path, name)
        results.append((name, status, elapsed))

    # Summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    total = sum(t for _, _, t in results if t)
    for name, status, elapsed in results:
        ts = f"{elapsed:.0f}s ({elapsed/60:.1f}min)" if elapsed else "-"
        s = status or "N/A"
        print(f"  {s:<12} {ts:<15} {name[:45]}")
    print(f"\n  TOTAL: {total:.0f}s ({total/60:.1f}min)")
    print(f"  Pod cost: ${total/3600 * 0.69:.3f}")
    print("=" * 60)
