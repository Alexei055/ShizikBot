import asyncio

import wavelink
from utils import Config
from wavelink.ext import spotify
import logging
import logging.handlers
from typing import List, Optional
import disnake
from disnake.ext import commands
from disnake.ext import tasks

intents = disnake.Intents.all()


class MyBot(commands.Bot):
    def __init__(self, *args,
                 initial_extensions: List[str],
                 testing_guild_id: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.node: wavelink.Node = None
        self.initial_extensions = initial_extensions
        self.testing_guild_id = testing_guild_id

    async def on_ready(self):
        """Подключение и инициализация узлов лавалинк"""
        if self.initial_extensions:
            for extension in self.initial_extensions:
                self.load_extension(extension)

        nodes = {"bot": self,
                 "host": Config.LAVA_HOST,
                 "port": Config.LAVA_PORT,
                 "password": Config.LAVA_PASS,
                 }

        if Config.SPOTIFY_CLIENT_ID:
            nodes["spotify_client"] = spotify.SpotifyClient(client_id=Config.SPOTIFY_CLIENT_ID,
                                                            client_secret=Config.SPOTIFY_SECRET)

        node: wavelink.Node = wavelink.Node(uri=f'https://{Config.LAVA_HOST}:{Config.LAVA_PORT}',
                                            password=Config.LAVA_PASS)
        self.node = node
        await wavelink.NodePool.connect(client=self,
                                        nodes=[node])

        print(f"[dismusic] INFO - Created node: {node}")


logger = logging.getLogger('disnake')
logger.setLevel(logging.DEBUG)
logging.getLogger('disnake.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='disnake.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

exts = ["cogs.flibusta"]

bot = MyBot(command_prefix="!!",
            initial_extensions=exts,
            intents=disnake.Intents.all(),
            test_guilds=Config.GUILD_IDS)

bot.run(Config.TOKEN)

# bot.load_extension("cogs.music")
# bot.load_extension("cogs.fun")
# bot.load_extension("cogs.flibusta")
# bot.load_extension("cogs.randommes")
