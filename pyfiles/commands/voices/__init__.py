"""
ボイス系の初期化ファイルです

ボイス系の関数群が入ってます
"""
import asyncio
from .connect import setup_commands as setup_connect
from .setvoice import setup_commands as setup_voice
from .tts_dict import setup_commands as setup_tts_dict

def setup_commands(bot):
    # 従来の関数ベースのセットアップ
    setup_voice(bot)
    setup_connect(bot)
    setup_tts_dict(bot)
