import os
import disnake
import io
import chat_exporter
import json

from disnake.ext import commands

class TicketControlView(disnake.ui.View):
    def __init__(self, is_closed: bool = False):
        super().__init__(timeout=None)
        if not is_closed:
            self.add_item(disnake.ui.Button(
                label="Закрыть Тикет", 
                style=disnake.ButtonStyle.secondary, 
                custom_id="ticket_close",
                emoji="🔒"
            ))
        else:
            self.add_item(disnake.ui.Button(
                label="Открыть Тикет", 
                style=disnake.ButtonStyle.success, 
                custom_id="ticket_open",
                emoji="🔓"
            ))
            self.add_item(disnake.ui.Button(
                label="Удалить Тикет", 
                style=disnake.ButtonStyle.danger, 
                custom_id="ticket_delete",
                emoji="🗑️"
            ))

class TicketModal(disnake.ui.Modal):
    def __init__(self, ticket_type: str):
        self.ticket_type = ticket_type
        components = [
            disnake.ui.TextInput(
                label="Заголовок проблемы",
                placeholder="Кратко опишите суть...",
                custom_id="ticket_title",
                style=disnake.TextInputStyle.short,
                max_length=256,
            ),
            disnake.ui.TextInput(
                label="Описание проблемы",
                placeholder="Опишите проблему максимально подробно...",
                custom_id="ticket_desc",
                style=disnake.TextInputStyle.paragraph,
                max_length=4000,
            ),
            disnake.ui.TextInput(
                label="Ссылка на видео/скриншот (необязательно)",
                placeholder="https://...",
                custom_id="ticket_media",
                style=disnake.TextInputStyle.short,
                required=False,
            ),
        ]
        title = "Серверный Тикет" if ticket_type == "server" else "Технический Тикет"
        super().__init__(title=title, custom_id=f"modal_ticket_{ticket_type}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        bot = inter.bot
        
        title = inter.text_values["ticket_title"]
        desc = inter.text_values["ticket_desc"]
        media = inter.text_values.get("ticket_media")

        cat_id = int(os.getenv("TICKET_CATEGORY_SERVER")) if self.ticket_type == "server" else int(os.getenv("TICKET_CATEGORY_TECH"))
        category = inter.guild.get_channel(cat_id)
        
        redis_key = f"ticket_count_{self.ticket_type}"
        ticket_num = await bot.redis.incr(redis_key)
        type_short = "server" if self.ticket_type == "server" else "tech"
        channel_name = f"ticket-{type_short}-{ticket_num}"

        admin_role = inter.guild.get_role(int(os.getenv("ADMIN_ROLE_ID")))
        support_role = inter.guild.get_role(int(os.getenv("SUPPORT_ROLE_ID")))
        
        overwrites = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            bot.user: disnake.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        if admin_role: overwrites[admin_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role: overwrites[support_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await inter.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Тикет #{ticket_num} от {inter.author.id}"
        )

        embed = disnake.Embed(
            title=f"🎫 {title}", 
            description=f"**Детали обращения:**\n```text\n{desc}\n```", 
            color=0x8B5CF6
        )
        embed.set_author(name=f"Создатель: {inter.author.display_name}", icon_url=inter.author.display_avatar.url if inter.author.display_avatar else None)
        
        if media: 
            embed.add_field(name="📎 Прикрепленные материалы", value=media, inline=False)
            
        embed.add_field(name="👤 Пользователь", value=inter.author.mention, inline=True)
        embed.add_field(name="🛠️ Статус", value="🟢 Ожидает ответа", inline=True)
        embed.set_footer(text=f"ID Тикета: {ticket_num} • Ожидайте ответа поддержки")
        embed.timestamp = disnake.utils.utcnow()

        await ticket_channel.send(content=f"{inter.author.mention}", embed=embed, view=TicketControlView(is_closed=False))

        ticket_data = {
            "id": str(ticket_channel.id),
            "name": channel_name,
            "type": self.ticket_type,
            "status": "open",
            "creator_id": str(inter.author.id),
            "creator_name": inter.author.display_name,
            "created_at": str(int(disnake.utils.utcnow().timestamp()))
        }
        await bot.redis.hset(f"ticket:{ticket_channel.id}", mapping=ticket_data)

        await inter.edit_original_message(content=f"✅ Ваш тикет успешно создан: {ticket_channel.mention}")

class TicketSelect(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Серверный", value="server", description="Вопросы по игровому серверу", emoji="🎮"),
            disnake.SelectOption(label="Технический", value="tech", description="Ошибки, баги, проблемы с донатом", emoji="🛠️")
        ]
        super().__init__(placeholder="Выберите категорию обращения...", min_values=1, max_values=1, options=options, custom_id="ticket_create_select")

    async def callback(self, inter: disnake.MessageInteraction):
        ticket_type = self.values[0]
        await inter.response.send_modal(modal=TicketModal(ticket_type))

class TicketCreateView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.views_added = False
        self.bot.loop.create_task(self.web_control_listener())

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.views_added:
            self.bot.add_view(TicketCreateView())
            self.bot.add_view(TicketControlView(is_closed=False))
            self.bot.add_view(TicketControlView(is_closed=True))
            self.views_added = True

    @commands.command(name="setup_tickets")
    async def setup_tickets_prefix(self, ctx: commands.Context):
        embed = disnake.Embed(
            title="🎧 Центр поддержки",
            description="> Добро пожаловать!\n\nЕсли у вас возникла проблема или вопрос, выберите подходящую категорию в выпадающем меню ниже. Бот автоматически создаст приватный канал для общения с администрацией.",
            color=0x8B5CF6
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="KwargsssBot • Support System")

        await ctx.send(embed=embed, view=TicketCreateView())
        try: await ctx.message.delete()
        except: pass

    @commands.Cog.listener("on_message")
    async def ticket_message_sync(self, message: disnake.Message):
        """Трансляция сообщений из Discord в веб-панель"""
        if message.author.bot and not message.embeds:
            return

        ticket_data = await self.bot.redis.hgetall(f"ticket:{message.channel.id}")
        if not ticket_data: return

        embeds_data = [e.to_dict() for e in message.embeds]
        
        payload = {
            "id": str(message.id),
            "content": message.content,
            "author": message.author.display_name,
            "avatar": message.author.display_avatar.url if message.author.display_avatar else None,
            "is_bot": message.author.bot,
            "embeds": embeds_data,
            "timestamp": message.created_at.timestamp()
        }
        await self.bot.redis.publish(f"ticket_chat:{message.channel.id}", json.dumps(payload))

    async def web_control_listener(self):
        await self.bot.wait_until_ready()
        pubsub = self.bot.redis.pubsub()
        await pubsub.subscribe("web_ticket_controls")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    action = data.get("action")
                    ticket_id = int(data.get("ticket_id"))
                    channel = self.bot.get_channel(ticket_id)
                    
                    if not channel: continue

                    if action == "send_message":
                        embed = disnake.Embed(description=data["content"], color=0x8B5CF6)
                        embed.set_footer(text=f"Сотрудник поддержки: {data['author_name']}", icon_url=data.get("author_avatar"))
                        embed.timestamp = disnake.utils.utcnow()
                        await channel.send(embed=embed)

                    elif action == "close":
                        ticket_data = await self.bot.redis.hgetall(f"ticket:{channel.id}")
                        creator_id = int(ticket_data.get("creator_id", 0))
                        if creator_id:
                            member = channel.guild.get_member(creator_id)
                            if member: await channel.set_permissions(member, overwrite=None)
                                
                        close_embed = disnake.Embed(
                            title="🔒 Тикет закрыт",
                            description=f"Работа по данному обращению приостановлена администратором **{data['admin_name']}** (через Web-панель).",
                            color=0xEF4444
                        )
                        await channel.send(embed=close_embed, view=TicketControlView(is_closed=True))
                        await self.bot.redis.hset(f"ticket:{channel.id}", "status", "closed")

                    elif action == "open":
                        ticket_data = await self.bot.redis.hgetall(f"ticket:{channel.id}")
                        creator_id = int(ticket_data.get("creator_id", 0))
                        if creator_id:
                            member = channel.guild.get_member(creator_id)
                            if member: await channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
                                
                        open_embed = disnake.Embed(
                            title="🔓 Тикет возобновлен",
                            description=f"Администратор **{data['admin_name']}** возобновил работу тикета (через Web-панель).",
                            color=0x10B981
                        )
                        await channel.send(embed=open_embed, view=TicketControlView(is_closed=False))
                        await self.bot.redis.hset(f"ticket:{channel.id}", "status", "open")

                    elif action == "delete":
                        transcript = await chat_exporter.export(channel)
                        await self.bot.redis.set(f"transcript:{channel.id}", transcript)
                        if transcript:
                            archive_channel = channel.guild.get_channel(int(os.getenv("ARCHIVE_CHANNEL_ID")))
                            if archive_channel:
                                transcript_file = disnake.File(io.BytesIO(transcript.encode()), filename=f"archive-{channel.name}.html")
                                archive_embed = disnake.Embed(
                                    title="🗃️ Новый архив тикета",
                                    description=f"**Канал:** `{channel.name}`\n**Закрыл (Web):** {data['admin_name']}",
                                    color=0x8B5CF6
                                )
                                await archive_channel.send(embed=archive_embed, file=transcript_file)
                        
                        await channel.delete()
                        await self.bot.redis.hset(f"ticket:{channel.id}", "status", "archived")

                except Exception as e:
                    print(f"[Ticket Web Control Error]: {e}")

    @commands.Cog.listener("on_button_click")
    async def ticket_button_handler(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in ["ticket_close", "ticket_delete", "ticket_open"]:
            return

        admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
        support_role_id = int(os.getenv("SUPPORT_ROLE_ID"))
        user_roles = [r.id for r in inter.author.roles]
        
        is_staff = admin_role_id in user_roles or support_role_id in user_roles
        is_admin = admin_role_id in user_roles

        if inter.component.custom_id == "ticket_close":
            if not is_staff: return await inter.response.send_message("У вас нет прав для закрытия тикета.", ephemeral=True)
            await inter.response.defer()
            
            creator_id = None
            if inter.channel.topic and "от " in inter.channel.topic:
                try: creator_id = int(inter.channel.topic.split("от ")[1])
                except: pass

            if creator_id:
                member = inter.guild.get_member(creator_id)
                if member: await inter.channel.set_permissions(member, overwrite=None)
            
            await inter.edit_original_message(view=TicketControlView(is_closed=True))
            close_embed = disnake.Embed(title="🔒 Тикет закрыт", description=f"Работа по данному обращению приостановлена агентом поддержки {inter.author.mention}.\nПользователь больше не может писать в этот канал.", color=0xEF4444)
            await inter.channel.send(embed=close_embed)
            await inter.bot.redis.hset(f"ticket:{inter.channel.id}", "status", "closed")

        elif inter.component.custom_id == "ticket_open":
            if not is_staff: return await inter.response.send_message("У вас нет прав для возобновиления тикета.", ephemeral=True)
            await inter.response.defer()
            
            creator_id = None
            if inter.channel.topic and "от " in inter.channel.topic:
                try: creator_id = int(inter.channel.topic.split("от ")[1])
                except: pass

            if creator_id:
                member = inter.guild.get_member(creator_id)
                if member: await inter.channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)

            await inter.edit_original_message(view=TicketControlView(is_closed=False))
            open_embed = disnake.Embed(title="🔓 Тикет возобновлен", description=f"Агент {inter.author.mention} отменил закрытие тикета.\nПрава доступа пользователя <@{creator_id}> успешно восстановлены.", color=0x10B981)
            await inter.channel.send(embed=open_embed)
            await inter.bot.redis.hset(f"ticket:{inter.channel.id}", "status", "open")

        elif inter.component.custom_id == "ticket_delete":
            if not is_admin: return await inter.response.send_message("Удалять тикеты могут только администраторы.", ephemeral=True)
            await inter.response.defer()
            
            delete_embed = disnake.Embed(title="⏳ Удаление...", description="Генерация HTML-архива и очистка канала.", color=0xF59E0B)
            await inter.channel.send(embed=delete_embed)

            transcript = await chat_exporter.export(inter.channel)
            if transcript:
                await inter.bot.redis.set(f"transcript:{inter.channel.id}", transcript)
                archive_channel = inter.guild.get_channel(int(os.getenv("ARCHIVE_CHANNEL_ID")))
                if archive_channel:
                    transcript_file = disnake.File(io.BytesIO(transcript.encode()), filename=f"archive-{inter.channel.name}.html")
                    archive_embed = disnake.Embed(title="🗃️ Новый архив тикета", description=f"**Канал:** `{inter.channel.name}`\n**Закрыл:** {inter.author.mention}", color=0x8B5CF6)
                    await archive_channel.send(embed=archive_embed, file=transcript_file)
            
            await inter.channel.delete()
            await inter.bot.redis.hset(f"ticket:{inter.channel.id}", "status", "archived")

def setup(bot):
    bot.add_cog(TicketCog(bot))