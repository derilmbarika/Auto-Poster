#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse


ZERNIO_URL = "https://zernio.com/api/v1"


def load_env(path):
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def is_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def run(cmd, timeout=120):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return result.stdout.strip()


def curl_json(method, url, api_key=None, payload=None, headers=None, timeout=120):
    cmd = ["curl", "-sS", "-X", method, url]
    if api_key:
        cmd.extend(["-H", f"Authorization: Bearer {api_key}"])
    for header in headers or []:
        cmd.extend(["-H", header])
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload)])

    stdout = run(cmd, timeout=timeout)
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Zernio returned non-JSON response: {stdout[:500]}") from exc


def guess_content_type(path):
    guessed, _ = mimetypes.guess_type(str(path))
    suffix = path.suffix.lower()
    overrides = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".m4v": "video/x-m4v",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
    }
    return overrides.get(suffix, guessed or "video/mp4")


def verify_url(url):
    try:
        headers = run(["curl", "-sI", url], timeout=20)
    except Exception as exc:
        raise RuntimeError(f"Could not verify media URL: {exc}") from exc

    lowered = headers.lower()
    if "404" in lowered or "403" in lowered:
        raise RuntimeError(f"Media URL is not reachable: {url}")


def zernio_base_url():
    return os.environ.get("ZERNIO_API_URL", ZERNIO_URL).rstrip("/")


def upload_to_zernio(api_key, video_path):
    path = Path(video_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")
    if not path.is_file():
        raise ValueError(f"Video path is not a file: {path}")

    content_type = guess_content_type(path)
    presign = curl_json(
        "POST",
        f"{zernio_base_url()}/media/presign",
        api_key=api_key,
        payload={
            "filename": path.name,
            "contentType": content_type,
            "size": path.stat().st_size,
        },
        timeout=90,
    )
    if presign.get("error"):
        raise RuntimeError(f"Zernio presign failed: {presign}")

    upload_url = presign.get("uploadUrl")
    public_url = presign.get("publicUrl")
    if not upload_url or not public_url:
        raise RuntimeError(f"Zernio presign response missing uploadUrl/publicUrl: {presign}")

    run(
        [
            "curl",
            "-sS",
            "-X",
            "PUT",
            upload_url,
            "-H",
            f"Content-Type: {content_type}",
            "--data-binary",
            f"@{path}",
        ],
        timeout=900,
    )
    return public_url


def caption_from_args(args):
    if args.caption_file:
        return Path(args.caption_file).expanduser().read_text().strip()
    return (args.caption or "").strip()


def yt_title_from_args(args, source, caption):
    if args.yt_title:
        return args.yt_title.strip()
    if caption:
        return caption.splitlines()[0][:95].strip()
    if is_url(source):
        name = Path(urlparse(source).path).stem
        return name or "Video"
    return Path(source).stem or "Video"


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def optional_env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def parse_platforms(value):
    platforms = [p.strip().lower() for p in value.split(",") if p.strip()]
    aliases = {"x": "twitter", "twitter/x": "twitter"}
    platforms = [aliases.get(platform, platform) for platform in platforms]
    allowed = {
        "instagram",
        "tiktok",
        "youtube",
        "twitter",
        "linkedin",
        "facebook",
        "threads",
        "pinterest",
        "reddit",
        "bluesky",
    }
    invalid = sorted(set(platforms) - allowed)
    if invalid:
        raise ValueError(f"Unsupported platform(s): {', '.join(invalid)}")
    return platforms


def account_id_for(platform):
    normalized = platform.upper().replace("-", "_")
    return optional_env(
        f"ZERNIO_ACCOUNT_{normalized}",
        f"ZERNIO_ACCOUNT_ID_{normalized}",
    )


def platform_targets(platforms, require_accounts):
    targets = []
    missing = []
    for platform in platforms:
        account_id = account_id_for(platform)
        target = {"platform": platform}
        if account_id:
            target["accountId"] = account_id
        elif require_accounts:
            missing.append(f"ZERNIO_ACCOUNT_{platform.upper()}")
        targets.append(target)
    if missing:
        raise RuntimeError("Missing required env var(s): " + ", ".join(missing))
    return targets


def media_item(media_url):
    path = Path(urlparse(media_url).path)
    guessed = guess_content_type(path)
    media_type = "image" if guessed.startswith("image/") else "video"
    return {"type": media_type, "url": media_url}


def build_payload(args, platforms, media_url, caption, title):
    require_accounts = not args.allow_default_accounts
    payload = {
        "content": caption,
        "mediaItems": [media_item(media_url)],
        "platforms": platform_targets(platforms, require_accounts),
        "timezone": args.timezone,
    }

    if "youtube" in platforms and title:
        payload["title"] = title[:100]

    if args.mode == "shareNow":
        payload["publishNow"] = True
    elif args.mode == "customScheduled":
        payload["scheduledFor"] = args.due_at
    elif args.mode == "addToQueue":
        payload["queuedFromProfile"] = require_env("ZERNIO_PROFILE_ID")
        queue_id = optional_env("ZERNIO_QUEUE_ID")
        if queue_id:
            payload["queueId"] = queue_id
    elif args.mode == "draft":
        payload["isDraft"] = True

    return payload


def create_post(api_key, payload):
    return curl_json(
        "POST",
        f"{zernio_base_url()}/posts",
        api_key=api_key,
        payload=payload,
        headers=[f"x-request-id: {uuid.uuid4()}"],
        timeout=120,
    )


def summarize_response(response):
    post = response.get("post") or response.get("data", {}).get("post") or {}
    if not post:
        return response
    return {
        "post_id": post.get("_id") or post.get("id"),
        "status": post.get("status"),
        "scheduled_for": post.get("scheduledFor"),
        "platforms": [
            {
                "platform": platform.get("platform"),
                "status": platform.get("status"),
                "platform_post_url": platform.get("platformPostUrl"),
                "error": platform.get("error"),
            }
            for platform in post.get("platforms", [])
        ],
        "message": response.get("message"),
    }


def main():
    parser = argparse.ArgumentParser(description="Post a provided video directly to Zernio.")
    parser.add_argument("video", help="Local video path or public video URL")
    parser.add_argument("--caption", default="", help="Caption text")
    parser.add_argument("--caption-file", help="Path to a caption text file")
    parser.add_argument("--platforms", default="instagram,tiktok,youtube")
    parser.add_argument(
        "--mode",
        default="shareNow",
        choices=["shareNow", "addToQueue", "customScheduled", "draft"],
    )
    parser.add_argument("--due-at", help="ISO time for customScheduled mode")
    parser.add_argument("--timezone", default=os.environ.get("ZERNIO_TIMEZONE", "America/Chicago"))
    parser.add_argument("--yt-title", help="YouTube title")
    parser.add_argument("--allow-default-accounts", action="store_true", help="Send platform names without explicit account IDs")
    parser.add_argument("--dry-run", action="store_true", help="Print the Zernio payload without posting")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()

    load_env(args.env_file)

    if args.mode == "customScheduled" and not args.due_at:
        raise RuntimeError("--due-at is required when --mode customScheduled")

    api_key = require_env("ZERNIO_API_KEY")
    platforms = parse_platforms(args.platforms)
    caption = caption_from_args(args)
    title = yt_title_from_args(args, args.video, caption)

    media_url = args.video if is_url(args.video) else upload_to_zernio(api_key, args.video)
    verify_url(media_url)

    payload = build_payload(args, platforms, media_url, caption, title)
    if args.dry_run:
        print(json.dumps({"media_url": media_url, "payload": payload}, indent=2))
        return

    response = create_post(api_key, payload)
    if response.get("error"):
        print(json.dumps({"media_url": media_url, "error": response}, indent=2))
        sys.exit(1)

    print(
        json.dumps(
            {
                "media_url": media_url,
                "mode": args.mode,
                "platforms": platforms,
                "result": summarize_response(response),
                "raw": response,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
