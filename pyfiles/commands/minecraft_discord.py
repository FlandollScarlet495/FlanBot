"""
マイクラとディスコードの連携

マイクラ鯖とディスコード鯖の連携・表示
"""
import discord
from discord.ext import tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
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

            tps = "?"
            try:
                with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                    tps_raw = mcr.command("tps")
                    for word in tps_raw.split():
                        if word.replace(".", "", 1).isdigit():
                            tps = word
                            break
            except Exception:
                pass

            new_name = f"ゆきのさば {players}/{max_players} TPS:{tps}"
            await channel.edit(name=new_name)

        except Exception:
            await channel.edit(name="ゆきのさば オフライン")
