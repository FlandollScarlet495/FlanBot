# bot.py

# リンク https://discord.com/oauth2/authorize?client_id=1463158428435222807&permissions=8&integration_type=0&scope=bot+applications.commands
	
import os
import sys
import random
import subprocess
import threading
import asyncio
import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import pathlib

# ===== 環境変数 =====
env_path = pathlib.Path('.env')
if env_path.exists():
	load_dotenv(env_path)
else:
	load_dotenv()  # Renderなど、環境変数から直接読み込む

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
	raise RuntimeError("DISCORD_TOKEN が環境変数に設定されていません")

# ===== Bot 初期化 =====
intents = discord.Intents.default()

bot = commands.Bot(
	command_prefix="!",
	intents=intents,
	help_command=None
)

MAX_DELETE = 50

# ===== コマンドライン入力処理 =====
def input_handler():
	"""コマンドライン入力を監視"""
	while True:
		try:
			cmd = input().strip().lower()
			
			if cmd == "restart":
				print("ボットを再起動します...")
				asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
				python_executable = sys.executable
				script_path = os.path.abspath(__file__)
				subprocess.Popen([python_executable, script_path])
				break

			elif cmd == "shutdown" or cmd == "stop" or cmd == "exit":
				print("ボットをシャットダウンします...")
				asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
				break

			elif cmd == "help":
				print("\n=== コマンド一覧 ===")
				print("restart                  - ボットを再起動")
				print("shutdown or exit or stop - ボットをシャットダウン")
				print("help                     - このヘルプを表示\n")

		except Exception as e:
			print(f"エラー: {e}")

# ===== 起動処理 =====
@bot.event
async def on_ready():
	print("ゆきのbotが起動しました")

@bot.event
async def setup_hook():
	await bot.tree.sync()

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
@app_commands.checks.has_permissions(administrator=True)
async def restart(interaction: discord.Interaction):
	await interaction.response.send_message("ボットを再起動します...", ephemeral=True)
	await bot.close()
	# 新しいプロセスでボットを再起動
	python_executable = sys.executable
	script_path = os.path.abspath(__file__)
	subprocess.Popen([python_executable, script_path])

# =========================================================
# /shutdown
# =========================================================

@bot.tree.command(name="shutdown", description="ボットをシャットダウン")
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction: discord.Interaction):
	await interaction.response.send_message("ボットをシャットダウンします...", ephemeral=True)
	await bot.close()

# ===== 起動 =====
if __name__ == "__main__":
	# コマンドライン入力処理を別スレッドで実行
	input_thread = threading.Thread(target=input_handler, daemon=True)
	input_thread.start()
	
	print("ボットを起動しました")
	print("コマンド入力で制御できます (help でコマンド一覧表示)\n")

	bot.run(TOKEN)
