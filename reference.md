# Loova img2vid API Reference

## Authentication

- Obtain your API key after logging in at [https://loova.ai/](https://loova.ai/).
- All requests must include the header: `Authorization: Bearer <API_KEY>`.

## 1. Submit Task: POST /v1/img2vid

- **URL**: `https://api.loova.ai/v1/img2vid`
- **Method**: POST
- **Headers**: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`
- **Body**: See table below.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | `jimeng-video-seedance-2.0` or `jimeng-video-seedance-2.0-fast` |
| `params` | object | Yes | Generation parameters |
| `params.prompt` | string | Yes | Prompt; supports @ reference syntax |
| `params.functionMode` | string | No | `first_last_frames` (first/last frame) / `omni_reference` (omni mode) |
| `params.file_paths` | array | No | List of media file URLs |
| `params.ratio` | string | No | Video aspect ratio, default `16:9` |
| `params.aspect_ratio` | string | No | Video aspect ratio (legacy), default `16:9` |
| `params.duration` | number/string | No | Duration in seconds, 4–15, default `5` |

**Response**: Contains `task_id` for polling the result.

## 2. Get Result: GET /v1/video_item

- **URL**: `https://api.loova.ai/v1/video_item?task_id=<task_id>`
- **Method**: GET
- **Headers**: `Authorization: Bearer <API_KEY>`
- **Usage**: Poll until the task status is completed or failed, then read the video result (e.g. URL) from the response.
