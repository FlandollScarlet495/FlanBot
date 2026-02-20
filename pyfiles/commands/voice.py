"""
ボイスチャット関連コマンドのエントリーポイント
"""
from .voice import setup_commands as setup_voice

def setup_commands(bot):
    """コマンドをbotに登録する"""
    
    # 手動切断フラグ（botインスタンスに持たせる）
    if not hasattr(bot, 'manual_disconnect'):
        bot.manual_disconnect = set()

    setup_voice(bot)
