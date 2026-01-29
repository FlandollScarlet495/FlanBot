# bot.py

import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime
if sys.platform == "win32":
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 環境変数

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID"))

if not TOKEN:
	raise RuntimeError("DISCORD_TOKEN が未設定です")
if not DEVELOPER_ID:
	raise RuntimeError("DEVELOPER_ID が未設定です")

# Bot設定

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(
	command_prefix="!",
	intents=intents,
	help_command=None
)

bot.manual_disconnect = set()
VC_STATE_FILE = "vc_state.json"
MAX_DELETE = 50

# 共通関数

def is_admin_or_dev(interaction: discord.Interaction) -> bool:
	return (
		interaction.user.id == DEVELOPER_ID
		or interaction.user.guild_permissions.administrator
	)

def load_vc_state():
	if not os.path.exists(VC_STATE_FILE):
		return {}
	with open(VC_STATE_FILE, "r", encoding="utf-8") as f:
		return json.load(f)

def save_vc_state(state: dict):
	with open(VC_STATE_FILE, "w", encoding="utf-8") as f:
		json.dump(state, f, indent=2, ensure_ascii=False)

async def vc_watchdog(guild_id: int, channel: discord.VoiceChannel):
	while True:
		await asyncio.sleep(3)

		guild = bot.get_guild(guild_id)
		if not guild:
			return

		vc = guild.voice_client

		# 手動切断なら監視終了
		if guild_id in bot.manual_disconnect:
			bot.manual_disconnect.remove(guild_id)
			return

		# 切断されていたら再接続
		if not vc or not vc.is_connected():
			try:
				await channel.connect()
			except Exception as e:
				print(f"再接続失敗: {e}")
			return

# 起動

@bot.event
async def on_ready():
		# 現在時刻（ミリ秒なし）
		no_ms = datetime.now().replace(microsecond=0)
		# この行だけ出力
		print(f"{no_ms} ふらんちゃんが起動したよ💗")


@bot.event
async def setup_hook():
	await bot.tree.sync()

# /help
@bot.tree.command(name="help", description="ヘルプを表示")
async def help_cmd(interaction: discord.Interaction):
	embed = discord.Embed(
		title="ふらんちゃんbot コマンド一覧",
		color=discord.Color.blue()
	)
	embed.add_field(name="アプリ(thinking)", value="返信先に🤔リアクション (準備中)", inline=False)
	embed.add_field(name="/sonanoka", value="そーなのかー画像表示", inline=False)
	embed.add_field(name="/sonanoda", value="そーなのだー画像表示", inline=False)
	embed.add_field(name="/flandre", value="ふらんちゃん画像表示", inline=False)
	embed.add_field(name="/dice", value="サイコロを振る (準備中)", inline=False)
	embed.add_field(name="/delete", value="自分＋bot削除", inline=False)
	embed.add_field(name="/admin_del", value="管理者専用削除", inline=False)
	embed.add_field(name="/test", value="テスト", inline=False)
	embed.add_field(name="/ping", value="動作速度確認", inline=False)
	embed.add_field(name="/about", value="動作確認", inline=False)
	embed.add_field(name="/join", value="VC参加", inline=False)
	embed.add_field(name="/leave", value="VC退出", inline=False)

	await interaction.response.send_message(embed=embed)

# 画像コマンド

# /sonanoka
@bot.tree.command(name="sonanoka", description="そーなのかー")
async def sonanoka(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoka.png")
	)

# /sonanoda
@bot.tree.command(name="sonanoda", description="そーなのだー")
async def sonanoda(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoda.png")
	)

# /flandre
@bot.tree.command(name="flandre", description="ふらんちゃん")
async def flandre(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("flandre.png")
	)

# 削除系コマンド

# /delete
@bot.tree.command(name="delete", description="自分とBotのメッセージを削除")
@app_commands.describe(count="削除する件数（最大50）")
async def delete(interaction: discord.Interaction, count: int):
	if count < 1:
		await interaction.response.send_message(
			"1以上を指定してください",
			ephemeral=True
		)
		return

	count = min(count, MAX_DELETE)

	await interaction.response.defer(ephemeral=True)

	def check(msg: discord.Message):
		return (
			msg.author.id == interaction.user.id
			or msg.author.bot
		)

	deleted = await interaction.channel.purge(
		limit=count,
		check=check
	)

	await interaction.followup.send(
		f"{len(deleted)} 件のメッセージを削除しました",
	)
 
# /admin_del
class AdminDeleteConfirm(discord.ui.View):
	def __init__(self, interaction: discord.Interaction, count: int):
		super().__init__(timeout=30)
		self.interaction = interaction
		self.count = count

	async def on_timeout(self):
		# タイムアウト時にメッセージ更新（interactionが残っていれば）
		try:
			await self.interaction.edit_original_response(
				content="操作がタイムアウトしました",
				view=None
			)
		except Exception:
			pass  # interaction が期限切れでも安全

	@discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
	async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id != self.interaction.user.id:
			await interaction.response.send_message(
				"操作できません", ephemeral=True
			)
			return

		deleted = await interaction.channel.purge(limit=self.count)

		try:
			if interaction.response.is_done():
				await interaction.followup.send(
					f"{len(deleted)} 件のメッセージを削除しました",
					ephemeral=True
				)
			else:
				await interaction.response.edit_message(
					content=f"{len(deleted)} 件のメッセージを削除しました",
					view=None
				)
		except discord.NotFound:
			pass  # 安全に握りつぶす

		self.stop()

	@discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
	async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id != self.interaction.user.id:
			await interaction.response.send_message(
				"操作できません", ephemeral=True
			)
			return

		try:
			if interaction.response.is_done():
				await interaction.followup.send("キャンセルしました", ephemeral=True)
			else:
				await interaction.response.edit_message(
					content="キャンセルしました",
					view=None
				)
		except discord.NotFound:
			pass

		self.stop()

@bot.tree.command(name="admin_del", description="管理者専用メッセージ削除")
@app_commands.describe(count="削除する件数（最大50）")
async def admin_del(interaction: discord.Interaction, count: int):
	if not is_admin_or_dev(interaction):
		await interaction.response.send_message(
			"権限がありません", ephemeral=True
		)
		return

	if count < 1:
		await interaction.response.send_message(
			"1以上を指定してください", ephemeral=True
		)
		return

	count = min(count, MAX_DELETE)

	view = AdminDeleteConfirm(interaction, count)

	await interaction.response.send_message(
		f"本当に **{count} 件** のメッセージを削除しますか？",
		view=view,
		ephemeral=True
	)

# 動作確認コマンド

# /test
@bot.tree.command(name="test", description="テスト")
async def test(interaction: discord.Interaction):
	await interaction.response.send_message(
		"Hello World!"
	)

# /ping
@bot.tree.command(name="ping", description="動作速度確認")
async def ping(interaction: discord.Interaction):
	await interaction.response.send_message(
		f"🏓 {round(bot.latency * 1000)}ms"
	)

# /about
@bot.tree.command(name="about", description="動作確認")
async def about(interaction: discord.Interaction):
	await interaction.response.send_message(
		"flandre, ふらんちゃん"
	)

# ボイスチャットコマンド

# /join
@bot.tree.command(name="join", description="VCに参加")
async def join(interaction: discord.Interaction):
	if not interaction.user.voice or not interaction.user.voice.channel:
		await interaction.response.send_message("先にVCへ参加してください")
		return

	channel = interaction.user.voice.channel

	if interaction.guild.voice_client:
		await interaction.response.send_message("すでにVCに参加しています")
		return

	await channel.connect()

	# 監視タスク開始
	bot.loop.create_task(
		vc_watchdog(interaction.guild.id, channel)
	)

	await interaction.response.send_message(f"「{channel}」に参加しました")

# /leave
@bot.tree.command(name="leave", description="VCから退出")
async def leave(interaction: discord.Interaction):
	vc = interaction.guild.voice_client
	
	if not vc:
		await interaction.response.send_message("VCに参加していません")
		return
	
	bot.manual_disconnect.add(interaction.guild.id)

	await vc.disconnect()
	await interaction.response.send_message("VCから退出しました")

bot.run(TOKEN)
