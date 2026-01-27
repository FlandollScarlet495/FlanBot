# ふらんBot - ゆきののつぶやきbot

ふらんちゃんだよよろしくぅ～

## Self Introduction (English)

It's Flandre, nice to meet you~

---

## Renderへのデプロイ方法

### 前提条件
- GitHub アカウント
- Renderアカウント (https://render.com)

### デプロイ手順

1. **GitHubにプッシュ**
   ```bash
   git add .
   git commit -m "Render対応"
   git push origin main
   ```

2. **Renderダッシュボードで接続**
   - https://dashboard.render.com にアクセス
   - 「New +」→「Web Service」を選択
   - GitHubリポジトリを接続

3. **環境変数を設定**
   - Render のダッシュボードで `DISCORD_TOKEN` を設定
   - Environment 画面で追加

4. **デプロイ**
   - Renderが自動的にデプロイを開始します

### 注意点
- **Free プラン**では、Keep-Alive サーバーが15分のアイドル後に停止します
- **Paid プラン** を使用することで、常時稼働できます
- `DISCORD_TOKEN` は **Environment Variables** で秘密として保管してください

---

## ローカル開発

### セットアップ
```bash
pip install -r requirements.txt
echo "DISCORD_TOKEN=your_token_here" > .env
python bot.py
```

### ファイル構成
- `bot.py` - メインのDiscord Bot
- `keep_alive.py` - サーバーをキープアライブするFlaskサーバー
- `Procfile` - Render/Heroku用の起動コマンド
- `render.yaml` - Renderの設定ファイル

---

## ライセンス
MIT License - 詳細は [LICENSE](LICENSE) を参照してください
