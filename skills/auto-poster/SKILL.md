---
name: auto-poster
description: "Post or schedule a provided video OR a nexchrono.com product page directly through Zernio. Video input: local path or public URL (whisper.cpp caption if none given). Product input: any nexchrono.com/product/ URL — scrape, draft caption in the house style, post all images to Instagram + Facebook. Triggers: post this video, post /path/to/video.mp4, schedule this video, queue this video, publish reel, post to instagram, post to zernio, any nexchrono.com product link."
---

# Auto Poster

Take the video Jason gives you and post it through Zernio.

This skill does one job with one optional prep step:

`provided video -> optional whisper.cpp caption -> Zernio`

Zernio posting should feel like:

```js
await fetch("https://zernio.com/api/v1/posts", {
  method: "POST",
  headers: { Authorization: `Bearer ${ZERNIO_API_KEY}` },
  body: JSON.stringify({
    content: "Caption goes here",
    platforms: [{ platform: "instagram", accountId: "..." }],
    mediaItems: [{ type: "video", url: "https://example.com/demo.mp4" }],
    publishNow: true
  })
});
```

Zernio's public examples sometimes show the shorthand shape `text`, `platforms`, and `mediaUrls`. The helper script uses the documented OpenAPI shape: `content`, `mediaItems`, and platform targets with account IDs.

## What This Skill Does Not Do

- Does not search Notion.
- Does not download from Frame.io or Google Drive.
- Does not update pipeline status.
- Does not run the full content production chain.

If the user wants those steps, use the relevant upstream skill first, then come back here with the final video file.

## Inputs

Required:

- Local video path, e.g. `/Users/jason/.../final.mp4`
- Or a public direct video URL, e.g. `https://.../video.mp4`

Optional:

- Caption text or caption file.
- If no caption is provided, generate one from a whisper.cpp transcript.
- Platforms: default `instagram,tiktok,youtube`.
- Mode: default `shareNow`.
- Schedule time for `customScheduled`.
- YouTube title. Default is the filename or caption first line.

## Prerequisites

`.env` (in the project root) only needs `ZERNIO_API_KEY`. If any of `ZERNIO_ACCOUNT_INSTAGRAM`, `ZERNIO_ACCOUNT_TIKTOK`, `ZERNIO_ACCOUNT_YOUTUBE`, `ZERNIO_ACCOUNT_FACEBOOK`, or `ZERNIO_PROFILE_ID` are missing or blank, fetch them yourself with `GET https://zernio.com/api/v1/accounts` (bearer auth with the API key). The response is `{ accounts: [{ _id, platform, displayName, profileId: { _id, name }, ... }] }`. Write the discovered IDs back to `.env` so the next run doesn't repeat the lookup.

Aliases `ZERNIO_ACCOUNT_ID_<PLATFORM>` are also accepted.

Optional `.env` keys: `ZERNIO_API_URL`, `ZERNIO_QUEUE_ID`, `ZERNIO_TIMEZONE`. `ZERNIO_PROFILE_ID` is required only for `addToQueue`.

System tools used by the helpers: `python3`, `ffmpeg`, `curl`, `git`, `make`, `gcc`. The transcriber will `pip install cmake` on first run if it's missing.

## Fast Path

Use the helper script:

```bash
python3 scripts/post_to_zernio.py \
  "/absolute/path/to/video.mp4" \
  --caption-file "$CAPTION_FILE" \
  --platforms instagram,tiktok,youtube \
  --mode shareNow
```

Where `$CAPTION_FILE` is a path you created in this session — not a hardcoded shared path. See "Temp files" below.

For a public video URL:

```bash
python3 scripts/post_to_zernio.py \
  "https://example.com/video.mp4" \
  --caption "Caption goes here" \
  --platforms instagram,tiktok \
  --mode addToQueue
```

If Jason did not provide a caption, run the transcriber and capture the path it prints to stdout. Invoke it via `bash` so it works even if the file's executable bit was lost on checkout:

```bash
TRANSCRIPT_FILE=$(bash scripts/transcribe_for_caption.sh "/absolute/path/to/video.mp4")
```

Then read `$TRANSCRIPT_FILE`, write a caption to a path you control, and pass that to `--caption-file`.

For a scheduled post:

```bash
python3 scripts/post_to_zernio.py \
  "/absolute/path/to/video.mp4" \
  --caption-file "$CAPTION_FILE" \
  --mode customScheduled \
  --due-at "2026-05-18T12:00:00" \
  --timezone "America/Chicago"
```

For a draft:

```bash
python3 scripts/post_to_zernio.py \
  "/absolute/path/to/video.mp4" \
  --caption-file "$CAPTION_FILE" \
  --mode draft
```

## Product Link Mode (nexchrono.com)

When the user drops a `nexchrono.com/product/...` URL (with or without instructions), run the full pipeline end to end — no questions needed beyond first-post caption approval:

1. Extract product data:
   ```bash
   python3 scripts/post_product.py extract "<product_url>"
   ```
   Returns JSON: `title`, `price`, `description`, `images` (gallery URLs, logos filtered out).
2. Draft the caption in the house style (see template below) from the extracted data. Save it to a session-scoped temp file.
3. On the FIRST product post of a session, show the caption and wait for approval. After that, post subsequent links without asking unless something is ambiguous.
4. Post:
   ```bash
   python3 scripts/post_product.py post "<product_url>" \
     --caption-file "$CAPTION_FILE" \
     --platforms instagram,facebook \
     --mode shareNow
   ```
   The script handles everything per platform: Facebook gets the original image URLs (max 11); Instagram gets the first 10 images downloaded, converted WebP→JPG, center-cropped to max 4:5 (Instagram rejects WebP and ratios taller than 4:5), uploaded via Zernio presign.
5. Report post IDs, statuses, and live platform URLs.

`--mode` supports the same four modes as video posting (`shareNow`, `addToQueue`, `customScheduled` + `--due-at`, `draft`).

### Product Caption Template (house style)

```
💵 {PRICE} — {TITLE}

Brand new & unworn | Full set | {YEAR} warranty card   ← adapt to actual condition/included items

⌚ {size + materials}
📿 {bracelet + sizing}
🟢 {dial}
📋 {box/papers/warranty — only what the listing actually states}

DM us to purchase.
Trades welcome. Appraisal included.

📞 +1(854) 410-7388
📧 info@nexchrono.com

#Rolex #{Model} #{ModelVariant} #{RefNumber} #LuxuryWatches #RolexDealer #RolexForSale #WatchDealer #WatchCollector #Watches #NexChrono
```

Rules: price + title always on line 1. Do NOT put the product URL in the caption — links aren't clickable on Instagram. The script automatically appends `👉 {PRODUCT_URL}` as the last line of the Facebook caption only (suppress with `--no-link`). Pull specs only from the actual listing — never invent condition, warranty, or included items. Mirror the listing's transparency (e.g. "NO WARRANTY CARD" if the listing says so). ~15 hashtags, model-specific ones swapped per watch.

## Transcription (whisper.cpp)

`scripts/transcribe_for_caption.sh` uses whisper.cpp with the `ggml-tiny.en` model by default. This was chosen after testing:

- `tiny.en` is ~75 MB and transcribes a 90-second video in ~2 seconds on CPU.
- `faster-whisper` + `onnxruntime` + `av` need ~3 GB of disk just for deps, which doesn't fit in some sandboxed environments. Avoid it unless you've confirmed disk headroom.
- The script ffmpeg-extracts 16 kHz mono audio first so whisper.cpp processes a few MB instead of hundreds.

Override the model with `AUTO_POSTER_WHISPER_MODEL=base.en` (or `small.en`) if you want more quality; expect ~150 MB / ~500 MB and a few seconds longer per run.

The whisper.cpp build and downloaded models are cached at `~/.cache/auto-poster/whisper.cpp/`. First run takes 3–5 minutes (clone + build + model download). Every run after that reuses the cache and finishes in seconds. Override the cache location with `AUTO_POSTER_WHISPER_DIR`.

## Temp files

When you write a caption file for `--caption-file`, use a path you create yourself (e.g. the agent's outputs directory or `"$(mktemp -t auto-poster-caption.XXXXXXXX)"`) rather than a hardcoded shared path. `transcribe_for_caption.sh` already does this and prints the path on stdout — just read whatever path it prints.

## Execution Rules

1. If the user did not provide a video path or URL, ask for the video.
2. If Jason provided a caption, use it.
3. If Jason did not provide a caption, run `transcribe_for_caption.sh`, generate a caption from the transcript, and save it to a session-scoped file you created.
4. If the video is a local file, run `post_to_zernio.py` with that path. The script uploads it through Zernio's presigned media upload flow.
5. If the video is already a public URL, pass it directly as the media URL.
6. Default to all configured platforms unless Jason names specific platforms.
7. For YouTube, set `--yt-title` if Jason provides one. Otherwise use the filename or first caption line.
8. Report Zernio post IDs, statuses, platform URLs, and errors. Do not mark any outside system as posted.
9. For `shareNow` on the first post of a session — or any post going to a real public account — show Jason the caption and confirm before publishing.

## Caption Rules

Generate the caption from the transcript, not from a generic template.

- If the transcript includes a real comment/DM CTA Jason said on camera, put that CTA on line 1 and repeat it at the end.
- If there is no spoken CTA, do not manufacture one. Use the strongest hook/take from the transcript and keep it casual.
- Keep it direct, conversational, and short enough for IG/TikTok.
- Use line breaks. Avoid numbered lists unless the video itself is clearly a numbered list.

## Supported Modes

- `shareNow`: sends `publishNow: true`.
- `addToQueue`: sends `queuedFromProfile`, using `ZERNIO_PROFILE_ID`.
- `customScheduled`: sends `scheduledFor` and `timezone`.
- `draft`: sends `isDraft: true`.

For `customScheduled`, `--due-at` is required.

## Platform Metadata

The script sends:

- Caption as top-level `content`.
- Video as `mediaItems: [{ type: "video", url }]`.
- Platforms as `{ platform, accountId }` targets from `.env`.
- YouTube title as top-level `title` when posting to YouTube.

## Notes

- Zernio API base URL is `https://zernio.com/api/v1`.
- Zernio uses bearer auth with `ZERNIO_API_KEY`.
- Local files are uploaded via `POST /v1/media/presign`, then `PUT` to the returned upload URL, then posted with the returned `publicUrl`.
- The helper sends a fresh `x-request-id` for each post create call.
- Zernio also has a shorthand examples style using `text`, platform names, and `mediaUrls`; use the helper unless Jason explicitly asks for the raw shorthand payload.
