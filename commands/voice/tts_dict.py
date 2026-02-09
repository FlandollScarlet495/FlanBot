import discord
from services.permission import is_admin_or_dev
from services.storage import tts_dict_storage

def setup_commands(bot):
    @bot.tree.command(name="tts_dict_add", description="TTS辞書に単語を追加")
    async def tts_dict_add(
        interaction: discord.Interaction,
        surface: str,
        reading: str
    ):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        ok = tts_dict_storage.add(
            interaction.guild.id,
            surface,
            reading
        )

        if not ok:
            await interaction.response.send_message("すでに登録されています", ephemeral=True)
            return

        await interaction.response.send_message(
            f"辞書に追加しました\n`{surface}` → `{reading}`",
            ephemeral=True
        )

    @bot.tree.command(name="tts_dict_remove", description="TTS辞書から単語を削除")
    async def tts_dict_remove(
        interaction: discord.Interaction,
        surface: str
    ):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        ok = tts_dict_storage.remove(
            interaction.guild.id,
            surface
        )

        if not ok:
            await interaction.response.send_message("見つかりませんでした", ephemeral=True)
            return

        await interaction.response.send_message(
            f"`{surface}` を辞書から削除しました",
            ephemeral=True
        )

    @bot.tree.command(name="tts_dict_list", description="TTS辞書一覧")
    async def tts_dict_list(interaction: discord.Interaction):
        rows = tts_dict_storage.list(interaction.guild.id)

        if not rows:
            await interaction.response.send_message("辞書は空です", ephemeral=True)
            return

        text = "\n".join(
            f"`{s}` → `{r}`" for s, r in rows
        )

        await interaction.response.send_message(
            text,
            ephemeral=True
        )
