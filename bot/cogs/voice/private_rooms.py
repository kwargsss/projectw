import disnake
import asyncio
import json
import random
import redis.exceptions

from disnake.ext import commands
from ui.voice_ui import PrivateVoiceControlView

class PrivateRoomsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.task_started:
            self.bot.add_view(PrivateVoiceControlView())
            self.bot.loop.create_task(self.web_deploy_listener())
            self.task_started = True

    async def web_deploy_listener(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                pubsub = self.bot.redis.pubsub()
                await pubsub.subscribe("system_controls")
                
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60.0)
                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            action = data.get("action")
                            if action == "deploy_private_voice":
                                await self.deploy_setup(data["guild_id"])
                            elif action == "disable_private_voice":
                                await self.disable_setup(data["guild_id"])
                        except Exception as e:
                            self.bot.logger.error(f"[PrivateVoice] Ошибка деплоя: {e}")
                    await pubsub.ping()
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)

    async def deploy_setup(self, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if not guild: return

        category = await guild.create_category("🔒 Приватные каналы")

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(send_messages=False),
            guild.me: disnake.PermissionOverwrite(send_messages=True, embed_links=True)
        }
        
        text_channel = await category.create_text_channel("💬・управление", overwrites=overwrites)
        creator_channel = await category.create_voice_channel("➕・Создать канал", user_limit=2)

        embed = disnake.Embed(
            title="🎛️ Управление приватным каналом",
            description="Зайдите в `➕・Создать канал`, чтобы создать комнату.\nИспользуйте меню ниже для настройки вашей комнаты.",
            color=0x8B5CF6
        )
        msg = await text_channel.send(embed=embed, view=PrivateVoiceControlView())

        setup_data = {
            "category_id": category.id,
            "text_channel_id": text_channel.id,
            "creator_channel_id": creator_channel.id,
            "control_message_id": msg.id
        }
        await self.bot.redis.set(f"pv_setup:{guild_id}", json.dumps(setup_data))
        self.bot.logger.info(f"[PrivateVoice] Сетап развернут на сервере {guild.name}")

    async def disable_setup(self, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if not guild: return

        setup_str = await self.bot.redis.get(f"pv_setup:{guild_id}")
        if setup_str:
            setup_data = json.loads(setup_str)
            try:
                creator_channel = guild.get_channel(setup_data.get("creator_channel_id"))
                if creator_channel: await creator_channel.delete()
                
                text_channel = guild.get_channel(setup_data.get("text_channel_id"))
                if text_channel: await text_channel.delete()
                
                category = guild.get_channel(setup_data.get("category_id"))
                if category: await category.delete()
            except Exception as e:
                self.bot.logger.error(f"[PrivateVoice] Ошибка удаления каналов: {e}")

            await self.bot.redis.delete(f"pv_setup:{guild_id}")
            self.bot.logger.info(f"[PrivateVoice] Сетап полностью удален на сервере {guild.name}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot: return
        guild_id = member.guild.id

        if after.channel is not None and before.channel != after.channel:
            setup_str = await self.bot.redis.get(f"pv_setup:{guild_id}")
            if not setup_str: return
            setup_data = json.loads(setup_str)

            if after.channel.id == setup_data.get("creator_channel_id"):
                settings_str = await self.bot.redis.get(f"pv_settings:{guild_id}")
                settings = json.loads(settings_str) if settings_str else {
                    "is_enabled": True, "template": "🎧 {nick}", "default_limit": 0, "default_bitrate": 64000
                }

                if not settings.get("is_enabled", True): return

                existing_id = await self.bot.redis.get(f"pv_user:{member.id}")
                if existing_id:
                    old_channel = member.guild.get_channel(int(existing_id))
                    if old_channel:
                        return await member.move_to(old_channel)
                    else:
                        await self.bot.redis.delete(f"pv_user:{member.id}")

                category = member.guild.get_channel(setup_data.get("category_id"))
                if not category: return

                game_name = "Ничего"
                for activity in member.activities:
                    if activity.type == disnake.ActivityType.playing:
                        game_name = activity.name
                        break

                channel_name = settings["template"]
                channel_name = channel_name.replace("{user}", member.name)
                channel_name = channel_name.replace("{nick}", member.display_name)
                channel_name = channel_name.replace("{game}", game_name)
                channel_name = channel_name.replace("{server}", member.guild.name)

                new_channel = await category.create_voice_channel(
                    name=channel_name,
                    user_limit=settings["default_limit"],
                    bitrate=min(settings["default_bitrate"], member.guild.bitrate_limit)
                )
                
                await new_channel.set_permissions(member, connect=True, view_channel=True, manage_channels=False)

                await self.bot.redis.set(f"pv_owner:{new_channel.id}", member.id)
                await self.bot.redis.set(f"pv_user:{member.id}", new_channel.id)
                
                try: await member.move_to(new_channel)
                except: await new_channel.delete()

        if before.channel is not None and before.channel != after.channel:
            owner_id_str = await self.bot.redis.get(f"pv_owner:{before.channel.id}")
            if owner_id_str:
                owner_id = int(owner_id_str)
                members_in_channel = [m for m in before.channel.members if not m.bot]
                
                if not members_in_channel:
                    await self.bot.redis.delete(f"pv_owner:{before.channel.id}")
                    await self.bot.redis.delete(f"pv_user:{owner_id}")
                    try: await before.channel.delete()
                    except: pass
                
                elif owner_id == member.id:
                    new_owner = random.choice(members_in_channel)
                    await self.bot.redis.set(f"pv_owner:{before.channel.id}", new_owner.id)
                    await self.bot.redis.delete(f"pv_user:{member.id}")
                    await self.bot.redis.set(f"pv_user:{new_owner.id}", before.channel.id)
                    
                    await before.channel.set_permissions(member, connect=None, view_channel=None)
                    await before.channel.set_permissions(new_owner, connect=True, view_channel=True)
                    try: await new_owner.send(f"👑 Владелец покинул канал **{before.channel.name}**. Теперь вы управляете им!")
                    except: pass

def setup(bot):
    bot.add_cog(PrivateRoomsCog(bot))