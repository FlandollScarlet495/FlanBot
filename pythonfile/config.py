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

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が未設定です")
if not DEVELOPER_ID:
    raise RuntimeError("DEVELOPER_ID が未設定です")

# データベースパス（絶対パスを使用してセキュリティを強化）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "bot_data.db")

# ファイルパス（互換性のため旧設定も残す）
# 将来的に削除予定
VC_STATE_FILE = "vc_state.json"
VC_ALLOW_FILE = "vc_allow.json"

# 定数
MAX_DELETE = 50
