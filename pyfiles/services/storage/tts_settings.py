import aiosqlite


class TTSSettingsStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, guild_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT enabled, speaker_id FROM tts_settings WHERE guild_id = ?",
                (guild_id,)
            )
            row = await cursor.fetchone()

            if row:
                return {
                    "enabled": bool(row[0]),
                    "speaker": row[1]
                }

            # デフォルト値
            return {
                "enabled": False,
                "speaker": 1
            }

    async def set_enabled(self, guild_id: int, enabled: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO tts_settings (guild_id, enabled)
                VALUES (?, ?)
                ON CONFLICT(guild_id)
                DO UPDATE SET enabled = excluded.enabled
                """,
                (guild_id, int(enabled))
            )
            await db.commit()
