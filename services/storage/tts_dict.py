import sqlite3
from .base import SQLiteBase

class TTSDictStorage(SQLiteBase):

    def add(self, guild_id: int, surface: str, reading: str) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO tts_dict VALUES (?, ?, ?)",
                    (guild_id, surface, reading)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove(self, guild_id: int, surface: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM tts_dict WHERE guild_id = ? AND surface = ?",
                (guild_id, surface)
            )
            return cur.rowcount > 0

    def list(self, guild_id: int):
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT surface, reading FROM tts_dict WHERE guild_id = ?",
                (guild_id,)
            )
            return cur.fetchall()
