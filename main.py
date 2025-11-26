import os
import asyncio
from telethon import TelegramClient, events

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE_NUMBER")
RTMP_URL = os.getenv("RTMP_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = TelegramClient("railway_user", API_ID, API_HASH)
playlist = []


def is_video(msg):
    if msg.video:
        return True
    if msg.document and msg.document.mime_type:
        return msg.document.mime_type.startswith("video/")
    return False


async def load_initial():
    print("📂 Loading channel history...")
    async for msg in client.iter_messages(CHANNEL_ID, limit=50):
        if is_video(msg):
            playlist.append((CHANNEL_ID, msg.id))
    playlist.reverse()
    print(f"✅ Loaded {len(playlist)} videos.")


@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    msg = event.message
    if is_video(msg):
        playlist.append((CHANNEL_ID, msg.id))
        print(f"➕ New upload: {msg.id}")


async def stream_loop():
    await load_initial()

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

            cmd = [
                "ffmpeg", "-re", "-i", file, "-vcodec", "libx264",
                "-preset", "veryfast", "-maxrate", "2500k",
                "-bufsize", "5000k", "-acodec", "aac",
                "-ar", "44100", "-b:a", "128k",
                "-f", "flv", RTMP_URL
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            while True:
                line = await proc.stdout.readline()
                if not line:
                    break

            await proc.wait()

            playlist.append((chat, mid))
            os.remove(file)

        except Exception as e:
            print(f"❌ Streaming error: {e}")
            playlist.append((chat, mid))
            await asyncio.sleep(5)


async def main():
    print("📱 Logging in...")
    await client.start(phone=PHONE)
    print("🤖 User logged in!")
    print("📺 Starting loop...")
    client.loop.create_task(stream_loop())
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
