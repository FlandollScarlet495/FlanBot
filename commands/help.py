"""
ヘルプ・動作確認コマンド

/help, /ping, /about, /test などの基本コマンド
"""
import discord
from discord import app_commands


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.command(name="help", description="ヘルプを表示")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(
            title="ふらんちゃんbot コマンド一覧",
            color=discord.Color.blue()
        )
        embed.add_field(name="thinking(アプリ)", value="返信先に🤔リアクション", inline=False)
        embed.add_field(name="/give_role", value="指定したユーザーにロールを付与", inline=False)
        embed.add_field(name="/remove_role", value="指定したユーザーからロールを剥奪", inline=False)
        embed.add_field(name="/sonanoka", value="そーなのかー画像表示", inline=False)
        embed.add_field(name="/sonanoda", value="そーなのだー画像表示", inline=False)
        embed.add_field(name="/flandre", value="ふらんちゃん画像表示", inline=False)
        embed.add_field(name="/stamp1", value="ふらんちゃんスタンプ表示", inline=False)
        embed.add_field(name="/dice", value="サイコロを振る", inline=False)
        embed.add_field(name="/delete", value="自分＋bot削除", inline=False)
        embed.add_field(name="/admin_del", value="管理者専用削除", inline=False)
        embed.add_field(name="/test", value="テスト", inline=False)
        embed.add_field(name="/ping", value="動作速度確認", inline=False)
        embed.add_field(name="/about", value="動作確認", inline=False)
        embed.add_field(name="/join", value="VC参加", inline=False)
        embed.add_field(name="/leave", value="VC退出", inline=False)

        await interaction.response.send_message(embed=embed)
        print("/helpが実行されました")
    
    @bot.tree.command(name="ping", description="動作速度確認")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")
        print("/pingが実行されました")
    
    @bot.tree.command(name="about", description="動作確認")
    async def about(interaction: discord.Interaction):
        await interaction.response.send_message("flandre, ふらんちゃん")
        print("/aboutが実行されました")
    
    @bot.tree.command(name="test", description="テスト")
    async def test(interaction: discord.Interaction):
        await interaction.response.send_message("test")
        print("/testが実行されました")
