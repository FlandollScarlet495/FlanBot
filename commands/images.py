"""
画像コマンド

/sonanoka, /sonanoda, /flandre, /stamp1_flan などの画像表示コマンド
"""
import discord
from discord import app_commands
import os
import re


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.command(name="sonanoka", description="そーなのかー")
    async def sonanoka(interaction: discord.Interaction):
        await interaction.response.send_message(file=discord.File("sonanoka.png"))
        print("/sonanokaが実行されました")
    
    @bot.tree.command(name="sonanoda", description="そーなのだー")
    async def sonanoda(interaction: discord.Interaction):
        await interaction.response.send_message(file=discord.File("sonanoda.png"))
        print("/sonanodaが実行されました")
    
    @bot.tree.command(name="flandre", description="ふらんちゃん")
    async def flandre(interaction: discord.Interaction):
        await interaction.response.send_message(file=discord.File("flandre.png"))
        print("/flandreが実行されました")
    
    @bot.tree.command(name="stamp1_flan", description="スタンプ画像を表示（例: p0）")
    @app_commands.describe(name="スタンプ名（例: p0 ～ p52）")
    async def stamp1(interaction: discord.Interaction, name: str):
        # p<number> をパース
        if not name.startswith("p"):
            await interaction.response.send_message("形式が違います（例: p0）", ephemeral=True)
            return

        num_part = name.replace("p", "", 1)

        if not num_part.isdigit():
            await interaction.response.send_message("番号は数字で指定してください（例: p12）", ephemeral=True)
            return

        n = int(num_part)

        if n < 0 or n > 52:
            await interaction.response.send_message("番号は 0〜52 の範囲で指定してください", ephemeral=True)
            return

        filename = f"stamp1/p{n}.png"

        if not os.path.exists(filename):
            await interaction.response.send_message("画像ファイルが見つかりません", ephemeral=True)
            return

        await interaction.response.send_message(file=discord.File(filename))
