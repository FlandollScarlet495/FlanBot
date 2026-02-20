"""
マイクラとディスコードの連携

マイクラ鯖とディスコード鯖の連携・表示
"""
import discord
from discord.ext import tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
import re
from pyfiles.config import (
    VOICE_CHANNEL_ID,
    SERVER_ADDRESS,
    SERVER_PORT,
    RCON_HOST,
    RCON_PASSWORD,
    RCON_PORT
)

def setup_commands(bot):

    @bot.event
    async def on_ready():
        update_channel.start()

    @tasks.loop(seconds=60)
    async def update_channel():

        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(VOICE_CHANNEL_ID)

        try:
            server = JavaServer.lookup(f"{SERVER_ADDRESS}:{SERVER_PORT}")
            status = server.status()

            players = status.players.online
            max_players = status.players.max

            try:
                with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                    tps_raw = mcr.command("tps")
                    # 数字とドットとカンマだけ残すよ！
                    clean_tps = re.sub(r'[^\d.,]', '', tps_raw)
                    # 最初の数字（1分間の平均）を取り出す
                    tps = clean_tps.split(',')[0]
            except Exception:
                tps = "Error"

            new_name = f"ゆきのさば {players}/{max_players} TPS:{tps}"
            await channel.edit(name=new_name)

        except Exception:
            await channel.edit(name="ゆきのさば オフライン")
