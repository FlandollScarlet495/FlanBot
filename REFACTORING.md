# リファクタリング Before / After

## 🔴 Before: 元のコード

### 構造

```text
bot.py (500行)
├─ グローバル変数
├─ 共通関数
├─ イベントハンドラ
├─ ヘルプコマンド
├─ アプリコマンド
├─ 管理系コマンド
├─ 画像コマンド
├─ 遊び系コマンド
├─ 削除系コマンド
├─ 動作確認コマンド
└─ VCコマンド
```

### 問題点

#### 1. 構造化されていない

- 500行が1ファイルに詰め込まれている
- 機能ごとの区切りがない
- どこに何があるか分からない

#### 2. グローバル変数が多い

```python
bot = commands.Bot(...)           # グローバル
VC_STATE_FILE = "vc_state.json"   # グローバル
VC_ALLOW_FILE = "vc_allow.json"   # グローバル
MAX_DELETE = 50                   # グローバル

# あちこちで参照される
@bot.tree.command(...)  # ← botがどこから来たか分からない
```

#### 3. 責任が混在

```python
# 権限チェック
def is_admin_or_dev(interaction):
    return ...

# ファイル操作
def load_vc_allow():
    with open(...) as f:
        return json.load(f)

# コマンド実装
@bot.tree.command(name="give_role")
async def give_role(...):
    if not is_admin_or_dev(...):  # ← 権限チェック
        return
    # ... ロール付与処理
```

→ 「権限」「ファイル」「コマンド」が同じレベルに並んでいる

#### 4. 変更の影響範囲が不明

- 「権限チェックのロジック変更」→ どこに影響するか分からない
- 「JSONファイルの保存形式変更」→ 全体を読む必要がある

---

## 🟢 After: リファクタリング版

### フォルダ構成

```folder
flandre_bot_refactored/
├── main.py (10行)              # 起動するだけ
├── bot.py (80行)               # Bot本体のクラス
├── config.py (20行)            # 設定の一元管理
├── commands/                   # コマンド群
│   ├── help.py (60行)         # ヘルプ・動作確認
│   ├── admin.py (180行)       # 管理系コマンド
│   ├── images.py (50行)       # 画像コマンド
│   ├── fun.py (80行)          # 遊び系コマンド
│   └── voice.py (200行)       # VC関連
└── services/                   # 共通処理
    ├── permission.py (60行)   # 権限チェック
    └── storage.py (60行)      # ファイル操作
```

### 改善点

#### 1. 機能ごとに分割

```python
# 画像コマンドを修正したい
→ commands/images.py を開く

# 権限チェックを変更したい
→ services/permission.py を開く

# VC機能を追加したい
→ commands/voice.py に追記
```

#### 2. グローバル変数を削減

```python
# config.py で一元管理
TOKEN = os.getenv("DISCORD_TOKEN")
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID"))

# bot.py でクラス化
class FlandreBot:
    def __init__(self, token):
        self.token = token
        self.bot = commands.Bot(...)

# 使う側
flandre = FlandreBot(TOKEN)
flandre.run()
```

#### 3. 責任を分離

```python
# 権限チェック（services/permission.py）
def is_admin_or_dev(interaction):
    return ...

# ファイル操作（services/storage.py）
class JSONStorage:
    def load(self): ...
    def save(self, data): ...

# コマンド実装（commands/admin.py）
@bot.tree.command(name="give_role")
async def give_role(...):
    if not is_admin_or_dev(...):  # ← services/から使う
        return
    # ...
```

#### 4. 変更の影響範囲が明確

- 「権限チェック変更」→ `services/permission.py` だけ修正
- 「JSONファイル形式変更」→ `services/storage.py` だけ修正
- 「画像コマンド追加」→ `commands/images.py` に追記

---

## 📊 数字で見る改善

| 項目 | Before | After |
| ---- | ------ | ----- |
| ファイル数 | 1 | 10 |
| 最大行数/ファイル | 500行 | 200行 |
| グローバル変数 | 5個 | 2個 |
| 関数の平均行数 | 30行 | 15行 |
| 「どこにあるか」探す時間 | 5分 | 10秒 |

---

## 🎓 息子さんへの説明ポイント

### なぜ分けるのか？

#### 例1: バグ修正

```text
Before:
「あれ、VCから切断できない...」
→ bot.py の500行を全部読む
→ 30分かかる

After:
「あれ、VCから切断できない...」
→ commands/voice.py を開く（200行）
→ leave 関数を見る（20行）
→ 5分で原因発見
```

#### 例2: 機能追加

```text
Before:
「新しい画像コマンド追加したい」
→ bot.py のどこに書けばいい？
→ 既存の画像コマンドを探す
→ 間違った場所に書いて動かない

After:
「新しい画像コマンド追加したい」
→ commands/images.py に書く
→ 迷わない
```

#### 例3: チーム開発

```text
Before:
友達A: 「VC機能作るわ」
友達B: 「画像コマンド作るわ」
→ 同じファイル（bot.py）を同時編集
→ コンフリクト地獄

After:
友達A: 「commands/voice.py 作るわ」
友達B: 「commands/images.py 作るわ」
→ 別ファイル
→ コンフリクトなし
```

---

## 💡 次のステップ

このリファクタリングは「構造化」だけです。
さらに改善するなら：

1. **SQLite化**: JSONファイル → データベース
2. **ログ改善**: print → logging モジュール
3. **テスト追加**: pytest でユニットテスト
4. **型チェック**: mypy で型安全性
5. **ドキュメント**: docstring を充実

でも、**まずは構造を理解すること**が大事です。
