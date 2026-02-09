import re
import pyopenjtalk
import soundfile as sf
import uuid
import asyncio
import discord
import os
import unicodedata
import numpy as np
import tempfile
import io
import hashlib
from services.logger import logger
from services.storage import tts_dict_storage

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
    """
    ギルド別 TTS ワーカー
    - 合成タスク：テキストを音声に合成
    - 再生タスク：合成済み音声を再生
    """
    guild = bot.get_guild(guild_id)
    queue = bot.tts_queues[guild_id]
    playback_queue = asyncio.Queue()
    # playback_queue を bot 側で参照できるように保存（/skip で消去できるように）
    try:
        bot.playback_queues[guild_id] = playback_queue
    except Exception:
        # bot が期待どおりの属性を持たない場合は無視
        pass

    async def synthesis_task():
        """テキストを合成してバッファを再生キューに追加"""
        while True:
            try:
                text, speaker = await queue.get()

                clean = sanitize_text(text, guild)
                if not clean:
                    queue.task_done()
                    continue

                # 音声合成を別スレッドで実行
                try:
                    buffer = await asyncio.to_thread(synthesize, clean, guild_id, speaker)
                    await playback_queue.put((buffer, text[:20]))
                except Exception as e:
                    logger.error(f"[Guild {guild_id}] TTS 合成エラー: {e}")

                queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Synthesis task error: {e}")
                queue.task_done()

    async def playback_task():
        """バッファを再生"""
        while True:
            try:
                vc = guild.voice_client
                if not vc or not vc.is_connected():
                    await asyncio.sleep(1)
                    continue

                buffer, text_preview = await asyncio.wait_for(
                    playback_queue.get(), timeout=1.0
                )

                # 再生中の場合は待機
                while vc.is_playing():
                    if bot.skip_flags.get(guild_id, False):
                        vc.stop()
                        bot.skip_flags[guild_id] = False
                        logger.info(f"[Guild {guild_id}] TTS 再生をスキップ")
                        break
                    await asyncio.sleep(0.1)

                # 再生
                audio_source = discord.FFmpegPCMAudio(buffer, pipe=True)
                vc.play(discord.PCMVolumeTransformer(audio_source, volume=0.7))

                playback_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Playback task error: {e}")

    # 合成タスクと再生タスクを同時実行
    tasks = [
        asyncio.create_task(synthesis_task()),
        asyncio.create_task(playback_task())
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        raise
    finally:
        # 終了時に playback_queue の参照を削除
        try:
            if guild_id in bot.playback_queues:
                del bot.playback_queues[guild_id]
        except Exception:
            pass
