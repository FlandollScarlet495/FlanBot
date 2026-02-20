"""
ヘルプ・動作確認コマンド

/help, /ping, /about, /test などの基本コマンド
"""
import discord
from discord import app_commands
from ..services.logger import logger


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.command(name="help", description="ヘルプを表示")
    async def help_cmd(interaction: discord.Interaction):
        # ======== Embed 1: 画像・お遊び＆ロール管理 ========
        embed1 = discord.Embed(
            title="ふらんちゃんbot コマンド一覧 (1/3)",
            color=discord.Color.blue()
        )
        
        embed1.add_field(name="━━ 画像・お遊び ━━", value="", inline=False)
        embed1.add_field(name="/sonanoka", value="そーなのかー画像表示", inline=False)
        embed1.add_field(name="/sonanoda", value="そーなのだー画像表示", inline=False)
        embed1.add_field(name="/flandre", value="ふらんちゃん画像表示", inline=False)
        embed1.add_field(name="/stamp1", value="ふらんちゃんスタンプ表示", inline=False)
        embed1.add_field(name="/dice", value="サイコロを振る", inline=False)
        embed1.add_field(name="/thinking", value="返信先に🤔リアクション", inline=False)
        
        embed1.add_field(name="━━ ロール管理 ━━", value="", inline=False)
        embed1.add_field(name="/give_role ユーザー名", value="指定したユーザーにロールを付与", inline=False)
        embed1.add_field(name="/remove_role ユーザー名", value="指定したユーザーからロールを剥奪", inline=False)
        
        # ======== Embed 2: ボイスチャット・TTS ＆ TTS辞書 ========
        embed2 = discord.Embed(
            title="ふらんちゃんbot コマンド一覧 (2/3)",
            color=discord.Color.green()
        )
        
        embed2.add_field(name="━━ ボイスチャット・TTS ━━", value="", inline=False)
        embed2.add_field(
            name="/join", 
            value="VCに参加して TTS 機能を有効化\n例: ボイスチャットに接続し、テキストメッセージを自動で読み上げします", 
            inline=False
        )
        embed2.add_field(
            name="/leave", 
            value="VCから退出", 
            inline=False
        )
        embed2.add_field(
            name="/tts_on / /tts_off", 
            value="TTS読み上げのON/OFF切り替え（VCには参加したまま）", 
            inline=False
        )
        embed2.add_field(
            name="/skip", 
            value="現在再生中・待機中のTTS読み上げをスキップ", 
            inline=False
        )
        
        embed2.add_field(name="━━ TTS辞書管理（管理者専用）━━", value="", inline=False)
        embed2.add_field(
            name="/tts_dict_add 単語 読み方", 
            value="TTS辞書に単語を登録\n例: `/tts_dict_add 擬音語 ぎおんご`\n→ 「擬音語」を「ぎおんご」と読み上げるよう登録", 
            inline=False
        )
        embed2.add_field(
            name="/tts_dict_remove 単語", 
            value="TTS辞書から単語を削除\n例: `/tts_dict_remove 擬音語`", 
            inline=False
        )
        embed2.add_field(
            name="/tts_dict_list", 
            value="登録されている辞書一覧を表示（番号付き）", 
            inline=False
        )
        
        # ======== Embed 3: メッセージ削除 ＆ 動作確認 ========
        embed3 = discord.Embed(
            title="ふらんちゃんbot コマンド一覧 (3/3)",
            color=discord.Color.purple()
        )
        
        embed3.add_field(name="━━ メッセージ削除 ━━", value="", inline=False)
        embed3.add_field(name="/delete", value="自分 ＋ bot のメッセージを削除", inline=False)
        embed3.add_field(name="/admin_del", value="管理者専用削除（権限チェック付き）", inline=False)
        
        embed3.add_field(name="━━ 動作確認 ━━", value="", inline=False)
        embed3.add_field(name="/ping", value="動作速度確認（応答時間を表示）", inline=False)
        embed3.add_field(name="/about", value="ふらんちゃん プロフィール表示", inline=False)
        embed3.add_field(name="/test", value="テスト", inline=False)

        await interaction.response.send_message(embeds=[embed1, embed2, embed3])
        logger.info(f"/help コマンド実行: {interaction.user}")
    
    @bot.tree.command(name="ping", description="動作速度確認")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")
        logger.info(f"/ping コマンド実行: {interaction.user}")
    
    @bot.tree.command(name="about", description="動作確認")
    async def about(interaction: discord.Interaction):
        await interaction.response.send_message("flandre, ふらんちゃん")
        logger.info(f"/about コマンド実行: {interaction.user}")
    
    @bot.tree.command(name="test", description="テスト")
    async def test(interaction: discord.Interaction):
        await interaction.response.send_message("test")
        logger.info(f"/test コマンド実行: {interaction.user}")
