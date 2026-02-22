"""
画像コマンド

/sonanoka, /sonanoda, /flandre, /stamp1_flan などの画像表示コマンド
"""
import discord
from discord import app_commands
import os
from ...services.logger import logger
import re

# 画像ファイルの基準ディレクトリ（commands/ ディレクトリ）
IMAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.command(name="sonanoka", description="そーなのかー")
    async def sonanoka(interaction: discord.Interaction):
        file_path = os.path.join(IMAGE_DIR, "sonanoka.png")
        if not os.path.exists(file_path):
            await interaction.response.send_message(f"ファイルが見つかりません: {file_path}", ephemeral=True)
            logger.warning(f"sonanoka.png が見つかりません: {file_path}")
            return
        await interaction.response.send_message(file=discord.File(file_path))
        logger.info(f"/sonanoka コマンド実行: {interaction.user}")
    
    @bot.tree.command(name="sonanoda", description="そーなのだー")
    async def sonanoda(interaction: discord.Interaction):
        file_path = os.path.join(IMAGE_DIR, "sonanoda.png")
        if not os.path.exists(file_path):
            await interaction.response.send_message(f"ファイルが見つかりません: {file_path}", ephemeral=True)
            logger.warning(f"sonanoda.png が見つかりません: {file_path}")
            return
        await interaction.response.send_message(file=discord.File(file_path))
        logger.info(f"/sonanoda コマンド実行: {interaction.user}")
    
    @bot.tree.command(name="flandre", description="ふらんちゃん")
    async def flandre(interaction: discord.Interaction):
        file_path = os.path.join(IMAGE_DIR, "flandre.png")
        if not os.path.exists(file_path):
            await interaction.response.send_message(f"ファイルが見つかりません: {file_path}", ephemeral=True)
            logger.warning(f"flandre.png が見つかりません: {file_path}")
            return
        await interaction.response.send_message(file=discord.File(file_path))
        logger.info(f"/flandre コマンド実行: {interaction.user}")
    
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

        filename = os.path.join(IMAGE_DIR, "stamp1", f"p{n}.png")

        if not os.path.exists(filename):
            await interaction.response.send_message(f"画像ファイルが見つかりません: {filename}", ephemeral=True)
            logger.warning(f"stamp1 ファイルが見つかりません: {filename}")
            return

        await interaction.response.send_message(file=discord.File(filename))
