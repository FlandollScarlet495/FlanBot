import sqlite3
from typing import Dict, Any
from .base import SQLiteBase
from services.logger import logger

class VCAllowStorage(SQLiteBase):

    def load(self, guild_id: int) -> Dict[str, Any]:
        try:
            with self.connect() as conn:
                cur = conn.cursor()

                cur.execute(
                    "SELECT target_id FROM vc_allows WHERE guild_id = ? AND type = 'user'",
                    (guild_id,)
                )
                users = [r[0] for r in cur.fetchall()]

                cur.execute(
                    "SELECT target_id FROM vc_allows WHERE guild_id = ? AND type = 'role'",
                    (guild_id,)
                )
                roles = [r[0] for r in cur.fetchall()]

                return {"users": users, "roles": roles}
        except sqlite3.Error as e:
            logger.error(f"DB読み込みエラー: {e}")
            return {"users": [], "roles": []}

    def save(self, guild_id: int, data: Dict[str, Any]) -> bool:
        try:
            with self.connect() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM vc_allows WHERE guild_id = ?", (guild_id,))

                for uid in data.get("users", []):
                    cur.execute(
                        "INSERT INTO vc_allows VALUES (?, 'user', ?)",
                        (guild_id, uid)
                    )

                for rid in data.get("roles", []):
                    cur.execute(
                        "INSERT INTO vc_allows VALUES (?, 'role', ?)",
                        (guild_id, rid)
                    )

                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"DB保存エラー: {e}")
            return False

    def add_user(self, guild_id: int, user_id: int) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO vc_allows VALUES (?, 'user', ?)",
                    (guild_id, user_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_user(self, guild_id: int, user_id: int) -> bool:
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM vc_allows WHERE guild_id = ? AND type='user' AND target_id = ?",
                (guild_id, user_id)
            )
            return cur.rowcount > 0

    def add_role(self, guild_id: int, role_id: int) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO vc_allows VALUES (?, 'role', ?)",
                    (guild_id, role_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_role(self, guild_id: int, role_id: int) -> bool:
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM vc_allows WHERE guild_id = ? AND type='role' AND target_id = ?",
                (guild_id, role_id)
            )
            return cur.rowcount > 0
