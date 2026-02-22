"""
ボイス系の初期化ファイルです

ボイス系の関数群が入ってます
"""
from .connect import setup_commands as setup_connect
from .tts_dict import setup_commands as setup_tts_dict

def setup_commands(bot):
    setup_connect(bot)
    setup_tts_dict(bot)
