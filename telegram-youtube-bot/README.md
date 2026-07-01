# Telegram YouTube Downloader Bot

A small Telegram bot that downloads YouTube videos with
[`yt-dlp`](https://github.com/yt-dlp/yt-dlp) and sends them back to the chat.
Send it a link, get the video. Add the word **audio** to get an MP3 instead.

## Features

- Paste any `youtube.com` / `youtu.be` link (watch, Shorts, live, embed, music).
- Automatically picks the best quality that fits Telegram's upload limit.
- Audio-only (MP3) mode — just include the word `audio` in your message.
- Optional allowlist so only specific Telegram users can use the bot.
- Downloads run in a worker thread, so the bot stays responsive.

## Requirements

- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) on your `PATH` (yt-dlp uses it to merge
  video/audio streams and to extract MP3s).

## Setup

```bash
cd telegram-youtube-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your BotFather token into TELEGRAM_BOT_TOKEN
```

Create a bot and get the token from [@BotFather](https://t.me/BotFather) with
`/newbot`.

## Run

```bash
python3 bot.py
```

Then open Telegram, find your bot, and send it a YouTube link.

## Configuration

All configuration is via environment variables (loaded from `.env` if present):

| Variable             | Required | Default    | Description                                               |
| -------------------- | -------- | ---------- | --------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | yes      | —          | BotFather token.                                          |
| `MAX_UPLOAD_MB`      | no       | `50`       | Upload cap. Plain Bot API allows 50 MB.                   |
| `DOWNLOAD_DIR`       | no       | temp dir   | Scratch directory for downloads (cleaned after each job). |
| `ALLOWED_USER_IDS`   | no       | (everyone) | Comma-separated Telegram user IDs allowed to use the bot. |

## Notes on the 50 MB limit

The standard Telegram Bot API caps bot uploads at **50 MB**. If you need larger
files, run a [local Bot API server](https://github.com/tdlib/telegram-bot-api)
(allows up to 2 GB) and set `MAX_UPLOAD_MB=2000`. When a video can't be shrunk
below the cap, the bot tells you and suggests the `audio` option.

## Legal

Only download content you have the right to. Respect YouTube's Terms of Service
and applicable copyright law.
