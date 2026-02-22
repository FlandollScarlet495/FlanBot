import re
import pyopenjtalk
import soundfile as sf
import asyncio
import discord
import unicodedata
import numpy as np
import io
from .logger import logger

def sanitize_text(text: str, guild=None) -> str:
    # URL削除
    text = re.sub(r'https?://\S+', '', text)

    # メンション → 表示名（敬称付き）
    def repl_mention(match):
        if guild:
            uid = int(match.group(1))
            m = guild.get_member(uid)
            if m:
                return m.display_name + "さん"
            return ""
        return ""

    text = re.sub(r'<@!?(\d+)>', repl_mention, text)

    # チャンネルメンション削除
    text = re.sub(r'<#\d+>', '', text)

    # カスタムスタンプ <:name:id> 削除
    text = re.sub(r'<a?:\w+:\d+>', '', text)

    # Unicode絵文字削除（Symbol カテゴリ）
    text = ''.join(
        ch for ch in text
        if unicodedata.category(ch)[0] != 'S'
    )

    # OpenJTalkが嫌う記号・特殊文字を積極的に削除
    # 括弧、演算子、その他の記号
    text = re.sub(r'[\[\]{}()<>]', '', text)
    text = re.sub(r'[=+*/^_|~`]', '', text)
    text = re.sub(r'[@#$%&]', '', text)
    text = re.sub(r'[¥\\]', '', text)

    # 句読点とその他の区切り文字
    text = re.sub(r'[、。，。.!?!？;:,\'"\"\'"`]', '', text)

    # 複数の空白を1つに統一
    text = re.sub(r'\s+', ' ', text).strip()

    # テキストが空またはあまりに短い場合は空文字を返す
    if not text or len(text.strip()) < 1:
        return ""

    return text[:200]

def synthesize(text: str, guild_id: int, speaker=None) -> io.BytesIO:
    """
    テキストを音声に変換してメモリバッファに返す
    
    Args:
        text: 音声合成対象テキスト
        guild_id: ギルドID
        speaker: スピーカーID（未使用）
    
    Returns:
        WAV データを含む BytesIO オブジェクト
    """
    # pyopenjtalk で音声合成（同期処理）
    wav, sr = pyopenjtalk.tts(text)

    # 正規化
    max_amp = np.max(np.abs(wav))
    if max_amp > 0:
        wav = wav / max_amp * 1.0

    # メモリバッファに WAV を書き込む
    buffer = io.BytesIO()
    sf.write(buffer, wav, sr, format='WAV')
    buffer.seek(0)
    
    return buffer

async def tts_worker(bot, guild_id: int):

    guild = bot.get_guild(guild_id)
    queue = bot.tts_queues[guild_id]

    while True:
        try:
            text, speaker = await queue.get()

            vc = guild.voice_client
            if not vc or not vc.is_connected():
                queue.task_done()
                continue

            clean = sanitize_text(text, guild)
            if not clean:
                queue.task_done()
                continue

            buffer = await asyncio.to_thread(
                synthesize, clean, guild_id, speaker
            )

            audio = discord.FFmpegPCMAudio(buffer, pipe=True)
            vc.play(discord.PCMVolumeTransformer(audio, volume=0.7))

            # 再生終了待ち
            while vc.is_playing():
                await asyncio.sleep(0.1)

            queue.task_done()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"TTS worker error: {e}")
            queue.task_done()
