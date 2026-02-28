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

        await interaction.response.defer()

        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.followup.send("権限がありません", ephemeral=True)
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

        # watchdogは1つだけ
        if gid in bot.watchdog_tasks:
            bot.watchdog_tasks[gid].cancel()

        bot.watchdog_tasks[gid] = bot.loop.create_task(
            vc_watchdog(bot, gid)
        )

        await interaction.followup.send(f"「{channel}」に参加しました")

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

        if gid in bot.watchdog_tasks:
            bot.watchdog_tasks[gid].cancel()
            del bot.watchdog_tasks[gid]

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

        if gid not in bot.tts_tasks:
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

    @bot.tree.command(name="setvoice", description="音声設定")
    async def setvoice(
        interaction: discord.Interaction,
        engine: str = None,
        name: str = None,
        style: str = None,
        speed: int = None,
        pitch: int = None
    ):

        if not interaction.guild:
            await interaction.response.send_message("サーバー内で実行してください")
            return

        gid = interaction.guild.id
        uid = interaction.user.id

        # 現在設定取得（なければデフォルト）
        current = await interaction.client.db_initializer.get_user_voice(gid, uid)

        current_engine = current.get("engine", "openjtalk")
        current_speaker = current.get("speaker_id")
        current_speed = current.get("speed", 1.0)
        current_pitch = current.get("pitch", 0.0)

        # ---- engine処理 ----
        if engine:
            if engine not in ["openjtalk", "voicevox"]:
                await interaction.response.send_message(
                    "engineは openjtalk / voicevox"
                )
                return
            current_engine = engine

        # ---- voicevox話者処理 ----
        if name:
            if current_engine != "voicevox":
                await interaction.response.send_message(
                    "voicevoxを使用する場合 engine=voicevox を指定してください"
                )
                return

            if style is None:
                style = "ノーマル"

            speaker_id = interaction.client.voicevox.get_id(name, style)

            if speaker_id is None:
                await interaction.response.send_message("指定された声が見つかりません")
                return

            current_speaker = speaker_id

        # ---- speed処理 ----
        if speed is not None:
            if not (50 <= speed <= 200):
                await interaction.response.send_message("speedは50〜200")
                return
            current_speed = speed / 100

        # ---- pitch処理 ----
        if pitch is not None:
            if not (50 <= pitch <= 200):
                await interaction.response.send_message("pitchは50〜200")
                return
            current_pitch = (pitch - 100) / 100

        # 保存
        await interaction.client.db_initializer.set_user_voice(
            gid,
            uid,
            current_engine,
            current_speaker,
            current_speed,
            current_pitch
        )

        await interaction.response.send_message("音声設定を更新しました")

    @bot.tree.command(name="setmembervoice", description="メンバーの音声設定を変更")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setmembervoice(
        interaction: discord.Interaction,
        member: discord.Member,
        engine: str = None,
        name: str = None,
        style: str = None,
        speed: int = None,
        pitch: int = None
    ):

        if not interaction.guild:
            await interaction.response.send_message("サーバー内で実行してください")
            return

        gid = interaction.guild.id
        uid = member.id

        current = await interaction.client.db_initializer.get_user_voice(gid, uid)

        current_engine = current.get("engine", "openjtalk")
        current_speaker = current.get("speaker_id")
        current_speed = current.get("speed", 1.0)
        current_pitch = current.get("pitch", 0.0)

        if engine:
            if engine not in ["openjtalk", "voicevox"]:
                await interaction.response.send_message("engineは openjtalk / voicevox")
                return
            current_engine = engine

        if name:
            if current_engine != "voicevox":
                await interaction.response.send_message("voicevoxを使用する場合 engine=voicevox を指定してください")
                return

            if style is None:
                style = "ノーマル"

            speaker_id = interaction.client.voicevox.get_id(name, style)
            if speaker_id is None:
                await interaction.response.send_message("指定された声が見つかりません")
                return

            current_speaker = speaker_id

        if speed is not None:
            if not (50 <= speed <= 200):
                await interaction.response.send_message("speedは50〜200")
                return
            current_speed = speed / 100

        if pitch is not None:
            if not (50 <= pitch <= 200):
                await interaction.response.send_message("pitchは50〜200")
                return
            current_pitch = (pitch - 100) / 100

        await interaction.client.db_initializer.set_user_voice(
            gid,
            uid,
            current_engine,
            current_speaker,
            current_speed,
            current_pitch
        )

        await interaction.response.send_message(
            f"{member.display_name} の音声設定を更新しました"
        )

    @bot.tree.command(name="voice_list")
    async def voice_list(interaction):

        voices = interaction.client.voicevox.voice_dict

        text = ""

        for name, styles in voices.items():
            style_list = ", ".join(styles.keys())
            text += f"{name} : {style_list}\n"

        await interaction.response.send_message(
            f"利用可能話者一覧\n{text[:1800]}"
        )
