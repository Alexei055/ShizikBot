import os
import random
import disnake
from disnake.ext import commands, tasks

from main import MyBot

HOURS = random.randint(6, 12)
MINUTES = random.randint(5, 60)
SECONDS = random.randint(5, 60)
CHANNEL_ID = 748498382288322653


class RandomMes(commands.Cog):
    def __init__(self, bot):
        self.bot: MyBot = bot
    #     self.random_mes.start()
    #
    # @tasks.loop(seconds=SECONDS, minutes=MINUTES, hours=HOURS)
    # async def random_mes(self):
    #
    #     channel = self.bot.get_channel(CHANNEL_ID)
    #     msgs = []
    #
    #     async for msg in channel.history(limit=250):
    #         if msg.content.startswith('%') or msg.content.startswith("http") or msg.content.startswith("https") \
    #                 or msg.content.startswith("<:") or msg.author.bot or not msg.content:
    #             continue
    #         else:
    #             msgs.append(msg)
    #
    #     if len(msgs) > 0:
    #         msg: disnake.Message = random.choice(msgs)
    #         await channel.send(msg.content)
    #
    # @random_mes.before_loop
    # async def before_random_mes(self):
    #     await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(RandomMes(bot))
