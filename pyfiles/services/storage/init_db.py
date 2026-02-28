import aiosqlite
from ..logger import logger

class DBInitializer:

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS vc_allows (
                        guild_id INTEGER NOT NULL,
                        type TEXT NOT NULL,
                        target_id INTEGER NOT NULL,
                        PRIMARY KEY (guild_id, type, target_id)
                    );
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tts_settings (
                        guild_id INTEGER PRIMARY KEY,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        speaker_id INTEGER NOT NULL DEFAULT 1
                    );
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tts_dict (
                        guild_id INTEGER NOT NULL,
                        surface TEXT NOT NULL,
                        reading TEXT NOT NULL,
                        PRIMARY KEY (guild_id, surface)
                    );
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS levels (
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        xp INTEGER NOT NULL DEFAULT 0,
                        level INTEGER NOT NULL DEFAULT 1,
                        last_message REAL NOT NULL DEFAULT 0,
                        PRIMARY KEY (guild_id, user_id)
                    );
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS tts_voice_profiles (
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        engine TEXT NOT NULL,
                        speaker_id INTEGER NOT NULL,
                        speed REAL NOT NULL DEFAULT 1.0,
                        pitch REAL NOT NULL DEFAULT 0.0,
                        PRIMARY KEY (guild_id, user_id)
                    );
                """)

                await db.commit()

        except Exception:
            logger.exception("DB初期化エラー")
            raise
    
    async def set_user_voice(self, guild_id, user_id,
                            engine, speaker_id,
                            speed=1.0, pitch=0.0):

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO tts_voice_profiles
                (guild_id, user_id, engine, speaker_id, speed, pitch)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, user_id, engine,
                speaker_id, speed, pitch))
            await db.commit()

    async def get_user_voice(self, guild_id, user_id):

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT engine, speaker_id, speed, pitch
                FROM tts_voice_profiles
                WHERE guild_id=? AND user_id=?
            """, (guild_id, user_id)) as cursor:

                row = await cursor.fetchone()

                if row:
                    return row

        return "openjtalk", 1, 1.0, 0.0
