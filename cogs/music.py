import random

from disnake import SelectOption
from datetime import timedelta
from utils import *
from disnake.ext import commands

from wavelink import TrackEventPayload, NodeStatus


class TrackNotFound(commands.CommandError):
    """Не найдена песня"""
    pass


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_timer = {}
        self.user_all_time = {}

    async def cog_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception) -> None:
        if isinstance(error, TrackNotFound):
            return await inter.send(f"{inter.author.mention} не найден трек по вашему запросу")

        await super().cog_slash_command_error(inter, error)
        raise error

    async def timeout_check(self, channel_id, guild_id):
        await asyncio.sleep(PLAYER_TIMEOUT)
        if player := self.bot.node.get_player(guild_id):
            channel = self.bot.get_channel(channel_id)
            if len(channel.members) == 1:
                await player.destroy()

    @commands.Cog.listener("on_button_click")
    async def on_player_button(self, interaction: disnake.MessageInteraction):
        if not interaction.data.custom_id.startswith("musicplayer_"):
            return

        await self.player_controller(interaction, interaction.data.custom_id)

    @commands.Cog.listener()
    async def on_voice_state_update(self,
                                    member: disnake.Member,
                                    before: disnake.VoiceState,
                                    after: disnake.VoiceState):
        if before.channel == after.channel:
            return
        if player := self.bot.node.get_player(member.guild.id):
            if member.id == self.bot.user.id and after.channel is None:
                await player.destroy()
                return

            channel = self.bot.get_channel(player.channel.id)

            if len(channel.members) == 1:
                await self.timeout_check(player.channel.id, member.guild.id)
                return

    @commands.Cog.listener("on_wavelink_track_exception")
    @commands.Cog.listener("on_wavelink_track_end")
    @commands.Cog.listener("on_wavelink_track_stuck")
    async def on_player_stop(self, payload: TrackEventPayload):
        payload.player: Player
        if payload.player.loop_mode:
            await payload.player.play(payload.player.looped_track)
            return
        payload.player.update_embed.cancel()
        await payload.player.do_next()

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown_player(self, inter: disnake.MessageInteraction):
        if not inter.data.custom_id.startswith("musicplayer_"):
            return

        player: Player = self.bot.node.get_player(inter.guild.id)
        selected_value = int(inter.values[0])
        await inter.response.edit_message(f"`{player.queue._queue[selected_value].title}` удален из очереди",
                                          components=[])
        del player.queue._queue[selected_value]
        await player.invoke_controller()

    async def player_controller(self, interaction: disnake.MessageInteraction, control: str):
        player: Player = self.bot.node.get_player(interaction.guild.id)
        await interaction.response.defer()
        print(player)
        if player:
            if interaction.message.id == player.message_controller.id:
                match control:

                    case PlayerControls.PLAY:
                        await player.set_paused()

                    case PlayerControls.PAUSE:
                        await player.set_paused()

                    case PlayerControls.STOP:
                        await player.destroy()
                        await interaction.edit_original_message(components=[])

                    case PlayerControls.SKIP:
                        await player.stop()

                    case PlayerControls.SHUFFLE:
                        if player.queue.qsize() < 3:
                            return await interaction.channel.send("Мало песен в очереди для перемешивания")
                        random.shuffle(player.queue._queue)
                        await interaction.channel.send("Очередь была перемешана")

                    case PlayerControls.LOOP_MODE:
                        if player.loop_mode:
                            player.loop_mode = False
                            await interaction.channel.send("Режим повтора выключен")
                        else:
                            player.loop_mode = True
                            player.looped_track = player.current
                            await interaction.channel.send("Режим повтора включен")

                    case PlayerControls.ADD_TO_PLAYLIST:
                        playlists = json.load(open("playlists.json"))
                        print(playlists)

                    case PlayerControls.REMOVE_FROM_PLAYLIST:
                        pass

    async def connect(self,
                      inter: disnake.CommandInteraction | disnake.Message,
                      user: disnake.Member,
                      channel: disnake.VoiceChannel = None):
        player = Player(inter=inter, bot=self.bot)

        channel = getattr(user.voice, 'channel', channel)

        if channel is None:
            await inter.channel.send(f"{user.mention} вы должны находиться в голосовом канале")
            return
        else:
            await channel.connect(cls=player)
            return player

    @commands.slash_command(name="play", )
    async def play(self,
                   inter: disnake.CommandInteraction,
                   search: str = commands.Param(description="URL или название трека", )):
        await inter.response.defer()
        player: Player = self.bot.node.get_player(inter.guild.id)
        if player is None or player.current_node.status == NodeStatus.DISCONNECTED:
            player = await self.connect(inter, inter.user)
        player.inter = inter
        await player.add_tracks(search)

    @commands.slash_command(name="seek",
                            description="перемотать трек на определенное место")
    async def seek(self,
                   inter: disnake.CommandInteraction,
                   minutes: commands.Range[1, ...] = commands.Param(name="минута",
                                                                    description="На какую минуту перемотать",
                                                                    default=None),
                   seconds: commands.Range[0, 60] = commands.Param(name="секунда",
                                                                   description="На какую секунду перемотать", )):
        player: Player = self.bot.node.get_player(inter.guild)
        minutes: int
        seconds: int
        if player and player.is_playing():
            position = seconds + (minutes * 60000) if minutes else seconds * 1000
            human_position = seconds + (minutes * 60) if minutes else seconds
            if position > (player.track.length * 60000):
                await inter.response.send_message(f"Трек столько не длится", delete_after=15)
                return
            await player.seek(position)
            await inter.response.send_message(
                f"Трек перемотан на {time.strftime('%M:%S', time.gmtime(human_position))}")
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="volume",
                            description="Настройка громкости")
    async def set_volume(self,
                         inter: disnake.CommandInteraction,
                         volume: commands.Range[0, 100] = commands.Param(name="громкость",
                                                                         description="На сколько процентов установить громкость воспроизведения")):
        player: Player = self.bot.node.get_player(inter.guild)
        volume: int
        if player and player.is_playing():
            await player.set_volume(volume)
            await inter.response.send_message(f"Громкость плеера установлена на {volume}%", delete_after=10)
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="remove",
                            description="Удалить определенный трек из очереди")
    async def remove_track(self, inter: disnake.CommandInteraction):
        player: Player = self.bot.node.get_player(inter.guild)
        if player and player.is_playing():
            qsize = player.queue.qsize()
            if qsize > 0:
                select_menu = disnake.ui.Select(
                    placeholder=f"Всего треков: {qsize}    Отображается с 1 по {qsize}",
                    options=[SelectOption(emoji="🎵",
                                          label=f"{ind + 1} - {tr.title[:95]}",
                                          value=f"{ind}",
                                          description=f"{time.strftime('%M:%S', time.gmtime(tr.length))}") for ind, tr
                             in tuple(enumerate(player.queue._queue))[:25]
                             ],
                    custom_id="musicplayer_dropdown")
                await inter.response.send_message("Выберите какой трек хотите удалить", components=[select_menu])
            else:
                await inter.response.send_message("Очередь пуста", delete_after=10)
        else:
            await inter.response.send_message(f"Музыка сейчас не играет", delete_after=15)

    @commands.slash_command(name="move",
                            description="Переместить бота в другой голосовой канал")
    async def move_bot(self, inter: disnake.CommandInteraction, channel: disnake.VoiceChannel):
        if player := self.bot.node.get_player(inter.guild):
            await player.move_to(channel)
            await inter.response.send_message(f"Я переместился в {channel.mention}", delete_after=10)
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку", delete_after=10)

    @commands.slash_command(name="qclear",
                            description="Очищает очередь")
    async def clear_queue(self, inter: disnake.CommandInteraction):
        if player := self.bot.node.get_player(inter.guild):
            player.queue = asyncio.Queue()
            await inter.response.send_message(f"Очередь была очищена", delete_after=10)
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку", delete_after=10)

    @commands.slash_command(name="stop",
                            description="Остановить музыку")
    async def stop(self, inter: disnake.CommandInteraction):
        if player := self.bot.node.get_player(inter.guild):
            await player.destroy()
            await inter.response.send_message(f"А всё, конец", delete_after=10)
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку", delete_after=10)

    @commands.slash_command(name="skip",
                            description="Пропустить трек")
    async def skip(self, inter: disnake.CommandInteraction):
        if player := self.bot.node.get_player(inter.guild):
            await player.stop()
            await inter.response.send_message(f"`{player.track.title}` был пропущен", delete_after=10)
        else:
            await inter.response.send_message(f"Я сейчас не играю музыку", delete_after=10)

    @commands.slash_command(name="test",
                            description="test")
    async def test(self, inter: disnake.CommandInteraction):
        player: Player = self.bot.node.get_player(inter.guild.id)
        print(player.current_node.status)
        print(type(player.current_node.status))


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
