"""
ボイスチャット関連コマンド

/join, /leave, /vc_allow_* などのVC関連コマンド
"""
import discord
from discord import app_commands
import asyncio
from services.permission import can_use_vc, is_admin_or_dev
from services.storage import vc_allow_storage
from services.logger import logger


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    # 手動切断フラグ（botインスタンスに持たせる）
    if not hasattr(bot, 'manual_disconnect'):
        bot.manual_disconnect = set()
    
    async def vc_watchdog(guild_id: int):
        """VC監視タスク（自動再接続）"""
        while True:
            await asyncio.sleep(3)

            guild = bot.get_guild(guild_id)
            if not guild:
                return

            # 手動切断フラグチェック
            if guild_id in bot.manual_disconnect:
                bot.manual_disconnect.remove(guild_id)
                logger.info("手動切断、監視終了")
                return

            vc = guild.voice_client

            # 接続中なら何もしない
            if vc and vc.is_connected():
                continue

            # 再接続先を探す
            channel = None
            for member in guild.members:
                if member.voice and member.voice.channel:
                    channel = member.voice.channel
                    break

            if not channel:
                continue

            # 再接続試行
            try:
                await channel.connect()
                logger.info(f"VC再接続成功: {channel}")
            except Exception as e:
                logger.error(f"VC再接続失敗: {e}")
    
    # VC許可管理コマンド
    @bot.tree.command(name="vc_allow_user_add", description="VC操作を許可するユーザーを追加")
    @app_commands.describe(member="許可するユーザー")
    async def vc_allow_user_add(interaction: discord.Interaction, member: discord.Member):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        data = vc_allow_storage.load()

        if member.id in data["users"]:
            await interaction.response.send_message("すでに許可されています", ephemeral=True)
            return

        data["users"].append(member.id)
        vc_allow_storage.save(data)

        await interaction.response.send_message(f"{member.mention} を VC操作許可ユーザーに追加しました")
    
    @bot.tree.command(name="vc_allow_user_remove", description="VC操作のユーザー許可を削除")
    @app_commands.describe(member="削除するユーザー")
    async def vc_allow_user_remove(interaction: discord.Interaction, member: discord.Member):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        data = vc_allow_storage.load()

        if member.id not in data["users"]:
            await interaction.response.send_message("許可されていません", ephemeral=True)
            return

        data["users"].remove(member.id)
        vc_allow_storage.save(data)

        await interaction.response.send_message(f"{member.mention} を VC操作許可から削除しました")
    
    @bot.tree.command(name="vc_allow_role_add", description="VC操作を許可するロールを追加")
    @app_commands.describe(role="許可するロール")
    async def vc_allow_role_add(interaction: discord.Interaction, role: discord.Role):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        data = vc_allow_storage.load(interaction.guild.id)

        if role.id in data["roles"]:
            await interaction.response.send_message("すでに許可されています", ephemeral=True)
            return

        data["roles"].append(role.id)
        vc_allow_storage.save(data)

        await interaction.response.send_message(f"ロール **{role.name}** を VC操作許可に追加しました")
    
    @bot.tree.command(name="vc_allow_role_remove", description="VC操作のロール許可を削除")
    @app_commands.describe(role="削除するロール")
    async def vc_allow_role_remove(interaction: discord.Interaction, role: discord.Role):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        data = vc_allow_storage.load()

        if role.id not in data["roles"]:
            await interaction.response.send_message("許可されていません", ephemeral=True)
            return

        data["roles"].remove(role.id)
        vc_allow_storage.save(data)

        await interaction.response.send_message(f"ロール **{role.name}** を VC操作許可から削除しました")
    
    @bot.tree.command(name="vc_allow_list", description="VC操作の許可ユーザー・ロール一覧を表示")
    async def vc_allow_list(interaction: discord.Interaction):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        data = vc_allow_storage.load()
        guild = interaction.guild

        # ユーザー一覧
        user_lines = []
        for uid in data["users"]:
            member = guild.get_member(uid)
            if member:
                user_lines.append(member.mention)
            else:
                user_lines.append(f"`{uid}`（不明）")

        # ロール一覧
        role_lines = []
        for rid in data["roles"]:
            role = guild.get_role(rid)
            if role:
                role_lines.append(role.mention)
            else:
                role_lines.append(f"`{rid}`（不明）")

        user_text = "\n".join(user_lines) if user_lines else "なし"
        role_text = "\n".join(role_lines) if role_lines else "なし"

        embed = discord.Embed(title="VC操作 許可一覧", color=discord.Color.green())
        embed.add_field(name="許可ユーザー", value=user_text, inline=False)
        embed.add_field(name="許可ロール", value=role_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # VC参加・退出コマンド
    @bot.tree.command(name="join", description="VCに参加")
    async def join(interaction: discord.Interaction):
        allow_data = vc_allow_storage.load()
        
        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("このコマンドを使用する権限がありません", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("先にVCへ参加してください")
            return

        if interaction.guild.voice_client:
            await interaction.response.send_message("すでにVCに参加しています")
            return

        channel = interaction.user.voice.channel
        await channel.connect()

        # 監視タスク開始
        bot.loop.create_task(vc_watchdog(interaction.guild.id))

        await interaction.response.send_message(f"「{channel}」に参加しました")
        logger.info(f"/join コマンド実行: {interaction.user} が {channel} に参加")
    
    @bot.tree.command(name="leave", description="VCから退出")
    async def leave(interaction: discord.Interaction):
        allow_data = vc_allow_storage.load()
        
        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("このコマンドを使用する権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("VCに参加していません")
            return
        
        bot.manual_disconnect.add(interaction.guild.id)
        await vc.disconnect()

        await interaction.response.send_message("VCから退出しました")
        logger.info(f"/leave コマンド実行: {interaction.user} が VCから退出")
