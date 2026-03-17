---
name: seedance-2-video-generator
displayName: Seedance 2.0 Video Generator
description: Generates video via Loova Seedance 2.0 API (img2vid). Requires LOOVA_API_KEY from .env or environment (get API key at loova.ai). Use when the user asks for Loova, Seedance 2.0, image-to-video, or img2vid.
---

# Seedance 2.0 Video Generator

Generate AI videos from text prompts or images using the Loova Seedance 2.0 API (img2vid). Submit a job, poll for completion, and get the video result.

## Capabilities

1. **Image/Text to Video** – Loova img2vid API with Seedance 2.0 or Seedance 2.0 Fast
2. **Prompt-driven** – Supports @ reference syntax and optional media files as FormData (File uploads; works with OpenClaw image/video/audio uploads)
3. **Configurable** – Duration (4–15s), aspect ratio, function mode (first/last frame or omni reference)

## Quick Start

```bash
# Generate video from prompt only
python scripts/run_seedance.py --prompt "Camera slowly pushes in, person smiles"

# With local file(s) (sent as FormData File uploads)
python scripts/run_seedance.py --prompt "Person turns head" --files "photo.jpg" --duration 8

# Fast model, custom ratio
python scripts/run_seedance.py --prompt "A cat in the sun" --model jimeng-video-seedance-2.0-fast --ratio "16:9"
```

## Setup

### Required API Key

Obtain your API key after logging in at [https://loova.ai/](https://loova.ai/) (e.g. from browser DevTools: Network or Local Storage).

Add to your environment or `.env` file in the project root:

```bash
# Required for Loova API
LOOVA_API_KEY=your_api_key_here
```

Create `.env` from the example:

```bash
cp .env.example .env
# Edit .env and set LOOVA_API_KEY
```

The script loads variables from `.env` automatically (via `python-dotenv`). You can also export `LOOVA_API_KEY` in your shell.

### Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `requests`, `python-dotenv`. No FFmpeg or other system binaries required.

## Usage Examples

### 1. Text to Video (prompt only)

```bash
python scripts/run_seedance.py --prompt "A futuristic city at night with flying cars" --duration 5
```

### 2. Image to Video (with reference image URL)

```bash
python scripts/run_seedance.py --prompt "Person slowly smiles" --files "https://your-cdn.com/portrait.jpg" --duration 8
```

### 3. Multiple Reference Images

```bash
python scripts/run_seedance.py --prompt "Smooth transition between scenes" --files "https://example.com/a.jpg,https://example.com/b.jpg" --function-mode first_last_frames
```

### 4. Fast Model, Custom Aspect Ratio

```bash
python scripts/run_seedance.py --prompt "Ocean waves" --model jimeng-video-seedance-2.0-fast --ratio "9:16" --duration 6
```

## Scripts Reference

| Script | Description |
|--------|-------------|
| `scripts/run_seedance.py` | Submit img2vid task and poll until done; prints result JSON (includes video URL on success) |

Arguments: `--prompt` (required), `--model`, `--duration`, `--ratio`, `--function-mode`, `--files` (comma-separated local paths; sent as multipart File uploads).

## API Flow

1. **Submit** – `POST https://api.loova.ai/v1/img2vid` with `Authorization: Bearer <API_KEY>`; response contains `task_id`.
2. **Poll** – `GET https://api.loova.ai/v1/video_item?task_id=<task_id>` every few seconds until status is succeeded or failed.
3. **Result** – Response includes the video result (e.g. URL). Script prints full JSON.

## Parameters Summary

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `model` | Yes | `jimeng-video-seedance-2.0` | `jimeng-video-seedance-2.0` or `jimeng-video-seedance-2.0-fast` |
| `params.prompt` | Yes | — | Prompt; supports @ reference syntax |
| `params.functionMode` | No | — | `first_last_frames` or `omni_reference` |
| (form) `files` | No | — | Multipart File parts (images/video/audio); sent as FormData |
| `params.ratio` | No | `16:9` | Aspect ratio |
| `params.duration` | No | `5` | Duration in seconds (4–15) |

For full API details, see [reference.md](reference.md). For a short setup guide, see [QUICK_START.md](QUICK_START.md).
