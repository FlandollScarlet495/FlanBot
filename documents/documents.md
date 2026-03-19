# ふらんBot 技術ドキュメント

**Python 3.14+** | **discord.py 2.4+** | **MIT License**

## 1. 概要

ふらんBot は Discord サーバー向けの多機能 TTS (Text-to-Speech) Botです。 テキストチャンネルのメッセージを `pyopenjtalk` または `VOICEVOX` を用いてボイスチャンネルで自動読み上げします。 さらに TTS 辞書管理、ロール管理、画像表示、Minecraft サーバー連携など幅広い機能を搭載しています。

---

## 2. セットアップ

### 2.1 前提条件

**Python 3.14 以上**
**FFmpeg**（ボイスチャット機能に必須）
**OpenJTalk**（TTS エンジンとして使用する場合）
**VOICEVOX**（オプション：高品質な音声合成エンジン）

### 2.2 インストール手順

1. **リポジトリのクローン**

    ```bash
    git clone [https://github.com/FlandollScarlet495/FlanBot.git](https://github.com/FlandollScarlet495/FlanBot.git)
    cd FlanBot
    ```

2. **仮想環境の設定・有効化、依存パッケージのインストール**

    ```cmd # Windows
    python -m venv .venv
    .venv\Scripts\activate.bat
    pip install -r requirements.txt
    ```

    ```PowerShell # Windows
    python -m venv .venv
    .venv\Scripts\activate.ps1
    pip install -r requirements.txt
    ```

    ```bash # MacOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install -r requirements.txt
    ```

    ```bash or PowerShell or cmd
    deactivate
    ```

3. **環境変数の設定**
    `.env` ファイルをプロジェクトルートに作成し、以下の変数を設定してください。

| 変数名 | 例 | 説明 |
| :--- | :--- | :--- |
| `DISCORD_TOKEN` | `your_discord_bot_token_here` | Discord Botトークン（必須） |
| `DEVELOPER_ID` | `123456789012345678` | 開発者のDiscordユーザーID（必須） |
| `SERVER_ADDRESS` | `example.playit.gg` | Minecraftサーバーのアドレス（必須） |
| `VOICE_CHANNEL_ID` | `your_channel_id` | 状態を表示するVC ID（必須） |
| `RCON_PASSWORD` | `your_password` | Minecraft RCON パスワード（必須） |

4. **データベースの初期化と起動**

    ```bash
    python pyfiles/services/storage/init_db.py  # DB初期化
    python main.py                              # Botの起動
    ```

---

## 3. アーキテクチャ

### 3.1 ディレクトリ構成

`main.py`: エントリーポイント
`pyfiles/bot.py`: イベント・コマンド登録
`pyfiles/commands/`: 各種コマンド（管理、遊び、マイクラ、音声）
`pyfiles/services/`: ロジック層（TTS合成、VOICEVOXクライアント等）
`pyfiles/storage/`: SQLite データベース層

### 3.2 TTS 処理フロー

1. **受信**: `on_message` でテキストを受信。
2. **判定**: VCテキストチャンネル判定およびTTS有効化チェック。
3. **整形**: `sanitize_text()` でURL削除や80文字制限を適用。
4. **合成**: `pyopenjtalk` または `VOICEVOX` で音声データを生成。
5. **再生**: `FFmpegPCMAudio` でボイスチャンネルへ出力。

---

## 4. コマンドリファレンス

### 4.1 ボイス・TTSコマンド

`/join`: VCに参加し、TTSを開始。
`/leave`: VCから退出し、TTSを終了。
`/setvoice`: 自分の音声（速度・ピッチ等）をカスタマイズ。
`/tts_dict_add`: 辞書に単語と読みを登録。

### 4.2 お遊び・管理コマンド

`/dice`: ダイスを振る（例: 1d20）。
`/flandre`: ふらんちゃん画像を送信。
`/admin_del`: メッセージの一括削除（最大50件）。

---

## 5. Minecraft サーバー連携

`minecraft_discord.py` により、60秒ごとにサーバー状態を取得し、指定したVCの名前を自動更新します
**オンライン時**: `ゆきのさば {現在人数}/{最大人数} TPS:{TPS}`
**オフライン時**: `ゆきのさば オフライン`

---

## 6. 開発ガイド

**型チェック**: `mypy pyfiles/bot.py` 等で実施
**テスト**: `pytest pyfiles/tests/` で各モジュールの動作を確認

---

## ふらんBot — MIT License

MIT License

Copyright (c) 2025 紅音 雪乃

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
