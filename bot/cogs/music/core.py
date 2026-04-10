import mafic

from disnake.ext import commands
from config import Config


class MusicCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.pool = mafic.NodePool(self.bot)
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await self.bot.pool.create_node(
            host=Config.LAVALINK_HOST,
            port=Config.LAVALINK_PORT,
            label="MASTER_NODE",
            password=Config.LAVALINK_PASSWORD,
        )

    @commands.Cog.listener()
    async def on_node_ready(self, node: mafic.Node):
        self.bot.logger.info(f"🎵 [MASTER] Lavalink Node '{node.label}' готова к поиску треков!")

def setup(bot):
    bot.add_cog(MusicCore(bot))