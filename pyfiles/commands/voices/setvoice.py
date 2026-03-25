import discord
from discord import app_commands
import asyncio
from ...services.logger import logger

def setup_commands(bot):

    # --- オートコンプリート関数 ---
    async def voice_name_autocomplete(interaction: discord.Interaction, current: str):
        voices = bot.voicevox.voice_dict
        results = [
            app_commands.Choice(name=name, value=name)
            for name in voices.keys() if current.lower() in name.lower()
        ]
        return results[:25]

    async def voice_style_autocomplete(interaction: discord.Interaction, current: str):
        voices = bot.voicevox.voice_dict
        name = interaction.namespace.name
        if not name:
            return []
        styles = voices.get(name, {})
        results = [
            app_commands.Choice(name=style, value=style)
            for style in styles.keys() if current.lower() in style.lower()
        ]
        return results[:25]

    # --- 内部処理用関数 ---
    async def _process_set_voice(interaction, target_id, engine, name, style, speed, pitch):
        gid = interaction.guild.id
        voice_engine, voice_speaker_id, voice_speed, voice_pitch = await bot.db_initializer.get_user_voice(gid, target_id)
        # print("取得値:", voice_engine, voice_speaker_id, voice_speed, voice_pitch)

        if engine:
            current_engine = engine.lower()
            if current_engine == "openjtalk":
                current_speaker = 1
            else:
                current_speaker = None
        else:
            current_engine = voice_engine or "openjtalk"
            current_speaker = voice_speaker_id
        current_speed = (speed / 100) if speed is not None else (voice_speed or 1.0)
        current_pitch = ((pitch - 100) / 100) if pitch is not None else (voice_pitch or 0.0)

        if engine and engine.lower() not in ["openjtalk", "voicevox"]:
            await interaction.response.send_message("engineは OpenJTalk / Voicevox を選んでね！", ephemeral=True)
            return False

        if name:
            if current_engine != "voicevox":
                await interaction.response.send_message("Voicevoxを使用する場合 engine=Voicevox を指定してね！", ephemeral=True)
                return False

            speaker_id = bot.voicevox.get_id(name, style or "ノーマル")
            if speaker_id is None:
                await interaction.response.send_message("指定された声が見つかりません", ephemeral=True)
                return False

            current_speaker = speaker_id

        elif current_engine == "voicevox" and current_speaker is None:
            await interaction.response.send_message("Voicevoxではspeaker指定が必要です！", ephemeral=True)
            return False

        if (speed is not None and not (50 <= speed <= 200)) or (pitch is not None and not (50 <= pitch <= 200)):
            await interaction.response.send_message("速度とピッチは50〜200の間で設定してね！", ephemeral=True)
            return False

        await bot.db_initializer.set_user_voice(gid, target_id, current_engine, current_speaker, current_speed, current_pitch)
        return True

    # --- コマンド定義 ---
    @app_commands.command(name="setvoice", description="音声設定")
    @app_commands.describe(engine="OpenJTalk / Voicevox", name="Voicevoxキャラ名", style="Voicevoxスタイル", speed="速度(50〜200)", pitch="ピッチ(50〜200)")
    @app_commands.autocomplete(name=voice_name_autocomplete, style=voice_style_autocomplete)
    async def setvoice(interaction: discord.Interaction, engine: str = None, name: str = None, style: str = None, speed: int = None, pitch: int = None):
        if not interaction.guild:
            return await interaction.response.send_message("サーバー内で実行してください", ephemeral=True)

        # _process_set_voice 内でメッセージを送信した場合は、ここで再度送らないようにする
        if await _process_set_voice(interaction, interaction.user.id, engine, name, style, speed, pitch):
            await interaction.response.send_message("音声設定を更新しました", ephemeral=True) # ephemeral=True にして、設定変更の確認メッセージを実行ユーザーのみに表示するようにする

    @app_commands.command(name="setmembervoice", description="メンバーの音声設定を変更")
    @app_commands.describe(member="対象メンバー", engine="OpenJTalk / Voicevox", name="Voicevoxキャラ名", style="Voicevoxスタイル", speed="速度(50〜200)", pitch="ピッチ(50〜200)")
    @app_commands.autocomplete(name=voice_name_autocomplete, style=voice_style_autocomplete)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setmembervoice(interaction: discord.Interaction, member: discord.Member, engine: str = None, name: str = None, style: str = None, speed: int = None, pitch: int = None):
        if not interaction.guild:
            return await interaction.response.send_message("サーバー内で実行してください", ephemeral=True)

        if await _process_set_voice(interaction, member.id, engine, name, style, speed, pitch):
            await interaction.response.send_message(f"{member.display_name} の音声設定を更新しました", ephemeral=True) # ephemeral=True にして、設定変更の確認メッセージを実行ユーザーのみに表示するようにする

    @app_commands.command(name="voicelist", description="利用可能話者一覧を表示")
    async def voice_list(interaction: discord.Interaction):
        voices = bot.voicevox.voice_dict
        if not voices:
            return await interaction.response.send_message("Voicevoxエンジンが起動していないか、話者情報を取得できていません。", ephemeral=True)
        
        text = ""
        for name, styles in voices.items():
            style_list = ", ".join(styles.keys())
            text += f"**{name}**: {style_list}\n"

        await interaction.response.send_message(f"### 利用可能話者一覧\n{text[:1900]}", ephemeral=True) # ephemeral=True にして、設定変更の確認メッセージを実行ユーザーのみに表示するようにする

    bot.tree.add_command(setvoice)
    bot.tree.add_command(setmembervoice)
    bot.tree.add_command(voice_list)
