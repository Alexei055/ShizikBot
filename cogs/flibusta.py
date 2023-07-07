from __future__ import annotations
import cgi
import io
from bs4 import BeautifulSoup
import disnake
from disnake.ext import commands
from disnake import SelectOption
from aiohttp_socks import ProxyConnector
from pyquery import PyQuery as pq
from dataclasses import dataclass
import aiohttp

RATING = {
    'файл не оценен': 0,
    'файл на 1': 1,
    'файл на 2': 2,
    'файл на 3': 3,
    'файл на 4': 4,
    'файл на 5': 5
}

PROXY_ADDRESS = "socks5://192.168.0.100:9050"


class NotFoundBook(commands.CommandError):
    def __str__(self):
        return "Не найдена книга"


class BlockConnectFlibusta(commands.CommandError):
    def __str__(self):
        return "Ошибка при отвале прокси"


class MaxRetriesError(commands.CommandError):
    def __str__(self):
        return "Достигнуто максимальное число попыток подключения"


@dataclass
class Book:
    book_name: str
    author: str
    book_link: str
    book_rating: str

    @classmethod
    def from_div(cls, div: pq) -> Book:
        link = pq(div)("div > a")
        img = pq(div)("img")
        return cls(
            link[0].text,
            link[-1].text,
            link.attr.href,
            img.attr.title
        )


async def search_books(book_name: str) -> str:
    """Парсинг страницы с книгами по параметру"""
    connector = ProxyConnector.from_url(PROXY_ADDRESS, force_close=True)
    reload_count = 0
    while reload_count < 3:
        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
                async with session.get(
                        f'http://flibusta.is/makebooklist?ab=ab1&t={"+".join(book_name.split(" "))}') as search_result:
                    if search_result.status == 200:
                        result = await search_result.text()
                        print(reload_count)
                        if result == 'Не нашлось ни единой книги, удовлетворяющей вашим требованиям.':
                            raise NotFoundBook
                        if "Доступ к ресурсу заблокирован!" in result:
                            raise BlockConnectFlibusta
                        else:
                            return result

        except Exception as e:
            if isinstance(e, (NotFoundBook, BlockConnectFlibusta)):
                raise e
            reload_count += 1

    raise MaxRetriesError


async def fetch_books(book_name) -> list[Book]:
    search_result = await search_books(book_name)

    doc = pq(search_result)

    books = [Book.from_div(i) for i in doc.find('div')]

    sotred_books = sorted(books,
                          key=lambda book: RATING[book.book_rating],
                          reverse=True)
    return sotred_books


async def search_image(link_book) -> str | None:
    connector = ProxyConnector.from_url(PROXY_ADDRESS, force_close=True)
    async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
        async with session.get(f"http://flibusta.is{link_book}") as book_link:
            result = await book_link.text()
            try:
                soup = BeautifulSoup(result, 'html.parser')
                values = soup.find_all("img", {"alt": "Cover image"})[0]
                doc = pq(str(values)).attr.src
                return doc
            except Exception:
                return None


class Flibusta(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.user_select_menu = {}
        self.image_channel = 991847730500604056

    async def cog_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception) -> None:

        if isinstance(error, (MaxRetriesError, BlockConnectFlibusta)):
            return await inter.send(f"<@262615370773430275>, тут по твоей части ошибочка:\n"
                                    f"```{error}```")

        if isinstance(error, NotFoundBook):
            return await inter.send(f"{inter.author.mention} не найдено книг по вашему запросу")

        await super().cog_slash_command_error(inter, error)
        await inter.send(f"<@262615370773430275>, тут по твоей части ошибочка, ```{str(error)[:1500]}```")
        raise error

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if not inter.data.custom_id.startswith("musicplayer_"):
            connector = ProxyConnector.from_url(PROXY_ADDRESS, force_close=True)
            await inter.response.defer()
            custom_id = inter.component.custom_id

            if custom_id == "prev_page":
                paginator_buttons = [
                    disnake.ui.Button(custom_id=f"prev_page", style=disnake.ButtonStyle.green, emoji="◀"),
                    disnake.ui.Button(custom_id=f"next_page", style=disnake.ButtonStyle.green, emoji="▶")]

                self.user_select_menu[inter.author.id]["index"] -= 1
                index = self.user_select_menu[inter.author.id]["index"]
                books: list[list[Book]] = self.user_select_menu[inter.author.id]["list_books"]
                count_books = sum([len(i) for i in books])
                from_ = sum([len(i) for i in books][:index]) + 1
                to = from_ + len(books[index]) - 1

                select_menu = disnake.ui.Select(
                    placeholder=f"Всего книг: {count_books}    Отображается с {from_} по {to}",
                    options=[SelectOption(emoji="📖",
                                          label=f"{book.book_name[:99]}",
                                          value=book.book_link,
                                          description=f"{book.author[:85]} | {book.book_rating}",
                                          ) for book in books[index]])
                components = []

                if index == 0:
                    paginator_buttons[0].disabled = True
                    components.append(select_menu)
                    components.append(paginator_buttons)
                else:
                    components.append(select_menu)
                return await inter.edit_original_message(components=components)

            if custom_id == "next_page":
                paginator_buttons = [
                    disnake.ui.Button(custom_id=f"prev_page", style=disnake.ButtonStyle.green, emoji="◀"),
                    disnake.ui.Button(custom_id=f"next_page", style=disnake.ButtonStyle.green, emoji="▶")]

                self.user_select_menu[inter.author.id]["index"] += 1
                index = self.user_select_menu[inter.author.id]["index"]
                books: list[list[Book]] = self.user_select_menu[inter.author.id]["list_books"]
                count_books = sum([len(i) for i in books])
                from_ = sum([len(i) for i in books][:index]) + 1
                to = from_ + len(books[index]) - 1

                select_menu = disnake.ui.Select(
                    placeholder=f"Всего книг: {count_books}    Отображается с {from_} по {to}",
                    options=[SelectOption(emoji="📖",
                                          label=f"{book.book_name[:99]}",
                                          value=book.book_link,
                                          description=f"{book.author[:85]} | {book.book_rating}",
                                          ) for book in books[index]])
                components = []

                if index == len(books) - 1:
                    paginator_buttons[1].disabled = True
                    components.append(select_menu)
                    components.append(paginator_buttons)

                else:
                    components.append(select_menu)

                return await inter.edit_original_message(components=components)

            if custom_id == "back_to_list":
                books: list[list[Book]] = self.user_select_menu[inter.author.id]["list_books"]
                count_books = sum([len(i) for i in books])
                index = self.user_select_menu[inter.author.id]['index']
                components = []

                from_ = sum([len(i) for i in books][:index]) + 1
                to = from_ + len(books[index]) - 1

                select_menu = disnake.ui.Select(
                    placeholder=f"Всего книг: {count_books}    Отображается с {from_} по {to}",
                    options=[
                        SelectOption(emoji="📖",
                                     label=f"{book.book_name[:99]}",
                                     value=book.book_link,
                                     description=f"{book.author[:85]} | {book.book_rating}",
                                     ) for book in
                        books[self.user_select_menu[inter.author.id]['index']]
                    ])
                components.append(select_menu)
                if count_books > 25:
                    paginator_buttons = [
                        disnake.ui.Button(custom_id=f"prev_page", style=disnake.ButtonStyle.green, emoji="◀",
                                          disabled=True),
                        disnake.ui.Button(custom_id=f"next_page", style=disnake.ButtonStyle.green, emoji="▶"), ]
                    if index == len(books) - 1:
                        paginator_buttons[0].disabled = False
                        paginator_buttons[1].disabled = True

                    components.append(paginator_buttons)

                return await inter.edit_original_message("Выберите книгу по вашему запросу", components=components,
                                                         embed=None, attachments=[])

            else:
                await inter.edit_original_message("Книга скачивается, пожалуйста, ожидайте", components=[], embed=None,
                                                  attachments=[])
                async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
                    async with session.get(f"http://flibusta.is{custom_id}") as book_file:
                        result = await book_file.read()

                        if "Internal server error" in str(result):
                            embed = self.user_select_menu[inter.author.id]["embed"]
                            await inter.edit_original_message("",
                                                              components=[
                                                                  self.user_select_menu[inter.author.id]["button"]],
                                                              embed=embed)
                            return await inter.send(
                                f"{inter.author.mention}, книга в этом формате не доступна, пожалуйста, попробуйте другой",
                                delete_after=10)

                        else:
                            filename = cgi.parse_header(book_file.headers['content-disposition'])[1]['filename']
                            content_length = int(book_file.headers['content-length'])
                            if content_length >= 19000000:  # 19 mb
                                await inter.edit_original_message(
                                    "Книга весит больше 8 мегабайт, я не могу такую отправить"
                                    ", потому что разработчик дебил")
                                del self.user_select_menu[inter.author.id]
                                return
                            else:
                                data = io.BytesIO(result)
                                file = disnake.File(data, filename=filename)
                                await inter.send(f"{inter.author.mention} ваша книга", file=file)
                                await inter.delete_original_message()
                                del self.user_select_menu[inter.author.id]

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        connector = ProxyConnector.from_url(PROXY_ADDRESS, force_close=True)
        await inter.response.defer()
        await inter.edit_original_message("Обработка", components=[])
        original_components = inter.component
        selected_value = inter.values[0]
        selected_option = 0
        for compon in original_components.options:
            if compon.value == selected_value:
                selected_option = compon
                break

        buttons = [disnake.ui.Button(custom_id=f"{selected_value}/epub", label="Скачать в epub",
                                     style=disnake.ButtonStyle.green, emoji="📗", row=1),
                   disnake.ui.Button(custom_id=f"{selected_value}/fb2", label="Скачать в fb2",
                                     style=disnake.ButtonStyle.red, emoji="📕", row=1),
                   disnake.ui.Button(custom_id=f"{selected_value}/mobi", label="Скачать в mobi",
                                     style=disnake.ButtonStyle.blurple, emoji="📘", row=1),
                   disnake.ui.Button(custom_id=f"back_to_list", label="Вернуться к списку",
                                     style=disnake.ButtonStyle.gray, emoji="📚", row=2), ]

        book_rating = RATING[selected_option.description.split('|')[1].lstrip()]

        image_link = await search_image(selected_value)
        image_link_2 = "https://cdn.discordapp.com/attachments/644984473368133652/991794432091361390/unknown.png?size=4096"

        if image_link:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
                async with session.get(f"http://flibusta.is{image_link}") as book_file:
                    data = io.BytesIO(await book_file.read())
                    file = disnake.File(data, filename="image.png")
                    image_channel = self.bot.get_channel(self.image_channel)
                    msg = await image_channel.send("", file=file)

        embed = disnake.Embed(title=selected_option.label,
                              description=f"Автор: {selected_option.description.split('|')[0]}\n"
                                          f"Оценка: {'⭐' * book_rating if book_rating else 'Нет оценки'}")
        embed.set_thumbnail(url=msg.attachments[0].url if image_link else image_link_2)
        self.user_select_menu[inter.author.id]["button"] = buttons
        self.user_select_menu[inter.author.id]["embed"] = embed
        await inter.edit_original_message(content="", embed=embed, components=[buttons])

    @commands.slash_command(name="flibusta", description="поиск книг на флибусте")
    async def flibusta(self,
                       inter: disnake.CommandInteraction,
                       book_name: str = commands.Param(name="название",
                                                       description="название книги"), ):
        """Поиск книг на флибусте"""
        await inter.response.send_message(f"Ищем книгу с названием - **{book_name}**")
        books = await fetch_books(book_name)
        f = lambda list_books, array_length=25: [list_books[i:i + array_length] for i in
                                                 range(0, len(list_books), array_length)]

        books: list[list[Book]] = f(books)
        count_books = sum([len(i) for i in books])
        paginator_buttons = [disnake.ui.Button(custom_id=f"prev_page", style=disnake.ButtonStyle.green, emoji="◀"),
                             disnake.ui.Button(custom_id=f"next_page", style=disnake.ButtonStyle.green, emoji="▶"), ]

        select_menu = disnake.ui.Select(placeholder=f"Всего книг: {count_books}    Отображается с 1 по {len(books[0])}",
                                        options=[
                                            SelectOption(emoji="📖",
                                                         label=f"{book.book_name[:99]}",
                                                         value=book.book_link,
                                                         description=f"{book.author[:85]} | {book.book_rating}"
                                                         ) for book in books[0]
                                        ])
        components = [select_menu]

        try:
            del self.user_select_menu[inter.author.id]
        except:
            pass

        self.user_select_menu[inter.author.id] = {"index": 0, "list_books": books, "button": 0, "embed": 0}
        if count_books > 25:
            paginator_buttons[0].disabled = True
            components.append(paginator_buttons)
        await inter.edit_original_message("Выберите книгу по вашему запросу", components=components)


def setup(bot):
    bot.add_cog(Flibusta(bot))
