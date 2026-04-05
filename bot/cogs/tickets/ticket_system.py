import disnake
import io
import chat_exporter
import json
import asyncio

from disnake.ext import commands
from config import Config
from utils.permissions import is_admin, is_staff, admin_only
from ui.ticket_ui import TicketCreateView, TicketV2View


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.views_added = False
        self.bot.loop.create_task(self.web_control_listener())

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.views_added:
            self.bot.add_view(TicketCreateView())
            self.views_added = True

    @commands.command(name="setup_tickets")
    @admin_only()
    async def setup_tickets_prefix(self, ctx: commands.Context):
        await ctx.send(view=TicketCreateView(), flags=disnake.MessageFlags(is_components_v2=True))
        try: await ctx.message.delete()
        except: pass

    @commands.Cog.listener("on_message")
    async def ticket_message_sync(self, message: disnake.Message):
        if message.author.bot and not message.embeds and not (hasattr(message, 'flags') and message.flags.is_components_v2): return

        ticket_data = await self.bot.redis.hgetall(f"ticket:{message.channel.id}")
        if not ticket_data: return

        content = message.content
        embeds_data = [e.to_dict() for e in message.embeds]

        if hasattr(message, 'flags') and message.flags.is_components_v2:
            await asyncio.sleep(0.5) 
            raw_v2_text = await self.bot.redis.get(f"v2_msg_text:{message.id}")
            if raw_v2_text:
                v2_text = raw_v2_text.decode('utf-8') if isinstance(raw_v2_text, bytes) else raw_v2_text
                
                raw_color = await self.bot.redis.get(f"v2_msg_color:{message.id}")
                color_str = raw_color.decode('utf-8') if isinstance(raw_color, bytes) else raw_color
                v2_color = int(color_str) if color_str else 0x8B5CF6
                
                embeds_data.append({
                    "description": v2_text,
                    "color": v2_color
                })

        payload = {
            "id": str(message.id), "content": content, "author": message.author.display_name,
            "avatar": message.author.display_avatar.url if message.author.display_avatar else None,
            "is_bot": message.author.bot, "embeds": embeds_data,
            "timestamp": message.created_at.timestamp()
        }
        
        payload_json = json.dumps(payload)
        await self.bot.redis.rpush(f"ticket_messages:{message.channel.id}", payload_json)
        await self.bot.redis.publish(f"ticket_chat:{message.channel.id}", payload_json)

    async def _change_ticket_status(self, channel: disnake.TextChannel, status: str, admin_name: str, admin_mention: str = None):
        ticket_data = await self.bot.redis.hgetall(f"ticket:{channel.id}")
        creator_id = int(ticket_data.get(b"creator_id", 0) if isinstance(ticket_data.get(b"creator_id"), bytes) else ticket_data.get("creator_id", 0))
        member = channel.guild.get_member(creator_id) if creator_id else None

        if status == "closed":
            if member: await channel.set_permissions(member, overwrite=None)
            text = f"## 🔒 Тикет закрыт\nРабота по данному обращению приостановлена.\n\n*Администратор: {admin_mention or admin_name}*"
            color = 0xEF4444
            view = TicketV2View(is_closed=True, text=text, color=color)
        else:
            if member: await channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True)
            text = f"## 🔓 Тикет возобновлен\nРабота по данному обращению возобновлена.\n\n*Администратор: {admin_mention or admin_name}*"
            color = 0x10B981
            view = TicketV2View(is_closed=False, text=text, color=color)

        msg = await channel.send(view=view, flags=disnake.MessageFlags(is_components_v2=True))
        await self.bot.redis.set(f"v2_msg_text:{msg.id}", text)
        await self.bot.redis.set(f"v2_msg_color:{msg.id}", str(color))
        await self.bot.redis.hset(f"ticket:{channel.id}", "status", status)

    async def _archive_ticket(self, channel: disnake.TextChannel, admin_name: str):
        transcript = await chat_exporter.export(channel)
        if transcript:
            await self.bot.redis.set(f"transcript:{channel.id}", transcript)
            archive_channel = channel.guild.get_channel(Config.ARCHIVE_CHANNEL_ID)
            if archive_channel:
                transcript_file = disnake.File(io.BytesIO(transcript.encode()), filename=f"archive-{channel.name}.html")
                embed = disnake.Embed(
                    title="🗃️ Новый архив тикета", 
                    description=f"**Канал:** `{channel.name}`\n**Удалил:** {admin_name}", 
                    color=disnake.Color.orange()
                )
                await archive_channel.send(file=transcript_file, embed=embed)
        
        await channel.delete()
        await self.bot.redis.hset(f"ticket:{channel.id}", "status", "archived")
        await self.bot.redis.delete(f"ticket_messages:{channel.id}")

    async def web_control_listener(self):
        import redis.exceptions
        await self.bot.wait_until_ready()
        
        while True:
            try:
                pubsub = self.bot.redis.pubsub()
                await pubsub.subscribe("web_ticket_controls")
                
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60.0)
                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            action = data.get("action")
                            channel = self.bot.get_channel(int(data.get("ticket_id")))
                            if not channel: continue

                            if action == "send_message":
                                text = f"## 💬 Сообщение от поддержки\n> {data['content']}\n\n*{data['author_name']}*"
                                components = [disnake.ui.Container(disnake.ui.TextDisplay(text), accent_colour=disnake.Colour(0x8B5CF6))]
                                msg = await channel.send(components=components, flags=disnake.MessageFlags(is_components_v2=True))
                                
                                await self.bot.redis.set(f"v2_msg_text:{msg.id}", text)
                                await self.bot.redis.set(f"v2_msg_color:{msg.id}", str(0x8B5CF6))
                            elif action == "close":
                                await self._change_ticket_status(channel, "closed", f"**{data['admin_name']}** (Web)")
                            elif action == "open":
                                await self._change_ticket_status(channel, "open", f"**{data['admin_name']}** (Web)")
                            elif action == "delete":
                                await self._archive_ticket(channel, f"{data['admin_name']} (Web)")
                        except Exception as inner_e:
                            self.bot.logger.error(f"[Ticket Web Control Processing Error]: {inner_e}")
                    await pubsub.ping()
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                await asyncio.sleep(5)
            except Exception as e:
                await asyncio.sleep(5)

    @commands.Cog.listener("on_button_click")
    async def ticket_button_handler(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in ["ticket_close", "ticket_delete", "ticket_open"]: return

        raw_text = await self.bot.redis.get(f"v2_msg_text:{inter.message.id}")
        text = raw_text.decode('utf-8') if isinstance(raw_text, bytes) else raw_text
        if not text: text = "## 🎫 Тикет\nДетали загружены из архива."
        
        raw_color = await self.bot.redis.get(f"v2_msg_color:{inter.message.id}")
        color_str = raw_color.decode('utf-8') if isinstance(raw_color, bytes) else raw_color
        color = int(color_str) if color_str else 0x8B5CF6

        if inter.component.custom_id == "ticket_close":
            if not is_staff(inter.author): 
                return await inter.response.send_message("❌ У вас нет прав для закрытия тикета.", ephemeral=True)
            view = TicketV2View(is_closed=False, text=text, color=color, disabled=True)
            await inter.response.edit_message(view=view, flags=disnake.MessageFlags(is_components_v2=True))
            await self._change_ticket_status(inter.channel, "closed", inter.author.display_name, inter.author.mention)

        elif inter.component.custom_id == "ticket_open":
            if not is_staff(inter.author): 
                return await inter.response.send_message("❌ У вас нет прав для открытия тикета.", ephemeral=True)
            view = TicketV2View(is_closed=True, text=text, color=color, disabled=True)
            await inter.response.edit_message(view=view, flags=disnake.MessageFlags(is_components_v2=True))
            await self._change_ticket_status(inter.channel, "open", inter.author.display_name, inter.author.mention)

        elif inter.component.custom_id == "ticket_delete":
            if not is_admin(inter.author): 
                return await inter.response.send_message("❌ Удалять тикеты могут только Администраторы.", ephemeral=True)
            view = TicketV2View(is_closed=True, text=text, color=color, disabled=True)
            await inter.response.edit_message(view=view, flags=disnake.MessageFlags(is_components_v2=True))
            
            del_text = "## ⏳ Удаление...\nГенерация HTML-архива и очистка канала."
            del_comps = [disnake.ui.Container(disnake.ui.TextDisplay(del_text), accent_colour=disnake.Colour(0xF59E0B))]
            await inter.channel.send(components=del_comps, flags=disnake.MessageFlags(is_components_v2=True))
            await self._archive_ticket(inter.channel, inter.author.mention)

def setup(bot):
    bot.add_cog(TicketCog(bot))