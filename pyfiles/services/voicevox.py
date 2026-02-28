import aiohttp
import io

class VoicevoxEngine:

    def __init__(self, host="localhost", port=50021):
        self.base = f"http://{host}:{port}"
        self.voice_dict = {}

    async def initialize(self):
        """Bot起動時に一度だけ呼ぶ"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base}/speakers") as res:
                data = await res.json()

        self.voice_dict = {
            s["name"]: {st["name"]: st["id"] for st in s["styles"]}
            for s in data
        }

    def get_id(self, name: str, style: str = "ノーマル"):
        if name in self.voice_dict:
            styles = self.voice_dict[name]
            return styles.get(style, list(styles.values())[0])
        return 1  # fallback

    async def synthesize(self, text, speaker_id, speed=1.0, pitch=0.0):
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
