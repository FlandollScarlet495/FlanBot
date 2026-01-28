# bot.py
# リンク https://discord.com/oauth2/authorize?client_id=1463158428435222807&permissions=8&integration_type=0&scope=bot+applications.commands
# update

import os
import sys
import random
import subprocess
import json
import threading
import asyncio
import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from hiragana import romaji_to_kana, register_word
from datetime import datetime

# ユーザーごとの変換モード管理
# デフォルトは "hiragana"
user_modes = {}

# ===== VC常駐用 =====
VC_STATE_FILE = "vc_state.json"

VC_RETRY_COUNT = 5       # 最大リトライ回数
VC_RETRY_INTERVAL = 5    # 秒

# ===== 環境変数 =====
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
	raise RuntimeError("DISCORD_TOKEN が .env に設定されていません")

load_dotenv()
_dev = os.getenv("DEVELOPER_ID")
if not _dev:
	raise RuntimeError("DEVELOPER_ID が .env に設定されていません")

DEVELOPER_IDS = { int(_dev) }

# ===== Bot 初期化 =====
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
	command_prefix="!",
	intents=intents,
	help_command=None
)

MAX_DELETE = 50

# ===== 起動処理 =====
@bot.event
async def on_ready():
	print("ふらんちゃんが起動したよ💗")
	await send_system_embed(
		"✅ Bot Online",
		"再起動が完了し、正常に起動しました"
	)
	bot.loop.create_task(restore_voice_connections())

@bot.event
async def setup_hook():
	await bot.tree.sync()

def load_vc_state():
    if not os.path.exists(VC_STATE_FILE):
        return {}
    try:
        with open(VC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"vc_state 読み込み失敗: {e}")
        return {}

def save_vc_state(state: dict):
	with open(VC_STATE_FILE, "w", encoding="utf-8") as f:
		json.dump(state, f, indent=2)

async def restore_voice_connections():
	await bot.wait_until_ready()

	state = load_vc_state()

	for guild_id, info in state.items():
		try:
			guild = bot.get_guild(int(guild_id))
			if not guild:
				continue

			channel = guild.get_channel(info["channel_id"])
			if not channel:
				continue

			if guild.voice_client and guild.voice_client.is_connected():
				continue

			await channel.connect(timeout=10, reconnect=True)
			print(f"VC自動復帰: {guild.name} / {channel.name}")

		except Exception as e:
			print(f"VC自動復帰失敗 ({guild_id}): {e}")

def is_admin_or_dev(interaction: discord.Interaction) -> bool:
	if interaction.user.id in DEVELOPER_IDS:
		return True
	return interaction.user.guild_permissions.administrator

async def find_notify_targets():
	await bot.wait_until_ready()
	results = []

	for guild in bot.guilds:
		vc = guild.voice_client
		text_ch = None
		vc_name = None

		if vc and vc.channel:
			vc_name = vc.channel.name

			if vc.channel.category:
				for ch in vc.channel.category.text_channels:
					if ch.permissions_for(guild.me).send_messages:
						text_ch = ch
						break

		if text_ch is None and guild.system_channel:
			if guild.system_channel.permissions_for(guild.me).send_messages:
				text_ch = guild.system_channel

		if text_ch:
			results.append((guild, text_ch, vc_name))

	return results

async def send_system_embed(title: str, description: str):
	targets = await find_notify_targets()
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	for guild, ch, vc_name in targets:
		embed = discord.Embed(
			title=title,
			description=description,
			color=discord.Color.orange()
		)

		embed.add_field(name="Guild", value=guild.name, inline=False)

		if vc_name:
			embed.add_field(name="VC", value=vc_name, inline=False)

		embed.set_footer(text=f"{now}")

		try:
			await ch.send(embed=embed)
		except Exception as e:
			print(f"通知失敗 ({guild.name}): {e}")

async def ensure_voice_connection(guild_id: int, channel_id: int):
	await bot.wait_until_ready()

	for attempt in range(1, VC_RETRY_COUNT + 1):
		try:
			guild = bot.get_guild(guild_id)
			if not guild:
				return

			channel = guild.get_channel(channel_id)
			if not isinstance(channel, discord.VoiceChannel):
				return

			vc = guild.voice_client
			if vc and vc.is_connected():
				return

			await channel.connect(timeout=10, reconnect=True)
			print(f"[VC再接続成功] {guild.name} / {channel.name}")
			return

		except Exception as e:
			print(f"[VC再接続失敗] ({attempt}/{VC_RETRY_COUNT}) {e}")
			await asyncio.sleep(VC_RETRY_INTERVAL)
			await send_system_embed(
					"⚠ VC再接続失敗",
					f"{guild.name} / {channel.name}"
			)

@bot.event
async def on_voice_state_update(member, before, after):
	if member.id != bot.user.id:
		return

	if before.channel and not after.channel:
		print("VC切断検知。state から再接続します")

		state = load_vc_state()
		info = state.get(str(before.channel.guild.id))
		if not info:
			return

		await ensure_voice_connection(
			before.channel.guild.id,
			info["channel_id"]
		)

# =========================================================
# /thinking
# =========================================================

@bot.tree.context_menu(name="🤔 Thinking")
async def thinking_context(interaction: discord.Interaction, message: discord.Message):
	await interaction.response.defer(ephemeral=True)
		
	try:
		await message.add_reaction("🤔")
		await interaction.followup.send("リアクションを追加しました！", ephemeral=True)
	except discord.Forbidden:
		await interaction.followup.send("リアクションを追加する権限がありません", ephemeral=True)
	except Exception as e:
		await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)

# =========================================================
# /sonanoka
# =========================================================

@bot.tree.command(name="sonanoka", description="そーなのかー")
async def sonanoka(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoka.png")
	)

# =========================================================
# /sonanoda
# =========================================================

@bot.tree.command(name="sonanoda", description="そーなのだー")
async def sonanoda(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("sonanoda.png")
	)

# =========================================================
# /flandre
# =========================================================

@bot.tree.command(name="flandre", description="ふらんちゃん")
async def flandre(interaction: discord.Interaction):
	await interaction.response.send_message(
		file=discord.File("flandre.png")
	)

# =========================================================
# /delete
# =========================================================

@bot.tree.command(name="delete", description="自分とbotのメッセージを削除")
@app_commands.describe(limit="削除件数")
async def delete(interaction: discord.Interaction, limit: int = 1):
	limit = min(limit, MAX_DELETE) + 1

	def check(m: discord.Message):
		return m.author == interaction.user or m.author == bot.user

	if isinstance(interaction.channel, discord.TextChannel):
		await interaction.channel.purge(limit=limit, check=check)

	await interaction.response.defer(ephemeral=True)

# =========================================================
# /admin_del
# =========================================================

@bot.tree.command(name="admin_del", description="管理者専用削除")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(limit="削除件数")
async def admin_del(interaction: discord.Interaction, limit: int = 5):
	limit = min(limit, MAX_DELETE) + 1

	if isinstance(interaction.channel, discord.TextChannel):
		await interaction.channel.purge(limit=limit)

	await interaction.response.defer(ephemeral=True)

# =========================================================
# /join
# =========================================================

@bot.tree.command(name="join", description="自分が入っているVCにBotを参加させます")
async def join_vc(interaction: discord.Interaction):
	await interaction.response.defer(ephemeral=True)

	if not interaction.user.voice or not interaction.user.voice.channel:
		await interaction.followup.send(
			"先にボイスチャンネルに参加してください",
			ephemeral=True
		)
		return

	channel = interaction.user.voice.channel
	guild = interaction.guild

	try:
		if guild.voice_client:
			await guild.voice_client.move_to(channel)
		else:
			await channel.connect(timeout=10, reconnect=True)

		await interaction.followup.send(
			f"VC **{channel.name}** に参加しました",
			ephemeral=True
		)

	except Exception as e:
		await interaction.followup.send(
			f"VC参加に失敗しました: {e}",
			ephemeral=True
		)

	state = load_vc_state()
	state[str(guild.id)] = {
		"channel_id": channel.id
	}
	save_vc_state(state)

# =========================================================
# /leave
# =========================================================

@bot.tree.command(name="leave", description="BotをVCから退出させます")
async def leave_vc(interaction: discord.Interaction):
	await interaction.response.defer(ephemeral=True)

	vc = interaction.guild.voice_client
	if not vc or not vc.is_connected():
		await interaction.followup.send(
			"BotはVCに参加していません。",
			ephemeral=True
		)
		return

	try:
		await vc.disconnect()
	except Exception as e:
		await interaction.followup.send(
			f"VC切断中にエラーが発生しました: {e}",
			ephemeral=True
		)
		return

	state = load_vc_state()
	state.pop(str(interaction.guild.id), None)
	save_vc_state(state)

	await interaction.followup.send(
		"VCから退出しました。",
		ephemeral=True
	)

# =========================================================
# /help
# =========================================================

@bot.tree.command(name="help", description="ヘルプを表示")
async def help_cmd(interaction: discord.Interaction):
	embed = discord.Embed(
		title="ふらんちゃんbot コマンド一覧",
		color=discord.Color.blue()
	)
	embed.add_field(name="アプリ(thinking)", value="返信先に🤔リアクション", inline=False)
	embed.add_field(name="/sonanoka", value="そーなのかー画像", inline=False)
	embed.add_field(name="/sonanoda", value="そーなのだー画像", inline=False)
	embed.add_field(name="/flandre", value="ふらんちゃん画像", inline=False)
	embed.add_field(name="/dice", value="サイコロを振る (sides, times 指定可)", inline=False)
	embed.add_field(name="/delete", value="自分＋bot削除", inline=False)
	embed.add_field(name="/admin_del", value="管理者専用削除", inline=False)
	embed.add_field(name="/ping", value="動作確認", inline=False)
	embed.add_field(name="/restart", value="ボット再起動（管理者のみ）", inline=False)
	embed.add_field(name="/shutdown", value="ボットシャットダウン（管理者のみ）", inline=False)
	embed.add_field(name="/join", value="入っているVCにBotを参加させる", inline=False)
	embed.add_field(name="/leave", value="BotをVCから退出させる", inline=False)

	await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================================================
# /dice
# =========================================================

@bot.tree.command(name="dice", description="サイコロを振る")
@app_commands.describe(
	sides="サイコロの面数（デフォルト:6）",
	times="振る回数（デフォルト:1）"
)
async def dice(interaction: discord.Interaction, sides: int = 6, times: int = 1):
	# 入力値の検証
	if sides < 2:
		await interaction.response.send_message("面数は2以上である必要があります", ephemeral=True)
		return
	
	if times < 1 or times > 100:
		await interaction.response.send_message("振る回数は1～100の範囲で指定してください", ephemeral=True)
		return
	
	# サイコロを振る
	results = [random.randint(1, sides) for _ in range(times)]
	total = sum(results)
	
	# 結果を表示
	embed = discord.Embed(
		title=f"🎲 {times}回のD{sides}",
		color=discord.Color.green()
	)
	
	if times == 1:
		embed.description = f"**結果: {results[0]}**"
	else:
		results_str = ", ".join(map(str, results))
		embed.add_field(name="各結果", value=results_str, inline=False)
		embed.add_field(name="合計", value=f"**{total}**", inline=False)
	
	embed.set_footer(text=f"実行者: {interaction.user.name}")
	
	await interaction.response.send_message(embed=embed)

# =========================================================
# /test
# =========================================================

@bot.tree.command(name="test", description="動作確認")
async def test(interaction: discord.Interaction):
	await interaction.response.send_message("pong!")
 
# =========================================================
# /ping
# =========================================================

@bot.tree.command(name="ping", description="動作確認（通信速度）")
async def ping(interaction: discord.Interaction):
	latency_ms = bot.latency * 1000
	embed = discord.Embed(
		title="🏓 Ping",
		description=f"**{latency_ms:.0f}ms**",
		color=discord.Color.blue()
	)
	embed.set_footer(text=f"実行者: {interaction.user.name}")
	await interaction.response.send_message(embed=embed)

# =========================================================
# /restart
# =========================================================

@bot.tree.command(name="restart", description="ボットを再起動")
@app_commands.check(is_admin_or_dev)
async def restart(interaction):
	await interaction.response.send_message("ボットを再起動します...")
	python_executable = sys.executable
	script_path = os.path.abspath(__file__)
	subprocess.Popen([python_executable, script_path])
	await bot.close()

# =========================================================
# /shutdown
# =========================================================

@bot.tree.command(name="shutdown", description="ボットをシャットダウン")
@app_commands.check(is_admin_or_dev)
async def shutdown(interaction: discord.Interaction):
	await interaction.response.send_message(
		"ボットをシャットダウンします..."
	)
	await bot.close()

# =========================================================
# /mode
# =========================================================

@bot.tree.command(
	name="mode",
	description="ローマ字→かな変換モードを設定します"
)
@app_commands.describe(
	mode="hiragana / katakana / nasi"
)
@app_commands.choices(
	mode=[
		app_commands.Choice(name="ひらがな", value="hiragana"),
		app_commands.Choice(name="カタカナ", value="katakana"),
		app_commands.Choice(name="変換なし", value="nasi"),
	]
)
async def mode_cmd(
	interaction: discord.Interaction,
	mode: app_commands.Choice[str]
):
	user_modes[interaction.user.id] = mode.value

	await interaction.response.send_message(
		f"変換モードを **{mode.value}** に設定しました",
		ephemeral=True
	)

@bot.event
async def on_message(message: discord.Message):
	if message.author.bot:
		return

	mode = user_modes.get(message.author.id, "hiragana")
	if mode == "nasi":
		return

	try:
		converted = romaji_to_kana(message.content, mode)
		register_word(message.content)

		if converted != message.content:
			await message.channel.send(converted)

	except Exception as e:
		print(f"変換エラー: {e}")

	await bot.process_commands(message)

# =========================================================
# ================= コマンドライン入力処理 ==================
# =========================================================

def input_handler():
	"""コマンドライン入力を監視"""
	while True:
		try:
			cmd = input().strip().lower()
			
			if cmd == "restart":
				print("ボットを再起動します...")
				asyncio.run_coroutine_threadsafe(
					send_system_embed(
						"🔄 Bot Restart",
						"コンソール操作により再起動します"
					),
					bot.loop
				)
				python_executable = sys.executable
				script_path = os.path.abspath(__file__)
				asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
				subprocess.Popen([python_executable, script_path])
				break

			elif cmd in ("shutdown", "stop", "exit"):
					print("ボットをシャットダウンします...")
					asyncio.run_coroutine_threadsafe(
							send_system_embed(
									"⛔ Bot Shutdown",
									"コンソール操作によりシャットダウンします"
							),
							bot.loop
					)
					asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
					break

			elif cmd == "help":
				print("\n=== コマンド一覧 ===")
				print("restart                  - ボットを再起動")
				print("shutdown or exit or stop - ボットをシャットダウン")
				print("help                     - このヘルプを表示\n")

		except Exception as e:
			print(f"エラー: {e}")

@restart.error
@shutdown.error
async def admin_or_dev_error(interaction: discord.Interaction, error):
	if isinstance(error, app_commands.CheckFailure):
		await interaction.response.send_message(
			"このコマンドは管理者または開発者のみ実行できます。",
			ephemeral=True
		)

# ================
# ===== 起動 =====
# ================
if __name__ == "__main__":
	# コマンドライン入力処理を別スレッドで実行
	input_thread = threading.Thread(target=input_handler, daemon=True)
	input_thread.start()
	
	print("ボットを起動しました")
	print("コマンド入力で制御できます (help でコマンド一覧表示)\n")

	bot.run(TOKEN)
