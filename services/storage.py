"""
ストレージサービス

SQLiteデータベースの読み書きを担当する
"""
import sqlite3
from typing import Dict, Any
from config import DB_PATH
from .logger import logger


class SQLiteStorage:
    """VC操作許可用 SQLite ストレージ"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """データベース初期化"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vc_allows (
                        guild_id INTEGER NOT NULL,
                        type TEXT NOT NULL,
                        target_id INTEGER NOT NULL,
                        PRIMARY KEY (guild_id, type, target_id)
                    );
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tts_settings (
                        guild_id INTEGER PRIMARY KEY,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        speaker_id INTEGER NOT NULL DEFAULT 1
                    );
                """)

                conn.commit()
        except sqlite3.Error:
            logger.exception("DB初期化エラー")
            raise

    def set_tts_enabled(self, guild_id: int, enabled: bool) -> None:
      with sqlite3.connect(self.db_path) as conn:
          conn.execute("""
              INSERT INTO tts_settings (guild_id, enabled, speaker_id)
              VALUES (?, ?, 1)
              ON CONFLICT(guild_id)
              DO UPDATE SET enabled = excluded.enabled
          """, (guild_id, int(enabled)))
          conn.commit()

    def get_tts_settings(self, guild_id: int) -> dict:
      try:
        with self._get_conn() as conn:
          cur = conn.execute(
            "SELECT enabled, speaker_id FROM tts_settings WHERE guild_id = ?",
            (guild_id,)
          )
          row = cur.fetchone()
          if row:
            return {"enabled": bool(row[0]), "speaker": row[1]}

          conn.execute(
            "INSERT INTO tts_settings VALUES (?, 1, 1)",
            (guild_id,)
          )
          return {"enabled": True, "speaker": 1}
      except Exception:
        return {"enabled": True, "speaker": 1}

    # --------------------
    # 互換用 API（既存コード対応）
    # --------------------

    def load(self, guild_id: int) -> Dict[str, Any]:
        """
        VC許可データを読み込む

        Returns:
            {"users": [...], "roles": [...]}
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT target_id FROM vc_allows WHERE guild_id = ? AND type = 'user'",
                    (guild_id,)
                )
                users = [row[0] for row in cursor.fetchall()]

                cursor.execute(
                    "SELECT target_id FROM vc_allows WHERE guild_id = ? AND type = 'role'",
                    (guild_id,)
                )
                roles = [row[0] for row in cursor.fetchall()]

                return {"users": users, "roles": roles}
        except sqlite3.Error as e:
            logger.error(f"DB読み込みエラー: {e}")
            return {"users": [], "roles": []}

    def save(self, guild_id: int, data: Dict[str, Any]) -> bool:
        """
        互換用一括保存（基本的に使用非推奨）
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM vc_allows WHERE guild_id = ?",
                    (guild_id,)
                )

                for uid in data.get("users", []):
                    cursor.execute(
                        "INSERT INTO vc_allows VALUES (?, 'user', ?)",
                        (guild_id, uid)
                    )

                for rid in data.get("roles", []):
                    cursor.execute(
                        "INSERT INTO vc_allows VALUES (?, 'role', ?)",
                        (guild_id, rid)
                    )

                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"DB保存エラー: {e}")
            return False

    # --------------------
    # 本命 API
    # --------------------

    def add_user(self, guild_id: int, user_id: int) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO vc_allows VALUES (?, 'user', ?)",
                    (guild_id, user_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            logger.error(f"ユーザー追加エラー: {e}")
            return False

    def remove_user(self, guild_id: int, user_id: int) -> bool:
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "DELETE FROM vc_allows WHERE guild_id = ? AND type = 'user' AND target_id = ?",
                    (guild_id, user_id)
                )
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"ユーザー削除エラー: {e}")
            return False

    def add_role(self, guild_id: int, role_id: int) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO vc_allows VALUES (?, 'role', ?)",
                    (guild_id, role_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            logger.error(f"ロール追加エラー: {e}")
            return False

    def remove_role(self, guild_id: int, role_id: int) -> bool:
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "DELETE FROM vc_allows WHERE guild_id = ? AND type = 'role' AND target_id = ?",
                    (guild_id, role_id)
                )
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"ロール削除エラー: {e}")
            return False


# グローバルインスタンス
vc_allow_storage = SQLiteStorage(DB_PATH)
