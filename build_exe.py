"""
PyInstaller ビルドスクリプト

Discord Bot を exe 化するためのスクリプト

使用方法:
    python build_exe.py
"""
import PyInstaller.__main__
import os
import sys
from pathlib import Path

# プロジェクトルート
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# 隠れたインポートを指定
HIDDEN_IMPORTS = [
    "discord",
    "discord.ext.commands",
    "dotenv",
    "pyfiles",
    "pyfiles.bot",
    "pyfiles.config",
]

# データファイルを指定
DATA_FILES = [
    ("logs", "logs"),
    ("pyfiles", "pyfiles"),  # stamp1 は pyfiles/commands/stamp1/ に含まれます
    (".env.sample", "."),
]

# root レベルの Python ファイルを指定
PYTHON_FILES = [
    str(ROOT_DIR / "main.py"),
]

def build_exe():
    """exe をビルド"""
    print("=" * 60)
    print("Discord Bot exe ビルドを開始します")
    print("=" * 60)
    
    # PyInstaller の引数
    args = [
        # エントリーポイント
        str(ROOT_DIR / "main.py"),
        
        # 出力設定
        "--onedir",  # フォルダ形式で生成（pyfiles/ と exe が同じ階層に）
        "--name=ふらんBot",  # exe の名前
        "--distpath=" + str(DIST_DIR),
        "--buildpath=" + str(BUILD_DIR),
        "--specpath=" + str(ROOT_DIR),
        
        # コンソール設定
        "--console",  # コンソール出力を表示
        
        # 隠れたインポート
        *[f"--hidden-import={module}" for module in HIDDEN_IMPORTS],
        
        # データファイル
        *[f"--add-data={src}{os.pathsep}{dst}" for src, dst in DATA_FILES],
        
        # パッケージの子モジュール自動検出
        "--collect-all=discord",
        
        # デバッグ情報
        "--debug=imports",
    ]
    
    print(f"\n生成される exe: {DIST_DIR / 'ふらんBot.exe'}")
    print(f"ビルドディレクトリ: {BUILD_DIR}\n")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "=" * 60)
        print("✅ ビルド成功！")
        print(f"exe フォルダは以下に生成されました:")
        print(f"  {DIST_DIR / 'ふらんBot'}/")
        print("=" * 60)
        
        # 使用方法を表示
        print("\n📖 使用方法:")
        print(f"  1. {DIST_DIR / 'ふらんBot'} フォルダに移動")
        print(f"  2. .env ファイルを配置（DISCORD_TOKEN と DEVELOPER_ID を設定）")
        print(f"     配置位置: {DIST_DIR / 'ふらんBot' / '.env'}")
        print(f"  3. 'ふらんBot.exe' をダブルクリックで実行")
        print(f"\n📁 フォルダ構成:")
        print(f"  dist/ふらんBot/")
        print(f"  ├── ふらんBot.exe")
        print(f"  ├── .env (手動で配置)")
        print(f"  ├── pyfiles/")
        print(f"  ├── logs/")
        print(f"  ├── stamp1/")
        print(f"  └── _internal/ (依存ライブラリ)")

        
        return True
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ エラーが発生しました: {e}")
        print("=" * 60)
        return False


def clean():
    """ビルドファイルをクリーンアップ"""
    print("クリーンアップ中...")
    import shutil
    
    for directory in [DIST_DIR, BUILD_DIR, ROOT_DIR / "ふらんBot.spec"]:
        if isinstance(directory, Path):
            if directory.is_dir():
                shutil.rmtree(directory)
                print(f"  削除: {directory}")
            elif directory.is_file():
                directory.unlink()
                print(f"  削除: {directory}")
        else:
            if os.path.exists(str(directory)):
                if os.path.isdir(str(directory)):
                    shutil.rmtree(str(directory))
                else:
                    os.remove(str(directory))
                print(f"  削除: {directory}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean()
    else:
        success = build_exe()
        sys.exit(0 if success else 1)
