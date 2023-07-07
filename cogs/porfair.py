from random import randint, choice
import requests
from disnake.ext import commands
import traceback


def chance(a, b=500):
    if randint(1, b) <= a:
        return True
    return False


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'DNT': '1'
}


class PorfirAi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, mes):
        if not mes.author.bot:
            if chance(3):
                channel = mes.channel
                msgs = []
                async for msg in channel.history(limit=50):
                    if msg.content.startswith('%') or msg.content.startswith("http") or msg.content.startswith("https") \
                            or msg.content.startswith("<:") or msg.author.bot or not msg.content:
                        continue
                    else:
                        msgs.append(msg)
                if len(msgs) > 0:
                    async with channel.typing():
                        try:
                            msg = choice(msgs)
                            response = requests.post('https://pelevin.gpt.dobro.ai/generate/',
                                                     headers=headers,
                                                     json={"prompt": msg.content, "length": 30})
                            resp = f'{msg.content}{response.json()["replies"][0]}'
                            await channel.send(f'{resp}', reference=msg, mention_author=False)
                        except Exception:
                            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(PorfirAi(bot))
