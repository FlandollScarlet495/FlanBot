import discord
from discord import app_commands
import asyncio
from ...services.permission import can_use_vc
from ...services.storage import vc_allow_storage
from ...services.tts import tts_worker
from ...services.logger import logger
from .watchdog import vc_watchdog


def setup_commands(bot):

    @bot.tree.command(name="join", description="VC参加")
    async def join(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("先にVCへ参加してください")
            return

        if interaction.guild.voice_client:
            await interaction.response.send_message("すでにVCに参加しています")
            return

        channel = interaction.user.voice.channel
        await channel.connect()

        bot.loop.create_task(vc_watchdog(bot, gid))
        await bot.tts_settings_storage.set_enabled(gid, True)

        await interaction.response.send_message(f"「{channel}」に参加しました")
        logger.info(f"/join: {interaction.user} joined {channel}")

    @bot.tree.command(name="leave", description="VC退出")
    async def leave(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("VCに参加していません")
            return

        await bot.tts_settings_storage.set_enabled(gid, False)

        if gid in bot.tts_tasks:
            bot.tts_tasks[gid].cancel()
            del bot.tts_tasks[gid]
            if gid in bot.tts_queues:
                del bot.tts_queues[gid]

        bot.manual_disconnect.add(gid)
        await vc.disconnect()

        await interaction.response.send_message("VCから退出しました")
        logger.info(f"/leave: {interaction.user} left VC")

    @bot.tree.command(name="skip", description="TTS再生をスキップ")
    async def skip(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("VCに参加していません", ephemeral=True)
            return

        if not vc.is_playing():
            await interaction.response.send_message("再生中ではありません", ephemeral=True)
            return

        vc.stop()

        queue = bot.tts_queues.get(gid)
        if queue:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        await interaction.response.send_message("TTS再生をスキップしました")
        logger.info(f"/skip: {interaction.user} skipped TTS in guild {gid}")

    @bot.tree.command(name="tts_on", description="TTS読み込みを有効化")
    async def tts_on(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("VCに参加していません", ephemeral=True)
            return

        await bot.tts_settings_storage.set_enabled(gid, True)

        if gid not in bot.tts_queues:
            bot.tts_queues[gid] = asyncio.Queue()
            bot.tts_tasks[gid] = bot.loop.create_task(
                tts_worker(bot, gid)
            )

        await interaction.response.send_message("TTS読み込みを有効化しました")
        logger.info(f"/tts_on: {interaction.user} enabled TTS in guild {gid}")

    @bot.tree.command(name="tts_off", description="TTS読み込みを無効化")
    async def tts_off(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("VCに参加していません", ephemeral=True)
            return

        await bot.tts_settings_storage.set_enabled(gid, False)

        if gid in bot.tts_tasks:
            bot.tts_tasks[gid].cancel()
            if gid in bot.tts_queues:
                del bot.tts_queues[gid]
            del bot.tts_tasks[gid]

        await interaction.response.send_message("TTS読み込みを無効化しました")
        logger.info(f"/tts_off: {interaction.user} disabled TTS in guild {gid}")
