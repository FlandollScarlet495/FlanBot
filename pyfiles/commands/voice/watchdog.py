import asyncio
from ...services.logger import logger
from ...services.tts import tts_worker


async def vc_watchdog(bot, guild_id: int):
    while True:
        await asyncio.sleep(3)

        guild = bot.get_guild(guild_id)
        if not guild:
            return

        if guild_id in bot.manual_disconnect:
            bot.manual_disconnect.remove(guild_id)
            logger.info("手動切断、監視終了")
            return

        vc = guild.voice_client
        if vc and vc.is_connected():
            continue

        channel = None
        for member in guild.members:
            if member.voice and member.voice.channel:
                channel = member.voice.channel
                break

        if not channel:
            continue

        settings = await bot.tts_settings_storage.get(guild_id)
        if not settings or not settings.get("enabled", False):
            return

        try:
            # 既存worker停止
            if guild_id in bot.tts_tasks:
                bot.tts_tasks[guild_id].cancel()
                del bot.tts_tasks[guild_id]

            if guild_id in bot.tts_queues:
                del bot.tts_queues[guild_id]

            await channel.connect()
            logger.info(f"VC再接続成功: {channel}")

            # worker再起動
            bot.tts_queues[guild_id] = asyncio.Queue()
            bot.tts_tasks[guild_id] = bot.loop.create_task(
                tts_worker(bot, guild_id)
            )

        except Exception as e:
            logger.error(f"VC再接続失敗: {e}")
