"""
遊び系コマンド

/dice, thinking(アプリ) などのエンタメ系コマンド
"""
import discord
from discord import app_commands
import random
import re
from ..services.logger import logger


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.context_menu(name="🤔 thinking")
    async def thinking(interaction: discord.Interaction, message: discord.Message):
        try:
            await message.add_reaction("🤔")
            await interaction.response.send_message("🤔 を付けました", ephemeral=True)
            logger.info(f"thinking コマンド実行: {interaction.user} がメッセージにを付子")
        except discord.Forbidden:
            await interaction.response.send_message("リアクションを付ける権限がありません", ephemeral=True)
            logger.warning(f"thinking コマンド: {interaction.user} がリアクション付子権限なし")
        except Exception as e:
            await interaction.response.send_message("エラーが発生しました", ephemeral=True)
            logger.error(f"thinking コマンドエラー: {e}")
    
    @bot.tree.command(name="dice", description="ダイスを振る（例: 1d20, 2d6+3）")
    @app_commands.describe(notation="ダイス表記（例: 1d20, 2d6+3）")
    async def dice(interaction: discord.Interaction, notation: str):
        m = re.fullmatch(r"(\d+)[dD](\d+)([+-]\d+)?", notation.strip())
        if not m:
            await interaction.response.send_message(
                "形式が正しくありません。例: `1d20`, `2d6+3`", 
                ephemeral=True
            )
            return

        n = int(m.group(1))  # 個数
        sides = int(m.group(2))  # 面数
        mod = int(m.group(3)) if m.group(3) else 0  # 補正

        if n < 1 or n > 100 or sides < 1 or sides > 1000 or abs(mod) > 100:
            await interaction.response.send_message(
                "指定範囲外です（個数:1–100、面数:1–1000、補正:±100）", 
                ephemeral=True
            )
            return

        rolls = [random.randint(1, sides) for _ in range(n)]
        total = sum(rolls) + mod

        # クリティカル / ファンブル判定（全ダイス対応）
        crit = any(1 <= r <= 5 for r in rolls)
        fumble = any((sides - 5) <= r <= sides for r in rolls)

        flag_text = ""
        if crit and fumble:
            flag_text = " **🎉 クリティカル！／💥 ファンブル！**"
        elif crit:
            flag_text = " **🎉 クリティカル！**"
        elif fumble:
            flag_text = " **💥 ファンブル！**"

        mod_text = f"{'+' if mod >= 0 else ''}{mod}" if mod else ""

        await interaction.response.send_message(
            f"🎲 `{n}d{sides}{mod_text}`{flag_text}\n出目: {rolls}\n合計: **{total}**"
        )
        logger.info(f"/dice コマンド実行: {interaction.user} (表記: {n}d{sides}{mod_text}, 合計: {total})")
