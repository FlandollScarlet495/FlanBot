import discord
from discord import app_commands
from services.permission import is_admin_or_dev
from services.storage import vc_allow_storage

def setup_commands(bot):
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