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
          if message.author.bot or not message.guild:
            return

          vc = message.guild.voice_client
          if not vc or not vc.is_connected():
              return

          if not message.author.voice:
              return
          if message.author.voice.channel != vc.channel:
              return

          # ボイスチャンネルと同じカテゴリーのテキストチャンネルか確認
          # カテゴリーがない場合（直下のチャンネル）も許容
          if message.channel.category and vc.channel.category:
              if message.channel.category != vc.channel.category:
                  return
          elif message.channel.category or vc.channel.category:
              # 一方がカテゴリーを持っていて、もう一方が持っていない場合はスキップ
              return

          gid = message.guild.id
          settings = tts_settings_storage.get(gid)
          if not settings["enabled"]:
            return

          # リプライ情報を取得
          reply_prefix = ""
          if message.reference:
              try:
                  replied_msg = await message.channel.fetch_message(message.reference.message_id)
                  if replied_msg.author:
                      reply_prefix = f"{replied_msg.author.display_name}さんへのリプライ。"
              except Exception as e:
                  logger.debug(f"リプライ情報取得エラー: {e}")

          text = reply_prefix + sanitize_text(message.content, message.guild)
          if not text.replace(reply_prefix, ""):  # リプライプレフィックス以外が空の場合
            return

          if gid not in self.bot.tts_queues:
            self.bot.tts_queues[gid] = asyncio.Queue()
            self.bot.tts_tasks[gid] = self.bot.loop.create_task(
              tts_worker(self.bot, gid)
            )

          await self.bot.tts_queues[gid].put((text, settings["speaker"]))
          logger.debug(f"[Guild {gid}] TTS キューに追加: {text[:20]}...")

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
