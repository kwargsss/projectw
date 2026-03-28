import disnake
import io
import chat_exporter
import json

from disnake.ext import commands
from config import Config
from utils.permissions import is_admin, is_staff, admin_only
from ui.ticket_ui import TicketCreateView, TicketControlView


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
    @admin_only()
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
        if message.author.bot and not message.embeds: return

        ticket_data = await self.bot.redis.hgetall(f"ticket:{message.channel.id}")
        if not ticket_data: return

        payload = {
            "id": str(message.id), "content": message.content, "author": message.author.display_name,
            "avatar": message.author.display_avatar.url if message.author.display_avatar else None,
            "is_bot": message.author.bot, "embeds": [e.to_dict() for e in message.embeds],
            "timestamp": message.created_at.timestamp()
        }
        await self.bot.redis.publish(f"ticket_chat:{message.channel.id}", json.dumps(payload))

    async def _change_ticket_status(self, channel: disnake.TextChannel, status: str, admin_name: str, admin_mention: str = None):
        ticket_data = await self.bot.redis.hgetall(f"ticket:{channel.id}")
        creator_id = int(ticket_data.get("creator_id", 0))
        member = channel.guild.get_member(creator_id) if creator_id else None

        if status == "closed":
            if member: await channel.set_permissions(member, overwrite=None)
            desc = f"Работа по данному обращению приостановлена администратором/агентом: {admin_mention or admin_name}."
            embed = disnake.Embed(title="🔒 Тикет закрыт", description=desc, color=0xEF4444)
            view = TicketControlView(is_closed=True)
        else:
            if member: await channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            desc = f"Администратор/агент {admin_mention or admin_name} возобновил работу тикета."
            embed = disnake.Embed(title="🔓 Тикет возобновлен", description=desc, color=0x10B981)
            view = TicketControlView(is_closed=False)

        await channel.send(embed=embed, view=view)
        await self.bot.redis.hset(f"ticket:{channel.id}", "status", status)

    async def _archive_ticket(self, channel: disnake.TextChannel, admin_name: str):
        transcript = await chat_exporter.export(channel)
        if transcript:
            await self.bot.redis.set(f"transcript:{channel.id}", transcript)
            archive_channel = channel.guild.get_channel(Config.ARCHIVE_CHANNEL_ID)
            if archive_channel:
                transcript_file = disnake.File(io.BytesIO(transcript.encode()), filename=f"archive-{channel.name}.html")
                archive_embed = disnake.Embed(title="🗃️ Новый архив тикета", description=f"**Канал:** `{channel.name}`\n**Удалил:** {admin_name}", color=0x8B5CF6)
                await archive_channel.send(embed=archive_embed, file=transcript_file)
        
        await channel.delete()
        await self.bot.redis.hset(f"ticket:{channel.id}", "status", "archived")

    async def web_control_listener(self):
        await self.bot.wait_until_ready()
        pubsub = self.bot.redis.pubsub()
        await pubsub.subscribe("web_ticket_controls")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    action = data.get("action")
                    channel = self.bot.get_channel(int(data.get("ticket_id")))
                    if not channel: continue

                    if action == "send_message":
                        embed = disnake.Embed(description=data["content"], color=0x8B5CF6)
                        embed.set_footer(text=f"Сотрудник поддержки: {data['author_name']}", icon_url=data.get("author_avatar"))
                        embed.timestamp = disnake.utils.utcnow()
                        await channel.send(embed=embed)
                    elif action == "close":
                        await self._change_ticket_status(channel, "closed", f"**{data['admin_name']}** (Web)")
                    elif action == "open":
                        await self._change_ticket_status(channel, "open", f"**{data['admin_name']}** (Web)")
                    elif action == "delete":
                        await self._archive_ticket(channel, f"{data['admin_name']} (Web)")

                except Exception as e:
                    self.bot.logger.error(f"[Ticket Web Control Error]: {e}")

    @commands.Cog.listener("on_button_click")
    async def ticket_button_handler(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in ["ticket_close", "ticket_delete", "ticket_open"]: return

        if inter.component.custom_id == "ticket_close":
            if not is_staff(inter.author): 
                return await inter.response.send_message("❌ У вас нет прав для закрытия тикета.", ephemeral=True)
            await inter.response.defer()
            await inter.edit_original_message(view=TicketControlView(is_closed=True))
            await self._change_ticket_status(inter.channel, "closed", inter.author.display_name, inter.author.mention)

        elif inter.component.custom_id == "ticket_open":
            if not is_staff(inter.author): 
                return await inter.response.send_message("❌ У вас нет прав для открытия тикета.", ephemeral=True)
            await inter.response.defer()
            await inter.edit_original_message(view=TicketControlView(is_closed=False))
            await self._change_ticket_status(inter.channel, "open", inter.author.display_name, inter.author.mention)

        elif inter.component.custom_id == "ticket_delete":
            if not is_admin(inter.author): 
                return await inter.response.send_message("❌ Удалять тикеты могут только Администраторы.", ephemeral=True)
            await inter.response.defer()
            await inter.channel.send(embed=disnake.Embed(title="⏳ Удаление...", description="Генерация HTML-архива и очистка канала.", color=0xF59E0B))
            await self._archive_ticket(inter.channel, inter.author.mention)

def setup(bot):
    bot.add_cog(TicketCog(bot))