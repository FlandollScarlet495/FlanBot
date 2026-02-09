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

            if guild_id in bot.manual_disconnect:
                bot.manual_disconnect.remove(guild_id)
                logger.info("手動切断、監視終了")
                return

            vc = guild.voice_client
            if vc and vc.is_connected():
                continue

            channel = None
            for member in guild.members:
                if member.voice and member.voice.channel:
                    channel = member.voice.channel
                    break

            if not channel:
                continue

            try:
                await channel.connect()
                logger.info(f"VC再接続成功: {channel}")
            except Exception as e:
                logger.error(f"VC再接続失敗: {e}")
    
    # =====================
    # VC許可管理（管理者）
    # =====================

    @bot.tree.command(name="vc_allow_user_add")
    async def vc_allow_user_add(interaction: discord.Interaction, member: discord.Member):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        data = vc_allow_storage.load(gid)

        if member.id in data["users"]:
            await interaction.followup.send("すでに許可されています", ephemeral=True)
            return

        data["users"].append(member.id)
        vc_allow_storage.save(gid, data)

        await interaction.followup.send(
            f"{member.mention} を VC操作許可ユーザーに追加しました",
            ephemeral=True
        )

    @bot.tree.command(name="vc_allow_user_remove")
    async def vc_allow_user_remove(interaction: discord.Interaction, member: discord.Member):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        data = vc_allow_storage.load(gid)

        if member.id not in data["users"]:
            await interaction.followup.send("許可されていません", ephemeral=True)
            return

        data["users"].remove(member.id)
        vc_allow_storage.save(gid, data)

        await interaction.followup.send(
            f"{member.mention} を VC操作許可から削除しました",
            ephemeral=True
        )

    @bot.tree.command(name="vc_allow_role_add")
    async def vc_allow_role_add(interaction: discord.Interaction, role: discord.Role):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        data = vc_allow_storage.load(gid)

        if role.id in data["roles"]:
            await interaction.followup.send("すでに許可されています", ephemeral=True)
            return

        data["roles"].append(role.id)
        vc_allow_storage.save(gid, data)

        await interaction.followup.send(
            f"ロール **{role.name}** を VC操作許可に追加しました",
            ephemeral=True
        )

    @bot.tree.command(name="vc_allow_role_remove")
    async def vc_allow_role_remove(interaction: discord.Interaction, role: discord.Role):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        data = vc_allow_storage.load(gid)

        if role.id not in data["roles"]:
            await interaction.followup.send("許可されていません", ephemeral=True)
            return

        data["roles"].remove(role.id)
        vc_allow_storage.save(gid, data)

        await interaction.followup.send(
            f"ロール **{role.name}** を VC操作許可から削除しました",
            ephemeral=True
        )

    @bot.tree.command(name="vc_allow_list")
    async def vc_allow_list(interaction: discord.Interaction):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        gid = interaction.guild.id
        data = vc_allow_storage.load(gid)
        guild = interaction.guild

        users = [
            guild.get_member(uid).mention
            if guild.get_member(uid) else f"`{uid}`"
            for uid in data["users"]
        ] or ["なし"]

        roles = [
            guild.get_role(rid).mention
            if guild.get_role(rid) else f"`{rid}`"
            for rid in data["roles"]
        ] or ["なし"]

        embed = discord.Embed(title="VC操作 許可一覧")
        embed.add_field(name="ユーザー", value="\n".join(users), inline=False)
        embed.add_field(name="ロール", value="\n".join(roles), inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # =====================
    # VC参加 / 退出
    # =====================

    @bot.tree.command(name="join")
    async def join(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("先にVCへ参加してください")
            return

        if interaction.guild.voice_client:
            await interaction.response.send_message("すでにVCに参加しています")
            return

        channel = interaction.user.voice.channel
        await channel.connect()

        bot.loop.create_task(vc_watchdog(gid))
        vc_allow_storage.set_tts_enabled(gid, True)

        await interaction.response.send_message(f"「{channel}」に参加しました")
        logger.info(f"/join: {interaction.user} joined {channel}")

    @bot.tree.command(name="leave")
    async def leave(interaction: discord.Interaction):
        gid = interaction.guild.id
        allow_data = vc_allow_storage.load(gid)

        if not can_use_vc(interaction, allow_data):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("VCに参加していません")
            return

        vc_allow_storage.set_tts_enabled(gid, False)

        if gid in bot.tts_tasks:
            bot.tts_tasks[gid].cancel()
            del bot.tts_tasks[gid]
            del bot.tts_queues[gid]

        bot.manual_disconnect.add(gid)
        await vc.disconnect()

        await interaction.response.send_message("VCから退出しました")
        logger.info(f"/leave: {interaction.user} left VC")
