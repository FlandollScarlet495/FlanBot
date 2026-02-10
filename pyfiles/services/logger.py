"""
ログ管理サービス

ロギング設定を一元管理する
"""
import logging
from datetime import datetime


def setup_logger(name: str = "FlandreBot") -> logging.Logger:
    """
    ロガーをセットアップする
    
    Args:
        name: ロガー名
        
    Returns:
        logging.Logger: 設定済みのロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 既に handler があれば追加しない
    if logger.hasHandlers():
        return logger
    
    # ログファイルの名前（日付付き）
    log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # コンソール出力（INFO以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    
    # ファイル出力（DEBUG以上）
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"ログファイルの作成に失敗しました: {e}")
    
    logger.addHandler(console_handler)
    
    return logger


# グローバルロガーのインスタンス
logger = setup_logger()
