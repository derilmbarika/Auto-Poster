# Auto Poster

A template repo for a single-purpose Claude skill that posts a video to Zernio (Instagram, TikTok, YouTube, Facebook). Nothing else.

Pipeline: `provided video → optional whisper.cpp caption → Zernio`.

## Setup (one time)

1. Copy `.env.example` to `.env`.
2. Paste your Zernio API key into `ZERNIO_API_KEY`.
3. Done. On the next run, Claude will auto-discover your account IDs (and `ZERNIO_PROFILE_ID` for queueing) by calling `GET https://zernio.com/api/v1/accounts` with your key, and write them back to `.env`. No manual ID lookup.

If you'd rather fill IDs in by hand, every `ZERNIO_ACCOUNT_<PLATFORM>` line in `.env.example` is documented.

## Using it

Drop a video into the project folder (or anywhere Claude can read) and say what you want, e.g.:

- "Post `/path/to/video.mp4` to TikTok"
- "Schedule this video for Friday 9am on Instagram"
- "Queue this for all platforms"

Claude will transcribe the video if you didn't supply a caption, draft a caption from what's actually said on camera, show it to you for approval, then post via `post_to_zernio.py`.

## Layout

- `.env.example` — template for credentials. Copy to `.env`. Never commit `.env`.
- `.claude/skills/auto-poster/SKILL.md` — skill spec Claude follows. Source of truth for behavior.
- `.claude/skills/auto-poster/scripts/post_to_zernio.py` — uploads (if local) and creates the Zernio post.
- `.claude/skills/auto-poster/scripts/transcribe_for_caption.sh` — whisper.cpp transcription, used only when no caption is provided.

## Posting modes

- `shareNow` — publish immediately (`publishNow: true`)
- `addToQueue` — add to your Zernio queue (uses `ZERNIO_PROFILE_ID`)
- `customScheduled` — schedule for a specific time (`--due-at`)
- `draft` — save as draft (`isDraft: true`)

## Running the script directly

```bash
python3 .claude/skills/auto-poster/scripts/post_to_zernio.py \
  "/absolute/path/to/video.mp4" \
  --caption-file "$CAPTION_FILE" \
  --platforms tiktok \
  --mode shareNow
```

## Rules Claude follows

- Generate captions from the transcript, not a template. If there's a real CTA spoken on camera, put it on line 1 and repeat at the end. Don't invent a CTA.
- Before `shareNow` on the first post of a session, show the caption and confirm.
- This skill does NOT touch Notion, Frame.io, Google Drive, or any pipeline-status system. Use upstream skills for that, then come back here with the final file.

## System requirements

`python3`, `ffmpeg`, `curl`, `git`, `make`, `gcc`. whisper.cpp build + models cache at `~/.cache/auto-poster/whisper.cpp/` (override with `AUTO_POSTER_WHISPER_DIR`). Default model is `ggml-tiny.en`; override with `AUTO_POSTER_WHISPER_MODEL=base.en` or `small.en`.

## Zernio API notes

- Base URL: `https://zernio.com/api/v1`
- Bearer auth with `ZERNIO_API_KEY`
- Local files: `POST /media/presign` → `PUT` to returned URL → create post with returned `publicUrl`
- Payload uses the OpenAPI shape (`content`, `mediaItems`, `platforms` with `accountId`), not the shorthand (`text`, `mediaUrls`)
- Fresh `x-request-id` per post create call
- List accounts: `GET /accounts` returns `{ accounts: [{ _id, platform, displayName, profileId, ... }] }` — this is how Claude auto-fills `.env`
