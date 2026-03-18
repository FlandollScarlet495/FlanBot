import aiohttp
import io
import subprocess
import os
import asyncio
from ..services.logger import logger
# ここで config をインポートするよ！
from .. import config


class VoicevoxEngine:
    def __init__(self, host="localhost", port=50021):
        self.base = f"http://{host}:{port}"
        self.voice_dict = {}
        # config からパスを取得
        self.engine_path = config.VOICE_ENGINE_PATH

    async def initialize(self):
        """
        Bot起動時に一度だけ呼び出す。
        エンジンが未起動なら、別プロセスで起動を試みる。
        """
        try:
            # 1. まずは現在の接続状況を確認
            await self._fetch_speakers()
            logger.info("VOICEVOXエンジンは既に起動しています。")
            return
        except (aiohttp.ClientConnectorError, Exception):
            logger.info("VOICEVOXエンジンへの接続に失敗しました。起動を試みます...")

        # 2. パスチェック
        if not self.engine_path or not os.path.exists(self.engine_path):
            logger.warning("VOICEVOXの起動パスが見つかりません。手動で起動してください。")
            self.voice_dict = {}
            return

        try:
            # 3. 別プロセスでエンジンを起動
            # shell=False (推奨) で実行し、標準出力を捨てることでBotのプロセスから切り離します。
            # Windowsの場合、CREATE_NO_WINDOW フラグを立てると黒い画面が出ません。
            creation_flags = 0
            if os.name == 'nt':  # Windowsの場合
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [self.engine_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creation_flags,
                close_fds=True  # プロセスを完全に独立させる
            )

            # 4. 起動を待機するリトライループ
            for i in range(10):  # 最大10回（約20秒）
                await asyncio.sleep(2)
                try:
                    await self._fetch_speakers()
                    logger.info(f"VOICEVOXエンジンが正常に起動しました（試行 {i+1}回目）")
                    return
                except Exception:
                    continue

            logger.error("エンジンプロセスは開始されましたが、応答がありません。")

        except Exception as e:
            logger.error(f"エンジンの起動処理中にエラーが発生しました: {e}")
            self.voice_dict = {}

    async def _fetch_speakers(self):
        """話者リストを取得する内部関数"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base}/speakers", timeout=3) as res:
                data = await res.json()
        self.voice_dict = {
            s["name"]: {st["name"]: st["id"] for st in s["styles"]}
            for s in data
        }

    async def synthesize(self, text, speaker_id, speed=1.0, pitch=1.0):
        """tts_workerから呼ぶ用"""

        limited_text = text[:120]

        async with aiohttp.ClientSession() as session:

            async with session.post(
                f"{self.base}/audio_query",
                params={"text": limited_text, "speaker": speaker_id}
            ) as res:
                query = await res.json()

            query["speedScale"] = speed
            query["pitchScale"] = pitch

            async with session.post(
                f"{self.base}/synthesis",
                params={"speaker": speaker_id},
                json=query
            ) as res:
                data = await res.read()

        return io.BytesIO(data)
