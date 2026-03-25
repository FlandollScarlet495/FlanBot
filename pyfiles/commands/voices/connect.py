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

        # deferをephemeral=Trueで実行すると、
        # 後続のfollowupもすべて非公開メッセージになる
        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.followup.send("権限がありません") # ここは ephemeral=True を書かなくても引き継がれるよ
            return

        if not interaction.user.voice:
            await interaction.followup.send("先にVCへ参加してください")
            return

        channel = interaction.user.voice.channel

        vc = interaction.guild.voice_client
        if vc:
            await vc.move_to(channel)
        else:
            await channel.connect()

        # --- watchdogの設定 ---
        if gid in bot.watchdog_tasks:
            bot.watchdog_tasks[gid].cancel()

        bot.watchdog_tasks[gid] = bot.loop.create_task(
            vc_watchdog(bot, gid)
        )

        await interaction.followup.send(f"「{channel}」に参加しました")
        logger.info(f"/join: {interaction.user} joined VC")

    @bot.tree.command(name="leave", description="VC退出")
    async def leave(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            # defer()後はresponse.send_message()は使えないため、
            # 追加メッセージはfollowup.send()で送る
            await interaction.followup.send("権限がありません")
            return

        vc = interaction.guild.voice_client
        if not vc:
            # defer()後はresponse.send_message()は使えないため、
            # 追加メッセージはfollowup.send()で送る
            await interaction.followup.send("VCに参加していません")
            return

        channel = interaction.user.voice.channel

        await bot.tts_settings_storage.set_enabled(gid, False)

        if gid in bot.tts_tasks:
            bot.tts_tasks[gid].cancel()
            del bot.tts_tasks[gid]
            if gid in bot.tts_queues:
                del bot.tts_queues[gid]

        bot.manual_disconnect.add(gid)
        await vc.disconnect()

        if gid in bot.watchdog_tasks:
            bot.watchdog_tasks[gid].cancel()
            del bot.watchdog_tasks[gid]

        # defer()後はresponse.send_message()は使えないため、
        # 追加メッセージはfollowup.send()で送る
        await interaction.followup.send(f"「{channel}」から退出しました")
        logger.info(f"/leave: {interaction.user} left VC")

    @bot.tree.command(name="skip", description="TTS再生をスキップ")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.followup.send("権限がありません")
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.followup.send("VCに参加していません")
            return

        if not vc.is_playing():
            await interaction.followup.send("再生中ではありません")
            return

        vc.stop()

        queue = bot.tts_queues.get(gid)
        if queue:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        await interaction.followup.send("TTS再生をスキップしました")
        logger.info(f"/skip: {interaction.user} skipped TTS in guild {gid}")

    @bot.tree.command(name="tts_on", description="TTS読み込みを有効化")
    async def tts_on(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.followup.send("権限がありません")
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.followup.send("VCに参加していません")
            return

        await bot.tts_settings_storage.set_enabled(gid, True)

        if gid not in bot.tts_queues:
            bot.tts_queues[gid] = asyncio.Queue()

        if gid not in bot.tts_tasks:
            bot.tts_tasks[gid] = bot.loop.create_task(
                tts_worker(bot, gid)
            )

        await interaction.followup.send("TTS読み込みを有効化しました")
        logger.info(f"/tts_on: {interaction.user} enabled TTS in guild {gid}")

    @bot.tree.command(name="tts_off", description="TTS読み込みを無効化")
    async def tts_off(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.followup.send("権限がありません")
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.followup.send("VCに参加していません")
            return

        await bot.tts_settings_storage.set_enabled(gid, False)

        if gid in bot.tts_tasks:
            bot.tts_tasks[gid].cancel()
            if gid in bot.tts_queues:
                del bot.tts_queues[gid]
            del bot.tts_tasks[gid]

        await interaction.followup.send("TTS読み込みを無効化しました")
        logger.info(f"/tts_off: {interaction.user} disabled TTS in guild {gid}")

    @bot.event
    async def on_voice_state_update(member, before, after):

        if member.id != bot.user.id:
            return

        if member.guild.id in bot.manual_disconnect:
            return

        if before.channel and not after.channel:
            asyncio.create_task(
                vc_watchdog(bot, member.guild.id)
            )
