#!/usr/bin/env python3
"""
Loova Seedance 2.0 img2vid script.
Loads LOOVA_API_KEY from environment or .env file.
Usage: python scripts/loova-img2vid.py --prompt "prompt" [--model ...] [--duration 5] [--ratio "16:9"] [--files "url1,url2"]
"""
import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
import requests

# Load .env from current directory or project root
load_dotenv()

IMG2VID_URL = "https://api.loova.ai/v1/img2vid"
VIDEO_ITEM_URL = "https://api.loova.ai/v1/video_item"
POLL_INTERVAL_SEC = 4
MAX_POLL_COUNT = 120  # ~8 minutes


def get_api_key() -> str:
    key = os.environ.get("LOOVA_API_KEY", "").strip()
    if not key:
        print(
            "Error: Set LOOVA_API_KEY in .env or environment (obtain it after logging in at https://loova.ai/)",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def submit_task(api_key: str, args: argparse.Namespace) -> str:
    payload = {
        "model": args.model,
        "params": {
            "prompt": args.prompt,
            "ratio": args.ratio,
            "duration": args.duration,
        },
    }
    if args.function_mode:
        payload["params"]["functionMode"] = args.function_mode
    if args.files:
        payload["params"]["file_paths"] = [u.strip() for u in args.files if u.strip()]

    resp = requests.post(
        IMG2VID_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    task_id = data.get("task_id") or (data.get("data") or {}).get("task_id") or data.get("taskId")
    if not task_id:
        raise RuntimeError("No task_id in response: " + json.dumps(data))
    return task_id


def poll_result(api_key: str, task_id: str) -> dict:
    url = f"{VIDEO_ITEM_URL}?task_id={task_id}"
    for i in range(MAX_POLL_COUNT):
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status") or (data.get("data") or {}).get("status") or data.get("state")
        if status in ("succeeded", "success", "completed"):
            return data
        if status in ("failed", "error"):
            msg = data.get("message") or data.get("error") or json.dumps(data)
            raise RuntimeError("Task failed: " + str(msg))
        if i == 0:
            print("Task submitted, polling...", file=sys.stderr)
        time.sleep(POLL_INTERVAL_SEC)
    raise RuntimeError("Polling timed out")


def main() -> None:
    parser = argparse.ArgumentParser(description="Loova Seedance 2.0 img2vid")
    parser.add_argument("--prompt", required=True, help="Prompt text")
    parser.add_argument("--model", default="jimeng-video-seedance-2.0", help="Model name")
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds (4-15)")
    parser.add_argument("--ratio", default="16:9", help="Aspect ratio")
    parser.add_argument("--function-mode", help="first_last_frames or omni_reference")
    parser.add_argument("--files", help="Comma-separated media URLs")
    args = parser.parse_args()
    args.files = args.files.split(",") if args.files else None

    api_key = get_api_key()
    task_id = submit_task(api_key, args)
    print("task_id:", task_id, file=sys.stderr)
    result = poll_result(api_key, task_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print("Request error:", e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
