"""
ふらんちゃんBot エントリーポイント

このファイルを実行してbotを起動する
"""
from pythonfile.bot import FlandreBot
from pythonfile.config import TOKEN


def main():
    """メイン処理"""
    flandre = FlandreBot(TOKEN)
    flandre.run()

if __name__ == "__main__":
    main()
