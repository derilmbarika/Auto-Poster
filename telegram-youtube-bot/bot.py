#!/usr/bin/env python3
"""Telegram bot that downloads YouTube videos with yt-dlp and sends them back.

Send the bot a YouTube link and it will fetch the video, pick a quality that
fits inside Telegram's upload limit, and deliver the file (or an audio-only
MP3 if you ask for it).

Config comes from environment variables (see .env.example):
  TELEGRAM_BOT_TOKEN   (required)  BotFather token
  MAX_UPLOAD_MB        (optional)  upload cap in MB; default 50 (plain Bot API)
  DOWNLOAD_DIR         (optional)  scratch dir for downloads; default a temp dir
  ALLOWED_USER_IDS     (optional)  comma-separated Telegram user IDs allowed to
                                   use the bot; empty means everyone
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path

import yt_dlp

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("yt-telegram-bot")

# --- config -----------------------------------------------------------------

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", tempfile.gettempdir())) / "yt-telegram-bot"
ALLOWED_USER_IDS = {
    int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x
}

MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

YOUTUBE_RE = re.compile(
    r"https?://(?:www\.|m\.|music\.)?"
    r"(?:youtube\.com/(?:watch\?[^\s]*v=|shorts/|live/|embed/)|youtu\.be/)"
    r"[\w\-]+[^\s]*",
    re.IGNORECASE,
)


def is_allowed(update: Update) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    user = update.effective_user
    return bool(user and user.id in ALLOWED_USER_IDS)


def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_RE.search(text or "")
    return match.group(0) if match else None


# --- yt-dlp (runs in a thread so it never blocks the event loop) -------------


def _download(url: str, workdir: Path, audio_only: bool) -> tuple[Path, str]:
    """Download the video/audio and return (file_path, title). Blocking."""
    outtmpl = str(workdir / "%(id)s.%(ext)s")

    if audio_only:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    else:
        # Prefer progressively smaller renditions that fit the upload cap.
        # yt-dlp's filesize filters keep us under the Telegram limit when the
        # metadata reports a size; the height ladder is a fallback for streams
        # that don't advertise one.
        cap = MAX_UPLOAD_BYTES
        ydl_opts = {
            "format": (
                f"best[filesize<{cap}][ext=mp4]/"
                f"best[filesize<{cap}]/"
                "best[height<=720][ext=mp4]/best[height<=720]/"
                "best[height<=480][ext=mp4]/best[height<=480]/best"
            ),
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "video")
        filename = Path(ydl.prepare_filename(info))
        if audio_only:
            filename = filename.with_suffix(".mp3")

    if not filename.exists():
        # Postprocessing or merging may change the extension; grab whatever landed.
        produced = sorted(workdir.glob(f"{info.get('id', '*')}.*"))
        if produced:
            filename = produced[0]
        else:
            raise FileNotFoundError("yt-dlp did not produce an output file")

    return filename, title


# --- handlers ----------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return
    await update.message.reply_text(
        "🎬 *YouTube Downloader*\n\n"
        "Send me a YouTube link and I'll download it for you.\n\n"
        "• Just paste a link to get the video\n"
        "• Add the word *audio* to get an MP3 instead\n\n"
        f"Uploads are capped at {MAX_UPLOAD_MB} MB (Telegram's bot limit). "
        "If a video is larger I'll grab the best quality that fits.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    text = update.message.text or ""
    url = extract_youtube_url(text)
    if not url:
        await update.message.reply_text(
            "That doesn't look like a YouTube link. Send me a youtube.com or youtu.be URL."
        )
        return

    audio_only = "audio" in text.lower()
    status = await update.message.reply_text(
        "⏳ Downloading… this can take a moment for longer videos."
    )

    workdir = DOWNLOAD_DIR / uuid.uuid4().hex
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        await context.bot.send_chat_action(
            update.effective_chat.id, ChatAction.RECORD_VOICE if audio_only else ChatAction.UPLOAD_VIDEO
        )
        file_path, title = await asyncio.to_thread(_download, url, workdir, audio_only)

        size = file_path.stat().st_size
        if size > MAX_UPLOAD_BYTES:
            await status.edit_text(
                f"⚠️ The smallest available version is {size / 1024 / 1024:.1f} MB, "
                f"which is over the {MAX_UPLOAD_MB} MB upload limit. "
                "Try the *audio* option, or a shorter video.",
                parse_mode="Markdown",
            )
            return

        await status.edit_text("📤 Uploading to Telegram…")
        await context.bot.send_chat_action(
            update.effective_chat.id, ChatAction.UPLOAD_VIDEO
        )

        with file_path.open("rb") as fh:
            if audio_only:
                await update.message.reply_audio(
                    audio=fh, title=title, caption=f"🎵 {title}", read_timeout=300, write_timeout=300
                )
            else:
                await update.message.reply_video(
                    video=fh,
                    caption=f"🎬 {title}",
                    supports_streaming=True,
                    read_timeout=300,
                    write_timeout=300,
                )
        await status.delete()

    except yt_dlp.utils.DownloadError as exc:
        logger.warning("Download failed for %s: %s", url, exc)
        await status.edit_text(
            "❌ Couldn't download that video. It may be private, age-restricted, "
            "region-locked, or removed."
        )
    except Exception:  # noqa: BLE001 - surface a friendly message, log the detail
        logger.exception("Unexpected error handling %s", url)
        await status.edit_text("❌ Something went wrong. Please try again.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env, add your "
            "BotFather token, and export it (or use a tool like python-dotenv)."
        )

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started. Upload cap: %s MB", MAX_UPLOAD_MB)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
