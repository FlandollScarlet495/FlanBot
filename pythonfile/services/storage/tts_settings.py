from .base import SQLiteBase

class TTSSettingsStorage(SQLiteBase):

    def set_enabled(self, guild_id: int, enabled: bool):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO tts_settings (guild_id, enabled, speaker_id)
                VALUES (?, ?, 1)
                ON CONFLICT(guild_id)
                DO UPDATE SET enabled = excluded.enabled
            """, (guild_id, int(enabled)))
            conn.commit()

    def get(self, guild_id: int) -> dict:
        with self.connect() as conn:
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
