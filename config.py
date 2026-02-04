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

# ファイルパス
VC_STATE_FILE = "vc_state.json"
VC_ALLOW_FILE = "vc_allow.json"

# 定数
MAX_DELETE = 50
