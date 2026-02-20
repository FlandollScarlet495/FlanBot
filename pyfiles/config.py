"""
設定ファイル

環境変数やBot全体の設定を管理する
"""
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# 必須設定
TOKEN = os.getenv("DISCORD_TOKEN")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))
SERVER_ADDRESS = str(os.getenv("SERVER_ADDRESS"))
SERVER_PORT = int(os.getenv("SERVER_PORT") or 25565)
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID") or 0)
RCON_HOST = str(os.getenv("RCON_HOST"))
RCON_PORT = int(os.getenv("RCON_PORT" or 25575))
RCON_PASSWORD = str(os.getenv("RCON_PASSWORD"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が未設定です")
if not DEVELOPER_ID:
    raise RuntimeError("DEVELOPER_ID が未設定です")
if not SERVER_ADDRESS:
    raise RuntimeError("SERVER_ADDRESS が未設定です")
if not SERVER_PORT:
    raise RuntimeError("SERVER_PORT が未設定です")
if not VOICE_CHANNEL_ID:
    raise RuntimeError("VOICE_CHANNEL_ID が未設定です")
if not RCON_HOST:
    raise RuntimeError("RCON_HOST が未設定です")
if not RCON_PORT:
    raise RuntimeError("RCON_PORT が未設定です")
if not RCON_PASSWORD:
    raise RuntimeError("RCON_PASSWORD が未設定です")

# データベースパス（絶対パスを使用してセキュリティを強化）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "bot_data.db")

# 定数
MAX_DELETE = 50
