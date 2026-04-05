import disnake

from config import Config


class TicketV2View(disnake.ui.View):
    def __init__(self, is_closed: bool, text: str, color: int = 0x8B5CF6, disabled: bool = False):
        super().__init__(timeout=None)
        self.is_closed = is_closed
        
        if not is_closed:
            self.add_item(disnake.ui.Button(
                label="Закрыть Тикет", style=disnake.ButtonStyle.secondary, 
                custom_id="ticket_close", emoji="🔒", disabled=disabled
            ))
        else:
            self.add_item(disnake.ui.Button(
                label="Открыть Тикет", style=disnake.ButtonStyle.success, 
                custom_id="ticket_open", emoji="🔓", disabled=disabled
            ))
            self.add_item(disnake.ui.Button(
                label="Удалить Тикет", style=disnake.ButtonStyle.danger, 
                custom_id="ticket_delete", emoji="🗑️", disabled=disabled
            ))
            
        self.v2_components = [
            disnake.ui.Container(
                disnake.ui.TextDisplay(text),
                disnake.ui.ActionRow(*self.children),
                accent_colour=disnake.Colour(color)
            )
        ]

    def to_components(self):
        return [c.to_component_dict() for c in self.v2_components]

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
        self.select = TicketSelect()
        self.add_item(self.select)
        
        text = (
            "## 🎧 Центр поддержки\n"
            "> Добро пожаловать!\n\n"
            "Если у вас возникла проблема или вопрос, выберите подходящую категорию в выпадающем меню ниже. "
            "Бот автоматически создаст приватный канал для общения с администрацией.\n\n"
            "*KwargsssBot • Support System*"
        )
        
        self.v2_components = [
            disnake.ui.Container(
                disnake.ui.TextDisplay(text),
                disnake.ui.ActionRow(self.select),
                accent_colour=disnake.Colour(0x8B5CF6)
            )
        ]

    def to_components(self):
        return [c.to_component_dict() for c in self.v2_components]

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

        ticket_data = {
            "id": str(ticket_channel.id), "name": channel_name, "type": self.ticket_type,
            "status": "open", "creator_id": str(inter.author.id), "creator_name": inter.author.display_name,
            "created_at": str(int(disnake.utils.utcnow().timestamp()))
        }
        await bot.redis.hset(f"ticket:{ticket_channel.id}", mapping=ticket_data)

        type_str = "Серверный Тикет" if self.ticket_type == "server" else "Технический Тикет"
        text = f"## 🎫 {title}\n"
        text += f"👤 **Создатель:** {inter.author.mention}\n"
        text += f"🛠️ **Статус:** 🟢 Ожидает ответа\n\n"
        text += f"> {desc}\n\n"
        if media:
            text += f"📎 **Материалы:** {media}\n\n"
        text += f"*{type_str} • ID: {ticket_num} • Ожидайте ответа поддержки*"

        view = TicketV2View(is_closed=False, text=text, color=0x8B5CF6)
        msg = await ticket_channel.send(view=view, flags=disnake.MessageFlags(is_components_v2=True))

        await bot.redis.set(f"v2_msg_text:{msg.id}", text)
        await bot.redis.set(f"v2_msg_color:{msg.id}", str(0x8B5CF6))

        await inter.edit_original_message(content=f"✅ Ваш тикет успешно создан: {ticket_channel.mention}")