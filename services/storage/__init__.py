from .init_db import DBInitializer
from .vc_allow import VCAllowStorage
from .tts_settings import TTSSettingsStorage
from .tts_dict import TTSDictStorage

# 初期化
DBInitializer().init()

# グローバルインスタンス
vc_allow_storage = VCAllowStorage()
tts_settings_storage = TTSSettingsStorage()
tts_dict_storage = TTSDictStorage()
