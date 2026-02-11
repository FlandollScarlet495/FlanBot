# exe ビルド手順

## 📋 前提条件

- Python 3.10以上がインストールされていること
- 必須パッケージがインストールされていること

## 🚀 ビルド手順

### 1. 必須パッケージをインストール

```bash
pip install -r requirements.txt
```

特に以下が必要です：

- `PyInstaller` - exe ビルドツール
- `discord.py` - Discord API ライブラリ
- `python-dotenv` - 環境変数管理
- その他のボット依存パッケージ

### 2. ビルドスクリプトを実行

```bash
python build_exe.py
```

実行すると以下が生成されます：

- `dist/ふらんBot/` - exe フォルダ（pyfiles/ と同じ階層）
  - `ふらんBot.exe` - 実行可能なプログラム
  - `pyfiles/` - ボット本体ファイル（stamp1/ を含む）
  - `logs/` - ログ出力先
  - `_internal/` - 依存ライブラリ
- `build/` - ビルド中間ファイル
- `ふらんBot.spec` - PyInstaller スペックファイル

### 3. exe フォルダの配有

`dist/ふらんBot/` 配下のファイルすべてを配有します。

生成されるフォルダ構造：

```folder
dist/ふらんBot/
├── ふらんBot.exe          # メイン実行ファイル
├── .env                    # 設定ファイル（手動で配置）
├── pyfiles/                # ボット本体ファイル
│   ├── bot.py
│   ├── config.py
│   ├── commands/
│   │   └── stamp1/         # スタンプ画像
│   ├── services/
│   └── ...
├── logs/                   # ログディレクトリ（自動作成）
└── _internal/              # 依存ライブラリ（PyInstaller 自動生成）
```

## ⚙️ exe 実行前の設定

### 1. `.env` ファイルを作成

`dist/ふらんBot/` フォルダ内に `.env` ファイルを作成します：

```env
DISCORD_TOKEN=your_discord_bot_token_here
DEVELOPER_ID=your_user_id_here
```

**配置位置**: `dist/ふらんBot/.env`

.env.sample がビルド時に同じフォルダにコピーされるため、それを参考に作成してください。

**注意**: `.env` ファイルには機密情報が含まれるため：

- git で管理しない
- 配有時には含めない
- ユーザーが自分で作成する必要があります

### 2. 外部依存ファイルの確認

exe が正常に動作するには、以下が必要な場合があります：

- **FFmpeg** - ボイスチャット機能用（オプション）
  - インストール: <https://ffmpeg.org/>
  - PATH に追加

- **OpenJTalk** - TTS（Text-to-Speech）用
  - Python パッケージ: `pip install pyopenjtalk`
  - exe 化時に自動的に含まれます

## ▶️ exe の実行

### 方法1: ダブルクリック

`dist/ふらんBot/` フォルダ内の `ふらんBot.exe` をダブルクリックで実行します。

### 方法2: コマンドプロンプトから実行

```cmd
cd dist\ふらんBot
ふらんBot.exe
```

**重要**: exe は必ず同じフォルダ内の pyfiles/, logs/, stamp1/ が必要です。
単独で移動や複製はできません。

## 📊 ビルド結果の確認

ビルドが成功すると、以下のようなログが表示されます：

```bash
============================================================
Discord Bot exe ビルドを開始します
============================================================

生成される exe フォルダ: dist\ふらんBot\
ビルドディレクトリ: build

... ビルド処理 ...

============================================================
✅ ビルド成功！
exe フォルダは以下に生成されました:
  dist\ふらんBot\
============================================================

📖 使用方法:
  1. dist\ふらんBot フォルダに移動
  2. .env ファイルを配置（DISCORD_TOKEN と DEVELOPER_ID を設定）
     配置位置: dist\ふらんBot\.env
  3. 'ふらんBot.exe' をダブルクリックで実行

📁 フォルダ構成:
  dist\ふらんBot\
  ├── ふらんBot.exe
  ├── .env (手動で配置)
  ├── pyfiles\ (stamp1 を含む)
  ├── logs\
  └── _internal\ (依存ライブラリ)
```

## 🧹 クリーンアップ

ビルドファイルを削除する場合：

```bash
python build_exe.py --clean
```

以下が削除されます：

- `dist/` - 生成された exe
- `build/` - ビルド中間ファイル
- `ふらんBot.spec` - スペックファイル

## ⚠️ 注意事項

### ファイルサイズが大きい

- PyInstaller が生成する exe フォルダは総容量が 100～200 MB 程度になる場合があります
- 圧縮しても配有時に時間がかかる可能性があります
- `_internal/` フォルダがサイズの大部分を占めます

### 実行パスの重要性

- exe は必ず **同じフォルダ** に以下が必要です：
  - `pyfiles/` - ボット本体ファイル（pyfiles/commands/stamp1/ を含む）
  - `logs/` - ログ出力ディレクトリ（自動作成）
  - `_internal/` - 依存ライブラリ（自動生成）

- `dist/ふらんBot/` フォルダ全体を保持する必要があります
- exe のみ取り出して実行することはできません

### exe フォルダの場所

- `dist/ふらんBot/` フォルダを任意の場所に移動可能です
- ただし、フォルダ内部の構造は変更しないでください
- `ふらんBot.exe` は必ずそのフォルダ内で実行してください

## 🔧 トラブルシューティング

### exe が起動しない

1. `.env` ファイルが配置されているか確認
2. `DISCORD_TOKEN` が正しいか確認
3. コマンドプロンプトから実行してエラーメッセージを確認

### dll が見つからないエラー

```exe
ImportError: DLL load failed
```

**対処**:

1. Python が C++ 再配布可能パッケージをインストール
2. Windows Update を実行
3. Python 再インストール

### TTS/音声出力が動作しない

1. `pyopenjtalk` がインストールされているか確認
2. FFmpeg がインストールされているか確認（PATH に追加）

## 📚 参考資料

- PyInstaller 公式: <https://pyinstaller.org/>
- Discord.py 公式: <https://discordpy.readthedocs.io/>
