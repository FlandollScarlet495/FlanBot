# bot.py

import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
import sys
import random
import re
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
	embed.add_field(name="thinking(アプリ)", value="返信先に🤔リアクション", inline=False)
	embed.add_field(name="/sonanoka", value="そーなのかー画像表示", inline=False)
	embed.add_field(name="/sonanoda", value="そーなのだー画像表示", inline=False)
	embed.add_field(name="/flandre", value="ふらんちゃん画像表示", inline=False)
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

# アプリ

# thinking
@bot.tree.context_menu(name="🤔 thinking")
async def thinking(interaction: discord.Interaction, message: discord.Message):
	try:
		await message.add_reaction("🤔")
		await interaction.response.send_message(
			"🤔 を付けました",
			ephemeral=True
		)
		print("thinking(アプリ)が実行されました、thinkingを付けれました")
	except discord.Forbidden:
		await interaction.response.send_message(
			"リアクションを付ける権限がありません",
			ephemeral=True
		)
		print("thinking(アプリ)が実行されました、リアクションをつける権限がありませんでした")
	except Exception as e:
		await interaction.response.send_message(
			"エラーが発生しました",
			ephemeral=True
		)
		print("thinking(アプリ)で実行する前にエラーが発生しました")

# コマンド

# 画像コマンド

# /sonanoka
@bot.tree.command(name="sonanoka", description="そーなのかー")
async def sonanoka(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoka.png")
	)
	print("/sonanokaが実行されました")

# /sonanoda
@bot.tree.command(name="sonanoda", description="そーなのだー")
async def sonanoda(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoda.png")
	)
	print("/sonanodaが実行されました")

# /flandre
@bot.tree.command(name="flandre", description="ふらんちゃん")
async def flandre(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("flandre.png")
	)
	print("/flandreが実行されました")

# 遊ぶ系コマンド

# /dice
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

	n = int(m.group(1))                     # 個数
	sides = int(m.group(2))                 # 面数
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
		f"🎲 `{n}d{sides}{mod_text}`{flag_text}\n"
		f"出目: {rolls}\n"
		f"合計: **{total}**"
	)
	print("/diceが実行されました")

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
	print("/deleteが実行されました")
 
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
	print("/admin_delが実行されました")

# 動作確認コマンド

# /test
@bot.tree.command(name="test", description="テスト")
async def test(interaction: discord.Interaction):
	await interaction.response.send_message(
		"test"
	)
	print("/testが実行されました")

# /ping
@bot.tree.command(name="ping", description="動作速度確認")
async def ping(interaction: discord.Interaction):
	await interaction.response.send_message(
		f"🏓 {round(bot.latency * 1000)}ms"
	)
	print("/pingが実行されました")

# /about
@bot.tree.command(name="about", description="動作確認")
async def about(interaction: discord.Interaction):
	await interaction.response.send_message(
		"flandre, ふらんちゃん"
	)
	print("/aboutが実行されました")

# ボイスチャットコマンド

async def vc_watchdog(guild_id: int):
	while True:
		await asyncio.sleep(3)

		guild = bot.get_guild(guild_id)
		if not guild:
			return

		# /leave のときだけ終了
		if guild_id in bot.manual_disconnect:
			bot.manual_disconnect.remove(guild_id)
			print("手動切断、監視終了")
			return

		vc = guild.voice_client

		# まだ接続中 or 接続試行中なら何もしない
		if vc and vc.is_connected():
			continue

		# 再接続先は「最後に人がいるVC」
		channel = None
		for member in guild.members:
			if member.voice and member.voice.channel:
				channel = member.voice.channel
				break

		if not channel:
			continue  # 接続先が無いなら待つ

		try:
			await channel.connect()
			print(f"VC再接続成功: {channel}")
		except Exception as e:
			print(f"VC再接続失敗: {e}")

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

	# 監視タスク開始（guild_id のみ渡す）
	bot.loop.create_task(
		vc_watchdog(interaction.guild.id)
	)

	await interaction.response.send_message(f"「{channel}」に参加しました")
	print("/joinが実行されました、VCから参加しました")

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
	print("/leaveが実行されました、VCから退出しました")

bot.run(TOKEN)
