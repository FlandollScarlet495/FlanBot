import discord
from discord import app_commands
from ...services.logger import logger


def setup_commands(bot):
    
    async def voice_name_autocomplete(
        interaction: discord.Interaction,
        current: str
    ):

        voices = interaction.client.voicevox.voice_dict

        results = []

        for name in voices.keys():
            if current.lower() in name.lower():
                results.append(app_commands.Choice(name=name, value=name))

        return results[:25]
    
    async def voice_style_autocomplete(
        interaction: discord.Interaction,
        current: str
    ):

        voices = interaction.client.voicevox.voice_dict

        name = interaction.namespace.name

        if not name:
            return []

        styles = voices.get(name, {})

        results = []

        for style in styles.keys():
            if current.lower() in style.lower():
                results.append(app_commands.Choice(name=style, value=style))

        return results[:25]

    @bot.tree.command(name="setvoice", description="音声設定")
    @app_commands.describe(
        engine="OpenJTalk / Voicevox",
        name="Voicevoxキャラ名",
        style="Voicevoxスタイル",
        speed="速度(50〜200)",
        pitch="ピッチ(50〜200)"
    )
    @app_commands.autocomplete(
        name=voice_name_autocomplete,
        style=voice_style_autocomplete
    )
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
        engine_v, speaker_id_v, speed_v, pitch_v = await interaction.client.db_initializer.get_user_voice(gid, uid)

        current_engine = engine_v or "openjtalk"
        current_speaker = speaker_id_v
        current_speed = speed_v or 1.0
        current_pitch = pitch_v or 0.0

        # ---- engine処理 ----
        if engine:
            if engine not in ["OpenJTalk", "Voicevox"]:
                await interaction.response.send_message(
                    "engineは Openjtalk / Voicevox"
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
    @app_commands.describe(
        engine="OpenJTalk / Voicevox",
        name="Voicevoxキャラ名",
        style="Voicevoxスタイル",
        speed="速度(50〜200)",
        pitch="ピッチ(50〜200)"
    )
    @app_commands.autocomplete(
        name=voice_name_autocomplete,
        style=voice_style_autocomplete
    )
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

        engine_v, speaker_id_v, speed_v, pitch_v = await interaction.client.db_initializer.get_user_voice(gid, uid)

        current_engine = engine_v or "openjtalk"
        current_speaker = speaker_id_v
        current_speed = speed_v or 1.0
        current_pitch = pitch_v or 0.0

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
