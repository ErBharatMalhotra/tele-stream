import os
import asyncio
import subprocess

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # <-- MOST IMPORTANT
RTMP_URL = os.getenv("RTMP_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

if not all([API_ID, API_HASH, SESSION_STRING, RTMP_URL, CHANNEL_ID]):
    raise RuntimeError("⚠️ Missing environment variables!")

# User session (NO phone login)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

playlist = []

def is_video(msg):
    """Check if message contains a video."""
    if msg.video:
        return True
    if msg.document and msg.document.mime_type:
        return msg.document.mime_type.startswith("video/")
    return False

async def load_initial():
    print("📂 Loading channel history...")

    async for msg in client.iter_messages(CHANNEL_ID, limit=200):
        if is_video(msg):
            playlist.append((CHANNEL_ID, msg.id))

    playlist.reverse()
    print(f"✅ Loaded {len(playlist)} videos into playlist.")

@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    msg = event.message
    if is_video(msg):
        playlist.append((CHANNEL_ID, msg.id))
        print(f"➕ New video added: {msg.id} | Total {len(playlist)}")

async def stream_loop():

    while True:
        if not playlist:
            print("⏳ Waiting for videos...")
            await asyncio.sleep(5)
            continue

        chat, mid = playlist.pop(0)

        try:
            msg = await client.get_messages(chat, ids=mid)
            file = await msg.download_media()
            print(f"📥 Downloaded: {file}")

            print("📡 Starting livestream...")
            cmd = [
                "ffmpeg", "-re", "-i", file, "-vcodec", "libx264", "-preset", "veryfast",
                "-maxrate", "3000k", "-bufsize", "6000k", "-acodec", "aac",
                "-ar", "44100", "-b:a", "128k", "-f", "flv", RTMP_URL
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            while True:
                l = await proc.stdout.readline()
                if not l:
                    break

            await proc.wait()

            # re-add video for loop playback
            playlist.append((chat, mid))

            try:
                os.remove(file)
            except:
                pass

        except Exception as e:
            print("❌ Error:", e)
            playlist.append((chat, mid))
            await asyncio.sleep(5)


async def main():
    print("📱 Starting user session...")

    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Invalid SESSION STRING")
        return

    print("🤖 User logged in successfully!")
    print("📺 Streaming system ready.")

    await load_initial()
    asyncio.create_task(stream_loop())
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
