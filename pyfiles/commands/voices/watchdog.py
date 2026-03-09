import asyncio
from ...services.logger import logger
from ...services.tts import tts_worker


async def ensure_voice(bot, guild, channel):
    vc = guild.voice_client

    # 接続済みなら移動だけ
    if vc and vc.is_connected():
        if vc.channel != channel:
            await vc.move_to(channel)
        return vc

    # 壊れたVCが残っている場合
    if vc:
        await vc.disconnect(force=True)

    return await channel.connect(timeout=30.0, reconnect=False)

async def vc_watchdog(bot, guild_id: int):
    guild = bot.get_guild(guild_id)
    if not guild:
        return

    if guild_id in bot.manual_disconnect:
        bot.manual_disconnect.discard(guild_id)
        return

    settings = await bot.tts_settings_storage.get(guild_id)
    if not settings or not settings.get("enabled", False):
        return

    vc = guild.voice_client
    if vc and vc.is_connected():
        return

    # メンバーのいるVCを探す
    channel = None
    for member in guild.members:
        if member.voice and member.voice.channel:
            channel = member.voice.channel
            break

    if not channel:
        return

    try:
        await ensure_voice(bot, guild, channel)

        # worker再起動
        if guild_id in bot.tts_tasks:
            bot.tts_tasks[guild_id].cancel()

        bot.tts_queues[guild_id] = asyncio.Queue()
        bot.tts_tasks[guild_id] = bot.loop.create_task(
            tts_worker(bot, guild_id)
        )

        logger.info("VC再接続成功")

    except Exception as e:
        logger.error(f"VC再接続失敗: {e}")
