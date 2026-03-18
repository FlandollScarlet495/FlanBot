"""
TTS辞書管理コマンド

/tts_dict_add, /tts_dict_remove, /tts_dict_list コマンドで
読み方が難しい単語を辞書登録し、TTS読み上げを制御します
"""
import discord
from discord import app_commands
from ...services.permission import is_admin_or_dev
from ...services.storage import tts_dict_storage

def setup_commands(bot):
    @bot.tree.command(name="tts_dict_add", description="TTS辞書に単語を追加（読み方を指定して読み上げを制御）")
    @app_commands.describe(
        surface="登録する単語（表記、最大100文字）。例: 擬音語、難読漢字、固有名詞など",
        reading="その単語をどう読むか（ひらがな、最大200文字）。例: がぐみぐみ、てすと、あるふぁ"
    )
    async def tts_dict_add(
        interaction: discord.Interaction,
        surface: str,
        reading: str
    ):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        # 入力長チェック（セキュリティ対策）
        if not surface.strip() or len(surface) > 100:
            await interaction.response.send_message("表記は1文字以上100文字以下である必要があります", ephemeral=True)
            return
        if not reading.strip() or len(reading) > 200:
            await interaction.response.send_message("読み方は1文字以上200文字以下である必要があります", ephemeral=True)
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
            f"✅ 辞書に追加しました\n\n📝 登録内容\n表記: `{surface}` → 読み方: `{reading}`\n\n💡 使用例: メッセージに「{surface}」と書くと「{reading}」と読み上げられます",
            ephemeral=True
        )

    @bot.tree.command(name="tts_dict_remove", description="TTS辞書から単語を削除")
    @app_commands.describe(
        surface="削除する単語（表記）"
    )
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
            f"✅ 削除完了: `{surface}`\n\n(`/tts_dict_list` で現在の登録状況を確認できます)",
            ephemeral=True
        )

    @bot.tree.command(name="tts_dict_list", description="TTS辞書一覧（登録されている単語と読み方を表示）")
    async def tts_dict_list(interaction: discord.Interaction):
        辞書リスト = tts_dict_storage.list(interaction.guild.id)

        if not 辞書リスト:
            await interaction.response.send_message(
                "📭 辞書は空です\n\n`/tts_dict_add` で単語を登録してください",
                ephemeral=True
            )
            return

        # 一覧を見やすくフォーマット
        表示テキスト = "📚 TTS辞書登録状況:\n\n"
        for 番号, (表記, 読み方) in enumerate(辞書リスト, 1):
            表示テキスト += f"{番号}. `{表記}` → `{読み方}`\n"

        表示テキスト += f"\n💡 計 {len(辞書リスト)} 件登録されています"

        await interaction.response.send_message(
            表示テキスト,
            ephemeral=True
        )
