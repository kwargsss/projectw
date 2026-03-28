import disnake
import json

from disnake.ext import commands
from utils.formatters import format_text
from utils.embed_builder import build_v1_embed, build_v2_components

class NotificationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_notification(self, member: disnake.Member, event_type: str):
        settings_str = await self.bot.redis.get("notification_settings")
        if not settings_str: return
        
        try:
            settings = json.loads(settings_str)
            config = settings.get(event_type)
            event_name = "Приветствие" if event_type == "welcome" else "Прощание"
            
            if not config or not config.get("enabled"): 
                return

            chan_id = str(config.get("channel_id", ""))
            if not chan_id or not chan_id.isdigit(): 
                self.bot.logger.warning(f"[ВНИМАНИЕ] {event_name} включено, но канал не выбран! Отмена.")
                return

            channel_id = int(chan_id)
            channel = member.guild.get_channel(channel_id) or await member.guild.fetch_channel(channel_id)
            if not channel: 
                self.bot.logger.warning(f"[ВНИМАНИЕ] Канал {channel_id} для {event_name} не найден!")
                return

            content = format_text(config.get("content"), member)

            if config.get("embed_type") == "v2":
                for block in config.get('blocks', []):
                    if block.get('content'): block['content'] = format_text(block['content'], member)
                    if block.get('url'): block['url'] = format_text(block['url'], member)
                    if block.get('button_label'): block['button_label'] = format_text(block['button_label'], member)
                    if block.get('button_url'): block['button_url'] = format_text(block['button_url'], member)
                    if block.get('description'): block['description'] = format_text(block['description'], member)

                config['footer'] = {"text": "Система оповещений"} 
                components = build_v2_components(config)
                
                if content:
                    components[0].components.insert(0, disnake.ui.Separator(divider=True))
                    components[0].components.insert(0, disnake.ui.TextDisplay(content))

                await channel.send(components=components, flags=disnake.MessageFlags(is_components_v2=True))
                self.bot.logger.info(f"[ACTION] {event_name} (V2) успешно отправлено для {member.name}.")

            else:
                config['title'] = format_text(config.get('title'), member)
                config['description'] = format_text(config.get('description'), member)
                embed = build_v1_embed(config)

                await channel.send(content=content if content else None, embed=embed)
                self.bot.logger.info(f"[ACTION] {event_name} (V1) успешно отправлено для {member.name}.")
                
        except Exception as e:
            self.bot.logger.error(f"[ERROR] Ошибка оповещения {event_type} для {member.name}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        await self.send_notification(member, "welcome")

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        await self.send_notification(member, "goodbye")

def setup(bot):
    bot.add_cog(NotificationsCog(bot))