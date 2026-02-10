"""
管理系コマンド

/give_role, /remove_role, /admin_del などの管理者専用コマンド
"""
import discord
from discord import app_commands
from services.permission import is_admin_or_dev
from services.logger import logger
from config import MAX_DELETE


def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    @bot.tree.command(name="give_role", description="指定したユーザーにロールを付与")
    @app_commands.describe(member="ロールを付与するユーザー", role="付与するロール")
    async def give_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        # 権限チェック
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        guild = interaction.guild
        bot_member = guild.me

        # Botの権限チェック
        if not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message("Botにロール管理権限がありません", ephemeral=True)
            return

        # 既に持っているかチェック
        if role in member.roles:
            await interaction.response.send_message(
                f"{member.mention} はすでに {role.name} を持っています", 
                ephemeral=True
            )
            return

        # ロール階層チェック
        if role >= bot_member.top_role:
            await interaction.response.send_message(
                "Botのロール階層が低すぎて、このロールは付与できません", 
                ephemeral=True
            )
            return

        # ロール付与
        try:
            await member.add_roles(role, reason=f"give_role by {interaction.user}")
            await interaction.response.send_message(f"{member.mention} に **{role.name}** を付与しました")
        except discord.Forbidden:
            await interaction.response.send_message("権限不足でロールを付与できません", ephemeral=True)
        except Exception as e:
            logger.error(f"give_role エラー: {e}")
            await interaction.response.send_message("エラーが発生しました", ephemeral=True)
    
    @bot.tree.command(name="remove_role", description="指定したユーザーからロールを剥奪")
    @app_commands.describe(member="ロールを剥奪するユーザー", role="剥奪するロール")
    async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        # 権限チェック
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        guild = interaction.guild
        bot_member = guild.me

        # Botの権限チェック
        if not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message("Botにロール管理権限がありません", ephemeral=True)
            return

        # 持っていないかチェック
        if role not in member.roles:
            await interaction.response.send_message(
                f"{member.mention} は {role.name} を持っていません", 
                ephemeral=True
            )
            return

        # ロール階層チェック
        if role >= bot_member.top_role:
            await interaction.response.send_message(
                "Botのロール階層が低すぎて、このロールは剥奪できません", 
                ephemeral=True
            )
            return

        # ロール剥奪
        try:
            await member.remove_roles(role, reason=f"remove_role by {interaction.user}")
            await interaction.response.send_message(f"{member.mention} から **{role.name}** を剥奪しました")
        except discord.Forbidden:
            await interaction.response.send_message("権限不足でロールを剥奪できません", ephemeral=True)
        except Exception as e:
            logger.error(f"remove_role エラー: {e}")
            await interaction.response.send_message("エラーが発生しました", ephemeral=True)
    
    @bot.tree.command(name="delete", description="自分とBotのメッセージを削除")
    @app_commands.describe(count="削除する件数（最大50）")
    async def delete(interaction: discord.Interaction, count: int):
        if count < 1:
            await interaction.response.send_message("1以上を指定してください", ephemeral=True)
            return

        count = min(count, MAX_DELETE)

        await interaction.response.defer(ephemeral=True)

        def check(msg: discord.Message):
            return (msg.author.id == interaction.user.id or msg.author.bot)

        deleted = await interaction.channel.purge(limit=count, check=check)

        await interaction.followup.send(f"{len(deleted)} 件のメッセージを削除しました")
        logger.info(f"/delete コマンド実行: {interaction.user} ({len(deleted)}件削除)")
    
    # admin_del用のViewクラス
    class AdminDeleteConfirm(discord.ui.View):
        def __init__(self, interaction: discord.Interaction, count: int):
            super().__init__(timeout=30)
            self.interaction = interaction
            self.count = count

        async def on_timeout(self):
            try:
                await self.interaction.edit_original_response(content="操作がタイムアウトしました", view=None)
            except Exception:
                pass

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
        async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.interaction.user.id:
                await interaction.response.send_message("操作できません", ephemeral=True)
                return

            deleted = await interaction.channel.purge(limit=self.count)

            try:
                if interaction.response.is_done():
                    await interaction.followup.send(f"{len(deleted)} 件のメッセージを削除しました", ephemeral=True)
                else:
                    await interaction.response.edit_message(content=f"{len(deleted)} 件のメッセージを削除しました", view=None)
            except discord.NotFound:
                pass

            self.stop()

        @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
        async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.interaction.user.id:
                await interaction.response.send_message("操作できません", ephemeral=True)
                return

            try:
                if interaction.response.is_done():
                    await interaction.followup.send("キャンセルしました", ephemeral=True)
                else:
                    await interaction.response.edit_message(content="キャンセルしました", view=None)
            except discord.NotFound:
                pass

            self.stop()
    
    @bot.tree.command(name="admin_del", description="管理者専用メッセージ削除")
    @app_commands.describe(count="削除する件数（最大50）")
    async def admin_del(interaction: discord.Interaction, count: int):
        if not is_admin_or_dev(interaction):
            await interaction.response.send_message("権限がありません", ephemeral=True)
            return

        if count < 1:
            await interaction.response.send_message("1以上を指定してください", ephemeral=True)
            return

        count = min(count, MAX_DELETE)

        view = AdminDeleteConfirm(interaction, count)

        await interaction.response.send_message(
            f"本当に **{count} 件** のメッセージを削除しますか？", 
            view=view, 
            ephemeral=True
        )
        logger.info(f"/admin_del コマンド実行: {interaction.user} ({count}件削除予定)")
