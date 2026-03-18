#!/usr/bin/env python3
"""Check a Loova Seedance task status once (optionally watch).

Usage:
  python scripts/check_seedance.py --task-id <id>
  python scripts/check_seedance.py --task-id <id> --watch --interval 60 --max-minutes 180

Outputs a single JSON object to stdout.
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


def load_key() -> str:
    load_dotenv()  # allow .env in cwd
    key = os.environ.get("LOOVA_API_KEY", "").strip()
    if not key:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_LOOVA_API_KEY",
                    "hint": "Set LOOVA_API_KEY in environment or .env",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def fetch_task(task_id: str, api_key: str) -> dict:
    url = f"{VIDEO_ITEM_URL}?task_id={task_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    r.raise_for_status()
    return r.json()


def norm_status(data: dict) -> str:
    s = data.get("status") or (data.get("data") or {}).get("status") or data.get("state")
    return str(s or "unknown")


def main() -> None:
    p = argparse.ArgumentParser(description="Check Seedance task status")
    p.add_argument("--task-id", required=True)
    p.add_argument("--watch", action="store_true")
    p.add_argument("--interval", type=int, default=60)
    p.add_argument("--max-minutes", type=int, default=180)
    args = p.parse_args()

    key = load_key()

    start = time.time()
    while True:
        data = fetch_task(args.task_id, key)
        status = norm_status(data).lower()

        # terminal states
        if status in {"succeeded", "success", "completed", "failed", "error"} or not args.watch:
            out = {
                "ok": True,
                "checked_at": utc_now_iso(),
                "task_id": args.task_id,
                "status": status,
                "data": data,
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        # keep watching
        elapsed_min = (time.time() - start) / 60.0
        if elapsed_min >= args.max_minutes:
            out = {
                "ok": False,
                "checked_at": utc_now_iso(),
                "task_id": args.task_id,
                "status": status,
                "error": "watch_timeout",
                "max_minutes": args.max_minutes,
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(json.dumps({"ok": False, "error": "request_error", "detail": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
