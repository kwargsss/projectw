import disnake

from config import Config

class TicketControlView(disnake.ui.View):
    def __init__(self, is_closed: bool = False):
        super().__init__(timeout=None)
        if not is_closed:
            self.add_item(disnake.ui.Button(
                label="Закрыть Тикет", style=disnake.ButtonStyle.secondary, 
                custom_id="ticket_close", emoji="🔒"
            ))
        else:
            self.add_item(disnake.ui.Button(
                label="Открыть Тикет", style=disnake.ButtonStyle.success, 
                custom_id="ticket_open", emoji="🔓"
            ))
            self.add_item(disnake.ui.Button(
                label="Удалить Тикет", style=disnake.ButtonStyle.danger, 
                custom_id="ticket_delete", emoji="🗑️"
            ))

class TicketModal(disnake.ui.Modal):
    def __init__(self, ticket_type: str):
        self.ticket_type = ticket_type
        components = [
            disnake.ui.TextInput(label="Заголовок проблемы", placeholder="Кратко опишите суть...", custom_id="ticket_title", style=disnake.TextInputStyle.short, max_length=256),
            disnake.ui.TextInput(label="Описание проблемы", placeholder="Опишите проблему максимально подробно...", custom_id="ticket_desc", style=disnake.TextInputStyle.paragraph, max_length=4000),
            disnake.ui.TextInput(label="Ссылка на видео/скриншот (необязательно)", placeholder="https://...", custom_id="ticket_media", style=disnake.TextInputStyle.short, required=False),
        ]
        title = "Серверный Тикет" if ticket_type == "server" else "Технический Тикет"
        super().__init__(title=title, custom_id=f"modal_ticket_{ticket_type}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        bot = inter.bot
        
        title = inter.text_values["ticket_title"]
        desc = inter.text_values["ticket_desc"]
        media = inter.text_values.get("ticket_media")

        cat_id = Config.TICKET_CATEGORY_SERVER if self.ticket_type == "server" else Config.TICKET_CATEGORY_TECH
        category = inter.guild.get_channel(cat_id)
        
        redis_key = f"ticket_count_{self.ticket_type}"
        ticket_num = await bot.redis.incr(redis_key)
        type_short = "server" if self.ticket_type == "server" else "tech"
        channel_name = f"ticket-{type_short}-{ticket_num}"

        admin_role = inter.guild.get_role(Config.ADMIN_ROLE_ID)
        support_role = inter.guild.get_role(Config.SUPPORT_ROLE_ID)
        
        overwrites = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            bot.user: disnake.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        if admin_role: overwrites[admin_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role: overwrites[support_role] = disnake.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await inter.guild.create_text_channel(
            name=channel_name, category=category, overwrites=overwrites, topic=f"Тикет #{ticket_num} от {inter.author.id}"
        )

        embed = disnake.Embed(title=f"🎫 {title}", description=f"**Детали обращения:**\n```text\n{desc}\n```", color=0x8B5CF6)
        embed.set_author(name=f"Создатель: {inter.author.display_name}", icon_url=inter.author.display_avatar.url if inter.author.display_avatar else None)
        
        if media: embed.add_field(name="📎 Прикрепленные материалы", value=media, inline=False)
        embed.add_field(name="👤 Пользователь", value=inter.author.mention, inline=True)
        embed.add_field(name="🛠️ Статус", value="🟢 Ожидает ответа", inline=True)
        embed.set_footer(text=f"ID Тикета: {ticket_num} • Ожидайте ответа поддержки")
        embed.timestamp = disnake.utils.utcnow()

        await ticket_channel.send(content=f"{inter.author.mention}", embed=embed, view=TicketControlView(is_closed=False))

        ticket_data = {
            "id": str(ticket_channel.id), "name": channel_name, "type": self.ticket_type,
            "status": "open", "creator_id": str(inter.author.id), "creator_name": inter.author.display_name,
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
        await inter.response.send_modal(modal=TicketModal(self.values[0]))

class TicketCreateView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())