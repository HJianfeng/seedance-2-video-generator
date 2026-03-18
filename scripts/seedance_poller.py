#!/usr/bin/env python3
"""Seedance background poller.

- Reads pending tasks from ~/.openclaw/seedance_tasks.jsonl
- Polls Loova task API every `--interval` seconds (default 60)
- On terminal state, sends a Feishu DM to the requester (if provided in record), including prompt/params summary.

Records format: JSON lines appended by run_seedance.py.
This poller is designed to be run as a long-lived background process.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

VIDEO_ITEM_URL = "https://api.loova.ai/api/v1/tasks"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def queue_path() -> str:
    return os.path.expanduser("~/.openclaw/seedance_tasks.jsonl")


def load_api_key(env_path: str | None) -> str:
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()
    key = os.environ.get("LOOVA_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing LOOVA_API_KEY")
    return key


def read_records(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                # skip corrupted line
                continue
    return out


def write_records(path: str, records: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def fetch_task(task_id: str, api_key: str) -> dict:
    url = f"{VIDEO_ITEM_URL}?task_id={task_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    r.raise_for_status()
    return r.json()


def norm_status(data: dict) -> str:
    s = data.get("status") or (data.get("data") or {}).get("status") or data.get("state")
    return str(s or "unknown").lower()


def build_summary(rec: dict) -> str:
    # Keep it compact but useful.
    prompt = (rec.get("prompt") or "").strip()
    if len(prompt) > 240:
        prompt = prompt[:240] + "…"
    parts = [
        f"model={rec.get('model')}",
        f"ratio={rec.get('ratio')}",
        f"duration={rec.get('duration')}s",
    ]
    if rec.get("function_mode"):
        parts.append(f"functionMode={rec.get('function_mode')}")
    return "参数: " + ", ".join(parts) + "\n" + "提示词: " + prompt


def send_feishu(message: str, target: str | None) -> None:
    """Send via OpenClaw message tool by invoking the local CLI event bridge.

    We avoid importing OpenClaw internals here; instead, we print a marker line that
    the parent agent can pick up if running under tool supervision.

    If you want direct sending from this script, wire it through a proper OpenClaw plugin.
    """
    # For now: write to stdout as a structured line.
    payload = {"type": "notify", "target": target, "message": message}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--env", default=None, help="Optional .env path to load LOOVA_API_KEY")
    args = ap.parse_args()

    api_key = load_api_key(args.env)
    path = queue_path()

    while True:
        records = read_records(path)
        changed = False

        for rec in records:
            if rec.get("notified"):
                continue
            task_id = rec.get("task_id")
            if not task_id:
                rec["notified"] = True
                rec["error"] = "missing_task_id"
                changed = True
                continue

            try:
                data = fetch_task(task_id, api_key)
            except Exception as e:
                rec["last_checked_at"] = utc_now_iso()
                rec["last_error"] = str(e)
                changed = True
                continue

            status = norm_status(data)
            rec["last_checked_at"] = utc_now_iso()
            rec["status"] = status

            if status in {"succeeded", "success", "completed", "failed", "error"}:
                rec["result"] = data
                rec["notified"] = True
                changed = True

                # Extract video_url if present
                video_url = None
                try:
                    video_url = (data.get("data") or {}).get("result", {}).get("video_url")
                except Exception:
                    video_url = None

                header = f"Seedance任务完成: {task_id}（{status}）"
                body = build_summary(rec)
                if video_url:
                    msg = header + "\n" + video_url + "\n\n" + body
                else:
                    msg = header + "\n\n" + body

                send_feishu(msg, rec.get("notify_target"))

        if changed:
            write_records(path, records)

        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
