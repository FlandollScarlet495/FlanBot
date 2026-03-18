import aiosqlite

class TTSSettingsStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # 1. 声の設定を保存するテーブル（既存）
            await db.execute('''CREATE TABLE IF NOT EXISTS voice_settings (
                guild_id INTEGER,
                user_id INTEGER,
                engine TEXT,
                speaker_id INTEGER,
                speed REAL,
                pitch REAL,
                PRIMARY KEY (guild_id, user_id)
            )''')

            # 2. 読み上げが有効かどうかを保存するテーブル（追加！）
            await db.execute('''CREATE TABLE IF NOT EXISTS tts_status (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0
            )''')
            await db.commit()

    # --- エラー解決のために追加したメソッド ---

    async def get(self, guild_id: int):
        """サーバーの読み上げON/OFF状態を取得する"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT enabled FROM tts_status WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                # 辞書形式で返せば bot.py の settings.get("enabled") が動くよ！
                if row:
                    return {"enabled": bool(row[0])}
                return {"enabled": False}

    async def set_enabled(self, guild_id: int, enabled: bool):
        """サーバーの読み上げON/OFFを切り替える"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO tts_status (guild_id, enabled) VALUES (?, ?) "
                "ON CONFLICT(guild_id) DO UPDATE SET enabled=excluded.enabled",
                (guild_id, int(enabled))
            )
            await db.commit()

    # --- 以下、既存のメソッド ---

    async def get_voice_setting(self, guild_id: int, user_id: int):
        # ...（お姉様の元のコードと同じ）...
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT engine, speaker_id, speed, pitch FROM voice_settings WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            row = await cur.fetchone()
            if not row:
                cur = await db.execute(
                    "SELECT engine, speaker_id, speed, pitch FROM voice_settings WHERE guild_id = ? AND user_id = 0",
                    (guild_id,)
                )
                row = await cur.fetchone()

            if row:
                return {"engine": row[0], "speaker_id": row[1], "speed": row[2], "pitch": row[3]}
            return {"engine": "openjtalk", "speaker_id": 1, "speed": 1.0, "pitch": 0.0}

    async def set_voice_setting(self, guild_id: int, user_id: int, engine, speaker_id, speed, pitch):
        # ...（お姉様の元のコードと同じ）...
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO voice_settings (guild_id, user_id, engine, speaker_id, speed, pitch)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    engine=excluded.engine,
                    speaker_id=excluded.speaker_id,
                    speed=excluded.speed,
                    pitch=excluded.pitch
            ''', (guild_id, user_id, engine, speaker_id, speed, pitch))
            await db.commit()
