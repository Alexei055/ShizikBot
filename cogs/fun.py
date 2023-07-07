import disnake
from disnake.ext import commands
import motor.motor_asyncio
import urllib.parse

quote_channel_id = 1040268412867334154
formats = ["png", 'jpg', 'jpeg', 'gif', 'svg', 'tiff']


# username = 'alexei055.kozachenko@gmail.com'
# password = '3ez5LvW#@jLEYBr'
# host = 'cloud.mindsdb.com'
# port = 27017
# username = urllib.parse.quote_plus(username)
# password = urllib.parse.quote_plus(password)
# uri = f"mongodb://{username}:{password}@{host}:{port}/?authMechanism=DEFAULT"
# client = motor.motor_asyncio.AsyncIOMotorClient(uri)
# db = client["mindsdb"]
# collection = db["gpt4"]


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # async def make_quote(self, inter, message):
    #     message = str(message)
    #     quote_message_id = message.split('/')[-1]
    #     quote_message: disnake.Message = await inter.channel.fetch_message(quote_message_id)
    #     content = f"{quote_message.content} [M]({quote_message.jump_url})"
    #     emb = disnake.Embed(colour=0x843679, description=content)
    #     emb.set_footer(text=f"(С){quote_message.author}", icon_url=quote_message.author.display_avatar.url)
    #     if quote_message.attachments:
    #         j = quote_message.attachments[0]
    #         for i in formats:
    #             if j.filename.endswith(i):
    #                 emb.set_image(url=j.url)
    #     return emb
    #
    # @commands.Cog.listener()
    # async def on_raw_message_delete(self, payload):
    #     if not payload.cached_message:
    #         print('Хуй')
    #         return
    #     message = payload.cached_message
    #     channel = self.bot.get_channel(1069583236591796264)
    #     emb = disnake.Embed(title="`Сообщения было удалено`", colour=0x9F368E)
    #     for a in message.attachments:
    #         if a.filename.endswith((".png", ".jpg", ".gif", ".mp4", ".jpeg", ".svg")):
    #             emb.set_image(url=a.proxy_url)
    #     emb.add_field(name="Удалённое сообщение: ", value=f"{message.content}" or "`[Контекст отсутствует]`",
    #                   inline=False)
    #     emb.add_field(name="Автор сообщения: ", value=f"{message.author.mention}", inline=False)
    #     emb.add_field(name="В канале: ", value=f"{message.channel.mention}")
    #     emb.set_footer(text=f"ID сообщения: {message.id}  | Сегодня в {message.created_at}"[:65])
    #     await channel.send(embed=emb)
    #
    # @commands.command()
    # async def quote(self,
    #                 ctx,
    #                 message: str = None):
    #     if ctx.message.reference:
    #         emb = await self.make_quote(ctx, ctx.message.reference.message_id)
    #     else:
    #         emb = await self.make_quote(ctx, message)
    #     quote_channel = self.bot.get_channel(quote_channel_id)
    #     await quote_channel.send(embed=emb)
    #     await ctx.send("Сделяль")
    #
    # @commands.slash_command(name="gpt",
    #                         description="Чатгпт...")
    # async def gpt(self,
    #               inter,
    #               request: str = commands.Param(description="Вопрос", )):
    #     inter: disnake.Interaction
    #     await inter.response.defer()
    #     async with inter.channel.typing():
    #         result = await collection.find_one(
    #             {"personality": "", "context": '', "author_username": "mindsdb", "text": request}, {"response": 1})
    #         response = result["response"]
    #         await inter.edit_original_message(response)

    @commands.Cog.listener()
    async def on_member_update(self, bef: disnake.Member, aft: disnake.Member):
        if bef.id == 638778376672509952:
            if aft.nick != "каппитализатор":
                await aft.edit(nick="каппитализатор")


def setup(bot):
    bot.add_cog(Fun(bot))
