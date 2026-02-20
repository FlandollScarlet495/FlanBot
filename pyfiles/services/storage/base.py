import sqlite3
from ...config import DB_PATH

class SQLiteBase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def connect(self):
        # タイムアウト設定でコンカレンシー問題を軽減（セキュリティ強化）
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        return conn
