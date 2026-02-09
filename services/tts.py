import re
import requests
import uuid
import asyncio
import discord
import os
from services.logger import logger

VOICEVOX_URL = "http://127.0.0.1:50021"

def sanitize_text(text: str) -> str:
  text = re.sub(r'https?://\S+', '', text)
  text = re.sub(r'<@!?\\d+>', '', text)
  text = re.sub(r'<#\\d+>', '', text)
  text = re.sub(r'<:.+?:\\d+>', '', text)
  return text.strip()[:200]

def synthesize(text: str, speaker: int) -> str:
  query = requests.post(
    f"{VOICEVOX_URL}/audio_query",
    params={"text": text, "speaker": speaker}
  ).json
  
  audio = requests.post(
    f"{VOICEVOX_URL}/synthesis",
    params={"speaker": speaker},
    json=query
  )
  
  filename = f"tts_{uuid.uuid4()}.wav"
  with open(filename, "wb") as f:
    f.write(audio.content)
    
  return filename

async def tts_worker(bot, guild_id: int):
    queue = bot.tts_queues[guild_id]
    guild = bot.get_guild(guild_id)

    while True:
        try:
            text, speaker = await queue.get()

            vc = guild.voice_client
            if not vc or not vc.is_connected():
                break

            path = synthesize(text, speaker)
            vc.play(discord.FFmpegPCMAudio(path))

            while vc.is_playing():
                await asyncio.sleep(0.3)

            os.remove(path)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            queue.task_done()
