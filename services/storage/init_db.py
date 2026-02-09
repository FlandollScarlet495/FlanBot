import sqlite3
from .base import SQLiteBase
from services.logger import logger

class DBInitializer(SQLiteBase):
    def init(self):
        try:
            with self.connect() as conn:
                cur = conn.cursor()

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vc_allows (
                        guild_id INTEGER NOT NULL,
                        type TEXT NOT NULL,
                        target_id INTEGER NOT NULL,
                        PRIMARY KEY (guild_id, type, target_id)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tts_settings (
                        guild_id INTEGER PRIMARY KEY,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        speaker_id INTEGER NOT NULL DEFAULT 1
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tts_dict (
                        guild_id INTEGER NOT NULL,
                        surface TEXT NOT NULL,
                        reading TEXT NOT NULL,
                        PRIMARY KEY (guild_id, surface)
                    );
                """)

                conn.commit()
        except sqlite3.Error:
            logger.exception("DB初期化エラー")
            raise
