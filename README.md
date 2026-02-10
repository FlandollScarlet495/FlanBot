# ふらんBot - Discord TTS Bot

ふらんちゃんだよよろしくぅ～

## 機能概要

- 🎤 **TTS（Text-to-Speech）読み上げ**: ボイスチャットに参加して、テキストメッセージを日本語で自動読み上げ
- 🎵 **VC参加/退出の通知**: ユーザーがボイスチャンネルに入退室したときにお知らせ
- 📚 **TTS辞書管理**: 難読漢字や固有名詞の読み方を登録して読み上げをカスタマイズ
- ⏭️ **スキップ機能**: 聞きたくない読み上げをスキップ
- 🖼️ **画像表示**: いろいろな画像を表示
- 🎲 **その他**: ロール管理、サイコロ、お遊びコマンドなど

## 📁 ファイル構成

```folder
ふらんBot/
├── main.py                      # 起動用ファイル（ここを実行する）
├── bot.py                       # Bot本体のクラス
├── config.py                    # 設定ファイル（環境変数の読み込み）
├── requirements.txt             # 依存パッケージ一覧
├── mypy.ini                     # 型チェック設定
├── pytest.ini                   # テスト設定
│
├── commands/                    # コマンド群
│   ├── __init__.py
│   ├── help.py                  # ヘルプコマンド  
│   ├── admin.py                 # ロール管理など管理系コマンド
│   ├── images.py                # 画像表示コマンド
│   ├── fun.py                   # サイコロなど遊び系コマンド
│   ├── voice.py                 # ボイスチャット関連（非推奨）
│   ├── vc_state.json            # VC状態の永続化
│   ├── stamp1/                  # スタンプ画像フォルダ
│   │   └── *.png
│   └── voice/                   # ボイスチャット関連コマンド
│       ├── __init__.py
│       ├── connect.py           # /join, /leave, /skip, /tts_on, /tts_off
│       ├── allow.py             # VC許可設定
│       ├── watchdog.py          # VC切断監視
│       ├── tts_dict.py          # TTS辞書管理コマンド
│       └── vc_allow.json        # VC許可設定の永続化
│
├── services/                    # サービス層（ビジネスロジック）
│   ├── __init__.py
│   ├── logger.py                # ロギング設定
│   ├── permission.py            # 権限チェック（管理者・開発者判定）
│   ├── tts.py                   # TTS合成・再生エンジン
│   └── storage/                 # データベース層
│       ├── __init__.py
│       ├── base.py              # SQLite接続管理
│       ├── init_db.py           # DB初期化スクリプト
│       ├── tts_dict.py          # TTS辞書DB操作
│       ├── tts_settings.py      # TTS設定DB操作
│       └── vc_allow.py          # VC許可設定DB操作
│
├── logs/                        # ログファイル（自動生成）
│
├── tests/                       # テストコード
│   ├── __init__.py
│   ├── conftest.py              # テスト設定・フィクスチャ
│   ├── test_logger.py
│   ├── test_permission.py
│   └── test_storage.py
│
├── REFACTORING.md               # リファクタリング手順（参考）
└── README.md                    # このファイル
```

## 🚀 セットアップ

### 前提条件

- Python 3.10以上
- FFmpeg （Voice チャット機能を使う場合は必須）
- OpenJTalk （TTS機能に必須）

### インストール手順

#### 1. リポジトリをクローン

```bash
git clone https://github.com/FlandollScarlet495/FlanBot.git
cd FlanBot
```

#### 2. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

#### 3. 環境変数をセットアップ

`.env` ファイルを作成し、以下の内容を記述します：

```env
DISCORD_TOKEN=your_discord_bot_token_here
DEVELOPER_ID=your_user_id_here
```

#### 4. データベースを初期化

```bash
python services/storage/init_db.py
```

#### 5. Botを起動

```bash
python main.py
```

## 💬 コマンド一覧

### 📱 ボイスチャット・TTS コマンド

| コマンド | 説明 | 権限 |
| ------- | ---- | ---- |
| `/join` | ボイスチャンネルに参加してTTS機能を有効化 | 全員 |
| `/leave` | ボイスチャンネルから退出 | 全員 |
| `/tts_on` | TTS読み上げをON（VCには参加したまま） | 全員 |
| `/tts_off` | TTS読み上げをOFF | 全員 |
| `/skip` | 現在再生中のTTS読み上げをスキップ | 全員 |
| `/tts_dict_add 単語 読み方` | TTS辞書に単語を登録（管理者専用） | 管理者 |
| `/tts_dict_remove 単語` | TTS辞書から単語を削除（管理者専用） | 管理者 |
| `/tts_dict_list` | 登録されている辞書一覧を表示 | 全員 |

### 🖼️ 画像・お遊び コマンド

| コマンド | 説明 |
| ------- | ---- |
| `/sonanoka` | そーなのかー画像表示 |
| `/sonanoda` | そーなのだー画像表示 |
| `/flandre` | ふらんちゃん画像表示 |
| `/stamp1 <番号>` | ふらんちゃんスタンプ表示 |
| `/dice` | サイコロを振る |

### 🛠️ ロール・管理 コマンド

| コマンド | 説明 | 権限 |
| ------- | ---- | ---- |
| `/give_role ユーザー名` | ユーザーにロールを付与 | 管理者 |
| `/remove_role ユーザー名` | ユーザーからロールを剥奪 | 管理者 |
| `/admin_del` | 管理者専用メッセージ削除 | 管理者 |
| `/delete` | 自分＋Botのメッセージを削除 | 全員 |

### ℹ️ 動作確認 コマンド

| コマンド | 説明 |
| ------- | ---- |
| `/help` | コマンド一覧を表示（3ページ） |
| `/ping` | 応答時間を確認 |
| `/about` | プロフィール表示 |
| `/test` | テスト |

## ⚙️ 設定

### TTS 読み上げの対象

- ✅ **読み上げる**: VC に接続しているユーザーがテキストチャネルに送信したメッセージ
- ✅ **読み上げる**: `/tts_on` でTTSを有効化したユーザーのメッセージ
- ✅ **読み上げる**: BC が参加/退出するときの通知
- ❌ **読み上げない**: VC に接続していないユーザーのメッセージ（`/tts_off` の場合）
- ❌ **読み上げない**: Bot のメッセージ

### テキスト処理の仕様

- 📝 **40文字制限**: 40文字を超えるメッセージは自動で切り詰めて「（以下省略）」を付加
- 📖 **以下略検出**: `以下略` または `以下省略` というテキストが含まれる場合、その位置で切り詰め
- 🔗 **URL削除**: URLは削除される
- 🎀 **絵文字削除**: 絵文字や記号類は削除される
- 💬 **メンション変換**: `@ユーザー名` は「ユーザー名さん」に変換される
- 💭 **リプライ対応**: リプライの場合、先頭に「相手さんへのリプライ。」が自動で追加される

## 🔧 開発・デバッグ

### ログ確認

```bash
# ログはコンソールと logs/ フォルダに出力されます
tail -f logs/*.log
```

### 型チェック

```bash
mypy bot.py commands/ services/
```

### テスト実行

```bash
pytest tests/
```

## 📊 アーキテクチャ

```text
Message (テキスト)
    ↓
on_message（VC判定・フィルタリング）
    ↓
sanitize_text（テキスト前処理）
    ↓
TTS Queue（ギルドごとのキュー）
    ↓
tts_worker（非同期ワーカー）
    ├─ synthesis_task（TTS合成）→ pyopenjtalk
    └─ playback_task（再生）→ FFmpeg PCM Audio
    ↓
Voice Channel（ボイスチャネルに再生）
```

Voice State Update（VC参加/退出）
    ↓
on_voice_state_update
    ↓
TTS Queue に「○○さんが接続しました」を追加
    ↓
同じフローで読み上げ

## 📝 今後の改善案

- [ ] `pyopenjtalk` の辞書カスタマイズを拡充
- [ ] TTS品質の最適化
- [ ] 複数音声話者の対応
- [ ] VC状態の更新が遅延する場合への対応
- [ ] 連続読み上げの安定性改善
- [ ] Web UI ダッシュボードの追加
- [ ] メトリクス・分析機能

## 🆚 変更履歴

### v1.0 (最新)

- TTS機能の実装（pyopenjtalk）
- SQLiteデータベース化
- VC参加/退出の通知機能
- TTS辞書管理機能
- メッセージテキスト処理（40文字制限、以下略検出）
- マルチギルド対応
- 非同期処理の最適化（並列 synthesis & playback）

## 📖 参考資料

- [discord.py documentation](https://discordpy.readthedocs.io/)
- [pyopenjtalk GitHub](https://github.com/Hiroshiba/pyopenjtalk)
- [OpenJTalk](http://open-jtalk.sourceforge.net/)

## 🎤 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
