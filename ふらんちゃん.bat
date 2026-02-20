@echo off
chcp 65001 > nul
cd /d %~dp0

echo.
echo ╔════════════════════════════════════════════╗
echo ║     ふらんBot - Discord Bot Launcher       ║
echo ╚════════════════════════════════════════════╝
echo.

REM .envファイルの確認
if not exist .env (
    echo [エラー] .env ファイルが見つかりません
    echo.
    echo .env ファイルを作成してください：
    echo   DISCORD_TOKEN=your_discord_bot_token_here
    echo   DEVELOPER_ID=your_user_id_here
    pause
    exit /b 1
)
echo [OK] .env ファイルを確認しました

REM Pythonの確認
echo.
echo --- Python確認 ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    pause
    exit /b 1
)
echo [OK] Python がインストールされています
python --version

REM FFmpegの確認
echo.
echo --- FFmpeg確認 ---
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg がインストールされていません
    echo         ボイスチャット機能が動作しません
)

REM 依存パッケージの更新
echo.
echo --- pip を更新しています ---
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [エラー] pip の更新に失敗しました
    pause
    exit /b 1
)

REM requirements.txt の確認
if not exist requirements.txt (
    echo [エラー] requirements.txt が見つかりません
    pause
    exit /b 1
)

REM 依存パッケージのインストール
echo.
echo --- 依存パッケージをインストールしています ---
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)
echo [OK] パッケージのインストール完了

REM Botを起動
echo.
echo --- ふらんBot を起動しています ---
echo.
python main.py

pause
