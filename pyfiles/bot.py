"""
ふらんちゃんBot本体

Discord botのメインクラス
各コマンドモジュールをまとめて管理する
"""
import discord
from discord.ext import commands
import sys
import asyncio
from datetime import datetime
import re
from services.logger import logger
from services.storage import vc_allow_storage, tts_settings_storage
from services.tts import sanitize_text, tts_worker

# Windows対応
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# コマンドモジュールをインポート
from commands import help, admin, images, fun, voice


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

        # イベントハンドラとコマンド登録
        self._setup_events()
        self._setup_commands()

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
            await self.bot.tree.sync()

        @self.bot.event
        async def on_message(message):
            # 自分の送信メッセージは無視（他Botは許可）
            if message.author == self.bot.user or not message.guild:
                return

            # 送信者が VC に接続していることを確認（ユーザーがどのVCにいても可）
            try:
                author_voice = getattr(message.author, "voice", None)
            except Exception:
                author_voice = None

            if not author_voice or not author_voice.channel:
                return

            # Bot がどのギルドの VC にも接続していなければ読み上げ不可
            vc = message.guild.voice_client
            if not vc or not vc.is_connected():
                return

            gid = message.guild.id
            settings = tts_settings_storage.get(gid)
            if not settings["enabled"]:
                return

            # リプライ情報を取得（あれば先頭に読み上げる）
            reply_prefix = ""
            if message.reference:
                try:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    if replied_msg and replied_msg.author:
                        reply_prefix = f"{replied_msg.author.display_name}さんへのリプライ。"
                except Exception as e:
                    logger.debug(f"リプライ情報取得エラー: {e}")

            # '以下略' を検出したらその位置で切り取り、末尾に表示文言を付ける
            content = message.content
            m = re.search(r'以下(?:省略|略)', content)
            suffix = ''
            if m:
                content_before = content[:m.start()].strip()
                suffix = '（以下省略）'
            else:
                content_before = content

            sanitized = sanitize_text(content_before, message.guild)
            # 読み上げる本文が無ければ終了
            if not sanitized:
                return

            # サニタイズ後40文字以上は切り詰めて「（以下省略）」を追加
            if len(sanitized) > 40:
                sanitized = sanitized[:40]
                suffix = '（以下省略）'

            text = reply_prefix + sanitized + suffix

            if gid not in self.bot.tts_queues:
                self.bot.tts_queues[gid] = asyncio.Queue()
                self.bot.tts_tasks[gid] = self.bot.loop.create_task(
                    tts_worker(self.bot, gid)
                )

            await self.bot.tts_queues[gid].put((text, settings["speaker"]))
            logger.debug(f"[Guild {gid}] TTS キューに追加: {text[:20]}...")

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
            settings = tts_settings_storage.get(gid)
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

            await self.bot.tts_queues[gid].put((text, settings["speaker"]))
            logger.info(f"[Guild {gid}] VC イベント読み上げキュー追加: {text}")

    def _setup_commands(self):
        """各モジュールのコマンドを登録"""
        help.setup_commands(self.bot)
        admin.setup_commands(self.bot)
        images.setup_commands(self.bot)
        fun.setup_commands(self.bot)
        voice.setup_commands(self.bot)
    
    def run(self):
        """Botを起動"""
        self.bot.run(self.token)
