"""
ふらんちゃんBot本体

Discord botのメインクラス
各コマンドモジュールをまとめて管理する
"""
import discord
from discord.ext import commands
import sys
import asyncio
import aiosqlite
import os

from .commands.images import images
from .services.logger import logger
from .services.tts import sanitize_text, tts_worker
from .services.storage.tts_settings import TTSSettingsStorage
from .services.storage.init_db import DBInitializer
from .services.voicevox import VoicevoxEngine

# Windows対応
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# コマンドモジュールをインポート
from .commands import help, admin, fun, voices, minecraft_discord

class FlandreBot:
    """ふらんちゃんbotのメインクラス"""
    
    def __init__(self, token: str):
        """
        初期化
        
        Args:
            token: Discord botのトークン
        """
        self.token = token
        
        # Intents設定
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.message_content = True
        
        # Bot作成
        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        self._setup_events()

        self.bot.tts_queues = {}
        self.bot.tts_tasks = {}
        self.bot.manual_disconnect = set()
        self.bot.skip_flags = {}  # ギルドごとのスキップフラグ
        self.bot.playback_queues = {}  # ギルドごとの合成済み再生キュー

    def _setup_events(self):
        """イベントハンドラの登録"""
        
        @self.bot.event
        async def on_ready():
            """Bot起動時の処理"""
            logger.info("ふらんちゃんが起動したよ💗")

        @self.bot.event
        async def setup_hook():
            """Bot初期化時の処理"""
            
            db_path = os.getenv("DB_PATH") or "flandre_bot.db"
            self.bot.db = await aiosqlite.connect(db_path)

            self.bot.db_initializer = DBInitializer(db_path)
            await self.bot.db_initializer.init()
            
            self.bot.tts_settings_storage = TTSSettingsStorage(db_path)
            
            # これを追加
            self.bot.voicevox = VoicevoxEngine()
            self.watchdog_tasks = {}
            self.bot.watchdog_tasks = {}
            self.bot.tts_tasks = {}
            self.bot.tts_queues = {}
            self.bot.manual_disconnect = set()

            self._setup_commands()
            await self.bot.tree.sync()

        @self.bot.event
        async def on_message(message: discord.Message):
            
            if message.author.bot:
                return

            if not message.guild:
                return

            # 発言者がVC参加中か（B）
            if not message.author.voice or not message.author.voice.channel:
                return

            user_vc = message.author.voice.channel

            # ===== A: このチャンネルがVCテキストか判定 =====
            # Discordの仕様上、VCテキストは
            # 「同名のVCが存在するテキストチャンネル」として扱われる

            matching_vc = discord.utils.get(
                message.guild.voice_channels,
                name=message.channel.name
            )

            if not matching_vc:
                return

            # 同名VCがあっても、参加中VCと一致しなければ無効
            if matching_vc.id != user_vc.id:
                return

            gid = message.guild.id
            settings = await self.bot.tts_settings_storage.get(gid)

            if not settings or not settings.get("enabled", False):
                return

            # リプライ情報
            reply_prefix = ""
            if message.reference:
                try:
                    replied_msg = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                    if replied_msg and replied_msg.author:
                        reply_prefix = (
                            f"{replied_msg.author.display_name}さんへのリプライ。"
                        )
                except Exception as e:
                    logger.debug(f"リプライ情報取得エラー: {e}")

            # メッセージ本文取得
            content = message.content or ""

            # サニタイズ
            try:
                sanitized = sanitize_text(content, message.guild)
            except Exception as e:
                logger.debug(f"sanitizeエラー: {e}")
                sanitized = content

            if not sanitized:
                return

            # 80文字制限
            suffix = ""
            if len(sanitized) > 80:
                sanitized = sanitized[:80]
                suffix = "（以下省略）"

            text = reply_prefix + sanitized + suffix

            # TTSキュー初期化
            if gid not in self.bot.tts_queues:
                self.bot.tts_queues[gid] = asyncio.Queue()
                self.bot.tts_tasks[gid] = self.bot.loop.create_task(
                    tts_worker(self.bot, gid)
                )

            await self.bot.tts_queues[gid].put((text, message.author.id))
            logger.debug(f"[Guild {gid}] TTS キューに追加: {text[:5]}...")

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
        voices.setup_commands(self.bot)
        minecraft_discord.setup_commands(self.bot)
    
    def run(self):
        """Botを起動"""
        self.bot.run(self.token)
