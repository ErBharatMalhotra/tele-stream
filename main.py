import os
import asyncio
import subprocess
from telethon.sessions import StringSession
from telethon import TelegramClient, events

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION_STRING")
RTMP_URL = os.getenv("RTMP_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
playlist = []


def is_video(msg):
    if msg.video:
        return True
    if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/"):
        return True
    return False


async def load_initial():
    print("📂 Loading channel history...")
    async for msg in client.iter_messages(CHANNEL_ID, limit=200):
        if is_video(msg):
            playlist.append((CHANNEL_ID, msg.id))

    playlist.reverse()
    print(f"✅ Loaded {len(playlist)} videos into playlist.")


@client.on(events.NewMessage(chats=CHANNEL_ID))
async def new_video(event):
    msg = event.message
    if is_video(msg):
        playlist.append((CHANNEL_ID, msg.id))
        print(f"➕ New video added: {msg.id}")


async def stream_loop():
    await load_initial()

    while True:
        if not playlist:
            print("⏳ Waiting for videos...")
            await asyncio.sleep(5)
            continue

        chat, msg_id = playlist.pop(0)

        try:
            msg = await client.get_messages(chat, ids=msg_id)
            file = await msg.download_media()
            print(f"📥 Downloaded: {file}")

            print("📡 Starting livestream...")
            cmd = [
                "ffmpeg", "-re", "-i", file,
                "-vcodec", "libx264", "-preset", "veryfast",
                "-acodec", "aac",
                "-f", "flv", RTMP_URL
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            await process.wait()
            print("✔ Stream ended")

            playlist.append((chat, msg_id))
            os.remove(file)

        except Exception as e:
            print("❌ STREAM ERROR:", e)
            playlist.append((chat, msg_id))
            await asyncio.sleep(5)


async def main():
    print("📱 Starting user session...")
    await client.start()
    print("🤖 Logged in")

    asyncio.create_task(stream_loop())
    await client.run_until_disconnected()


if __name__ == "__main__":
    print("🔥 Bot is starting...")
    client.loop.run_until_complete(main())
