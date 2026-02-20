import asyncio
from ...services.logger import logger
from ...services.storage import tts_settings_storage

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

        settings = tts_settings_storage.get(guild_id)
        if not settings["enabled"]:
            return

        try:
            await channel.connect()
            logger.info(f"VC再接続成功: {channel}")
        except Exception as e:
            logger.error(f"VC再接続失敗: {e}")
