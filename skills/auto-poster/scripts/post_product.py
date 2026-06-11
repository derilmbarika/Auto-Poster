#!/usr/bin/env python3
"""Post a nexchrono.com product page to Instagram + Facebook via Zernio.

Subcommands:
  extract <product_url>            Print product JSON (title, price, description, images)
  post    <product_url> [options]  Scrape, prep images, and publish

The Instagram pipeline converts WebP -> JPG and center-crops to a max 4:5
aspect ratio (Instagram rejects anything taller), then uploads the prepped
files through Zernio presign. Facebook gets the original image URLs as-is.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_env():
    for candidate in [Path.cwd() / ".env", SCRIPT_DIR.parents[3] / ".env"]:
        if candidate.exists():
            for raw in candidate.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
            return


def run(cmd, timeout=300):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip()[:500])
    return result.stdout


def curl_json(method, url, api_key=None, payload=None, headers=None, timeout=120):
    cmd = ["curl", "-sS", "-X", method, url]
    if api_key:
        cmd.extend(["-H", f"Authorization: Bearer {api_key}"])
    for header in headers or []:
        cmd.extend(["-H", header])
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload)])
    stdout = run(cmd, timeout=timeout)
    return json.loads(stdout)


def base_url():
    return os.environ.get("ZERNIO_API_URL", "https://zernio.com/api/v1").rstrip("/")


def extract_product(url):
    page = run(["curl", "-sSL", url], timeout=60)

    data = {"url": url, "title": None, "price": None, "description": None, "images": []}

    # JSON-LD product blocks carry the canonical title/price/description
    for block in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S):
        try:
            ld = json.loads(block)
        except json.JSONDecodeError:
            continue
        graphs = ld.get("@graph", [ld]) if isinstance(ld, dict) else ld
        for node in graphs:
            if isinstance(node, dict) and node.get("@type") in ("Product", ["Product"]):
                data["title"] = node.get("name") or data["title"]
                data["description"] = node.get("description") or data["description"]
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = offers.get("price") or offers.get("lowPrice")
                if price:
                    data["price"] = f"${float(price):,.2f}".rstrip("0").rstrip(".")

    if not data["title"]:
        m = re.search(r'<meta property="og:title" content="([^"]+)"', page)
        if m:
            data["title"] = html.unescape(m.group(1)).split(" - ")[0].strip()
    if not data["price"]:
        m = re.search(r'class="woocommerce-Price-amount[^>]*>.*?([\d,]+\.\d{2})', page, re.S)
        if m:
            data["price"] = f"${m.group(1)}"

    # Gallery images: full-size uploads referenced by the product gallery.
    # Skip site chrome (logos/icons live under cropped-* or carry WxH size suffixes).
    seen = []
    for m in re.findall(
        r'(?:data-large_image|href)="(https://nexchrono\.com/wp-content/uploads/[^"]+\.(?:webp|jpe?g|png))"',
        page,
    ):
        name = m.rsplit("/", 1)[-1].lower()
        if name.startswith("cropped-") or re.search(r"-\d+x\d+\.(?:png|jpe?g|webp)$", name):
            continue
        if m not in seen:
            seen.append(m)
    data["images"] = seen

    if data["title"]:
        data["title"] = re.sub(r"\s*-\s*Nexchrono\s*$", "", data["title"]).strip()

    # Description fallback: short-description block text
    if not data["description"]:
        m = re.search(
            r'<div class="woocommerce-product-details__short-description">(.*?)</div>', page, re.S
        )
        if m:
            text = re.sub(r"<[^>]+>", "\n", m.group(1))
            data["description"] = html.unescape(re.sub(r"\n{2,}", "\n", text)).strip()

    if not data["title"] or not data["images"]:
        raise RuntimeError(f"Could not extract product data from {url} (title={data['title']}, images={len(data['images'])})")
    return data


def prep_image_for_instagram(src_url, index, workdir):
    """Download, convert to JPG, center-crop to max 4:5. Returns local path."""
    raw = workdir / f"raw{index}"
    jpg = workdir / f"ig{index}.jpg"
    run(["curl", "-sS", "-o", str(raw), src_url], timeout=120)
    run(["sips", "-s", "format", "jpeg", str(raw), "--out", str(jpg)])
    info = run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(jpg)])
    w = int(re.search(r"pixelWidth: (\d+)", info).group(1))
    h = int(re.search(r"pixelHeight: (\d+)", info).group(1))
    max_h = w * 5 // 4
    if h > max_h:
        run(["sips", "-c", str(max_h), str(w), str(jpg)])
    return jpg


def upload_jpg(api_key, path, filename):
    presign = curl_json(
        "POST",
        f"{base_url()}/media/presign",
        api_key=api_key,
        payload={"filename": filename, "contentType": "image/jpeg", "size": path.stat().st_size},
    )
    upload_url, public_url = presign.get("uploadUrl"), presign.get("publicUrl")
    if not upload_url or not public_url:
        raise RuntimeError(f"presign failed: {presign}")
    run(["curl", "-sS", "-X", "PUT", upload_url, "-H", "Content-Type: image/jpeg",
         "--data-binary", f"@{path}"], timeout=600)
    return public_url


def create_post(api_key, caption, image_urls, platform, account_id, mode, due_at, timezone):
    payload = {
        "content": caption,
        "mediaItems": [{"type": "image", "url": u} for u in image_urls],
        "platforms": [{"platform": platform, "accountId": account_id}],
        "timezone": timezone,
    }
    if mode == "shareNow":
        payload["publishNow"] = True
    elif mode == "customScheduled":
        payload["scheduledFor"] = due_at
    elif mode == "addToQueue":
        payload["queuedFromProfile"] = os.environ["ZERNIO_PROFILE_ID"]
    elif mode == "draft":
        payload["isDraft"] = True
    return curl_json(
        "POST", f"{base_url()}/posts", api_key=api_key, payload=payload,
        headers=[f"x-request-id: {uuid.uuid4()}"],
    )


def summarize(response):
    post = response.get("post") or {}
    return {
        "error": response.get("error"),
        "post_id": post.get("_id"),
        "status": post.get("status"),
        "platforms": [
            {"platform": p.get("platform"), "status": p.get("status"),
             "url": p.get("platformPostUrl"), "error": p.get("error")}
            for p in post.get("platforms", [])
        ],
    }


def cmd_extract(args):
    print(json.dumps(extract_product(args.product_url), indent=2))


def cmd_post(args):
    api_key = os.environ.get("ZERNIO_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ZERNIO_API_KEY (set it in .env)")

    caption = Path(args.caption_file).expanduser().read_text().strip()
    product = extract_product(args.product_url)
    images = product["images"][: args.max_images]
    if not images:
        raise RuntimeError("No product images found")

    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    results = {}

    if "facebook" in platforms:
        fb_account = os.environ.get("ZERNIO_ACCOUNT_FACEBOOK")
        if not fb_account:
            raise RuntimeError("Missing ZERNIO_ACCOUNT_FACEBOOK")
        # Links are clickable on Facebook only, so the product URL goes there,
        # appended as the last line. Instagram gets the caption without it.
        fb_caption = caption if args.no_link else f"{caption}\n\n\U0001F449 {args.product_url}"
        results["facebook"] = summarize(create_post(
            api_key, fb_caption, images, "facebook", fb_account,
            args.mode, args.due_at, args.timezone))

    if "instagram" in platforms:
        ig_account = os.environ.get("ZERNIO_ACCOUNT_INSTAGRAM")
        if not ig_account:
            raise RuntimeError("Missing ZERNIO_ACCOUNT_INSTAGRAM")
        ig_images = images[:10]  # Instagram carousel cap
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            urls = []
            for i, src in enumerate(ig_images, 1):
                local = prep_image_for_instagram(src, i, workdir)
                urls.append(upload_jpg(api_key, local, f"product-ig-{uuid.uuid4().hex[:8]}-{i}.jpg"))
                print(f"prepped+uploaded image {i}/{len(ig_images)}", file=sys.stderr)
            results["instagram"] = summarize(create_post(
                api_key, caption, urls, "instagram", ig_account,
                args.mode, args.due_at, args.timezone))

    print(json.dumps(results, indent=2))
    if any(r.get("error") for r in results.values()):
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Print product data as JSON")
    p_extract.add_argument("product_url")
    p_extract.set_defaults(func=cmd_extract)

    p_post = sub.add_parser("post", help="Publish product to Instagram + Facebook")
    p_post.add_argument("product_url")
    p_post.add_argument("--caption-file", required=True)
    p_post.add_argument("--platforms", default="instagram,facebook")
    p_post.add_argument("--mode", default="shareNow",
                        choices=["shareNow", "addToQueue", "customScheduled", "draft"])
    p_post.add_argument("--due-at")
    p_post.add_argument("--max-images", type=int, default=11)
    p_post.add_argument("--no-link", action="store_true",
                        help="Don't append the product URL to the Facebook caption")
    p_post.add_argument("--timezone", default=os.environ.get("ZERNIO_TIMEZONE", "America/Chicago"))
    p_post.set_defaults(func=cmd_post)

    args = parser.parse_args()
    load_env()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
