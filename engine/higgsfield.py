"""Higgsfield asset generation utility: private local key and explicit paid submit.

Usage: python -m engine.higgsfield --image-url https://... --prompt "..." --dry-run
       python -m engine.higgsfield --image-url https://... --prompt "..." --submit

No keys, signed URLs, authorization headers or input prompts are logged.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = "https://api.higgsfield.ai"
MODEL = "alibaba/wan-3.0/image-to-video"
KEY_PATH = Path.home() / ".config" / "synthosize" / "higgsfield.key"

def read_key():
    key = os.environ.get("HF_KEY") or (KEY_PATH.read_text().strip() if KEY_PATH.exists() else "")
    if not key or ":" not in key:
        raise RuntimeError("No Higgsfield key configured. Run ~/Developer/Synthosize/set-higgsfield-key.sh locally.")
    return key

def make_request(path, key, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": "Key " + key, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(API + path, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        # Do not print upstream bodies: they may include potentially sensitive data.
        raise RuntimeError("Higgsfield HTTP " + str(error.code) + ". Check key, balance and model parameters.") from None

def generate(image_url, prompt, duration=5, resolution="720p", submit=False):
    if not image_url.startswith("https://"):
        raise ValueError("An HTTPS image URL is required for image-to-video.")
    if duration < 2 or duration > 30:
        raise ValueError("Duration must be between 2 and 30 seconds.")
    payload = {
        "image_url": image_url,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": "9:16",
        "generate_audio": False,
        "enable_thinking": False,
    }
    if not submit:
        return {"dry_run": True, "model": MODEL, "input": payload, "note": "No charge; add --submit to generate."}
    response = make_request("/" + MODEL, read_key(), payload)
    return {"submitted": True, "request_id": response.get("request_id"), "status_url": response.get("status_url")}

def check_status(request_id):
    # Avoid accepting arbitrary URLs from the service as request destinations.
    if not request_id or not all(ch.isalnum() or ch in "-_" for ch in request_id):
        raise ValueError("Invalid request id")
    response = make_request("/requests/" + request_id + "/status", read_key())
    return {"request_id": request_id, "status": response.get("status"), "video_url": (response.get("video") or {}).get("url") if isinstance(response.get("video"), dict) else None}

def main():
    parser = argparse.ArgumentParser(description="Generate optional AI character loops for Synthosize.")
    parser.add_argument("--image-url")
    parser.add_argument("--prompt")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--resolution", choices=("480p", "720p", "1080p"), default="720p")
    parser.add_argument("--submit", action="store_true", help="Explicitly authorize a paid video generation")
    parser.add_argument("--dry-run", action="store_true", help="Preview a request without submitting (default)")
    parser.add_argument("--status", help="Check a request without starting another generation")
    args = parser.parse_args()
    if args.dry_run and args.submit:
        parser.error("--dry-run and --submit cannot be combined")
    if args.status:
        result = check_status(args.status)
    else:
        if not args.image_url or not args.prompt:
            parser.error("--image-url and --prompt are required for generating videos")
        result = generate(args.image_url, args.prompt, args.duration, args.resolution, args.submit)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
