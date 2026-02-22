import aiosqlite

class TTSSettingsStorage:

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, guild_id: int):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                "SELECT enabled, speaker_id FROM tts_settings WHERE guild_id = ?",
                (guild_id,)
            ) as cur:
                row = await cur.fetchone()

        if row is None:
            return {"enabled": True, "speaker": 1}

        enabled, speaker_id = row
        return {"enabled": bool(enabled), "speaker": speaker_id}
