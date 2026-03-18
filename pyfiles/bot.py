"""
ふらんちゃんBot本体
"""
import discord
from discord.ext import commands
import sys
import asyncio
import aiosqlite
import os

from .services.logger import logger
from .services.tts import sanitize_text, tts_worker
from .services.storage.tts_settings import TTSSettingsStorage
from .services.storage.init_db import DBInitializer
from .services.voicevox import VoicevoxEngine

# Windows対応
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# コマンドモジュールをインポート
# お姉様の言う通り、ここには voice.py だけあればOK！
from .commands import help, admin, fun, voice, minecraft_discord
from .commands.images import images
from . import config


class FlandreBot:
    def __init__(self, token: str):
        self.token = token
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.message_content = True

        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self._setup_events()

    def _setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info("ふらんちゃんが起動したよ💗")

        @self.bot.event
        async def setup_hook():
            db_path = config.DB_PATH
            self.bot.db = await aiosqlite.connect(db_path)

            # --- DBの初期化 ---
            self.bot.db_initializer = DBInitializer(db_path)
            await self.bot.db_initializer.init()

            # 2. TTS設定用ストレージの初期化（ここを追加！）
            self.bot.tts_settings_storage = TTSSettingsStorage(db_path)
            await self.bot.tts_settings_storage.init_db() # これでテーブルが作られるわ！

            # --- Voicevoxエンジンの準備 ---
            self.bot.voicevox = VoicevoxEngine()
            await self.bot.voicevox.initialize() # これを忘れると話者リストが空になっちゃうの！
            logger.info("Voicevoxの話者リストを取得したよ！")

            self.bot.watchdog_tasks = {}
            self.bot.tts_tasks = {}
            self.bot.tts_queues = {}

            self._setup_commands()
            await self.bot.tree.sync()

        @self.bot.event
        async def on_message(message: discord.Message):
            # 1. Bot自身の発言やDMは無視
            if message.author.bot or not message.guild:
                return

            # 2. 接頭辞（!）で始まる場合は読み上げずにコマンドとして処理
            if message.content.startswith('!'):
                await self.bot.process_commands(message)
                return

            # 3. 発言者がVCに参加しているかチェック
            if not message.author.voice or not message.author.voice.channel:
                await self.bot.process_commands(message)
                return

            user_vc = message.author.voice.channel

            # 4. メッセージ送信先がVCテキストチャンネルか判定
            matching_vc = discord.utils.get(
                message.guild.voice_channels,
                name=message.channel.name
            )

            if not matching_vc or matching_vc.id != user_vc.id:
                await self.bot.process_commands(message)
                return

            # 5. サーバー設定で読み上げが有効か確認
            gid = message.guild.id
            settings = await self.bot.tts_settings_storage.get(gid)
            if not settings or not settings.get("enabled", False):
                await self.bot.process_commands(message)
                return

            # --- 読み上げテキストの構築 ---
            reply_prefix = ""
            if message.reference:
                try:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg and replied_msg.author:
                        reply_prefix = f"{replied_msg.author.display_name}さんへのリプライ。"
                except Exception:
                    pass

            content = message.content or ""
            try:
                sanitized = sanitize_text(content, message.guild)
            except Exception:
                sanitized = content

            if not sanitized:
                await self.bot.process_commands(message)
                return

            suffix = "（以下省略）" if len(sanitized) > 80 else ""
            text = reply_prefix + sanitized[:80] + suffix

            # 6. TTSキューへ追加
            if gid not in self.bot.tts_queues:
                self.bot.tts_queues[gid] = asyncio.Queue()
                self.bot.tts_tasks[gid] = self.bot.loop.create_task(
                    tts_worker(self.bot, gid)
                )

            await self.bot.tts_queues[gid].put((text, message.author.id))

            # 最後にコマンドも処理できるようにするわ
            await self.bot.process_commands(message)

        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """ユーザーの VC 参加/退出を監視して読み上げる

            Bot が接続しているボイスチャンネルに誰かが入った／出たとき、
            `○○さんが接続しました` / `○○さんが退出しました` を読み上げます。
            """
            # bot 自身とボットは無視
            if member.bot or not member.guild:
                return

            vc = member.guild.voice_client
            if not vc or not vc.is_connected() or not vc.channel:
                return

            bot_chan = vc.channel

            # 参加: before が bot_chan ではなく after が bot_chan
            joined = (before.channel != bot_chan) and (after.channel == bot_chan)
            # 退出: before が bot_chan で after が bot_chan ではない
            left = (before.channel == bot_chan) and (after.channel != bot_chan)

            if not (joined or left):
                return

            gid = member.guild.id
            settings = await self.bot.tts_settings_storage.get(gid)
            if not settings["enabled"]:
                return

            if joined:
                text = f"{member.display_name}さんが接続しました"
            else:
                text = f"{member.display_name}さんが退出しました"

            # キューとワーカーを確保して enqueue
            if gid not in self.bot.tts_queues:
                self.bot.tts_queues[gid] = asyncio.Queue()
                self.bot.tts_tasks[gid] = self.bot.loop.create_task(
                    tts_worker(self.bot, gid)
                )

            await self.bot.tts_queues[gid].put((text, member.id))
            logger.info(f"[Guild {gid}] VC イベント読み上げキュー追加: {text}")

    def _setup_commands(self):
        """各モジュールのコマンドを登録"""
        help.setup_commands(self.bot)
        admin.setup_commands(self.bot)
        images.setup_commands(self.bot)
        fun.setup_commands(self.bot)
        minecraft_discord.setup_commands(self.bot)

        # ここで voice.py (commands/voice.py) を呼び出す！
        # これが voices/setvoice.py まで繋いでくれるんだね。
        voice.setup_commands(self.bot)

    def run(self):
        self.bot.run(self.token)
