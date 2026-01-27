from flask import Flask
from threading import Thread
import os

app = Flask('')
run = True

@app.route('/')
def home():
	return "YukinoBotが起動しました！"

def run():
	app.run(host='0.0.0.0', port=8080)

def keep_alive():
	t = Thread(target=run)
	t.start()

def stop_server():
	print("サーバーを停止します...")
	os._exit(0) # プロセス全体を終了させる
