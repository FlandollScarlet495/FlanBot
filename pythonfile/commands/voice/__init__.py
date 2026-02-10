from .connect import setup_commands as setup_connect
from .allow import setup_commands as setup_allow
from .tts_dict import setup_commands as setup_tts_dict

def setup_commands(bot):
    setup_connect(bot)
    setup_allow(bot)
    setup_tts_dict(bot)
