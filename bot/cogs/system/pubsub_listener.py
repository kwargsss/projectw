import json
import asyncio
import disnake
import redis.exceptions

from disnake.ext import commands
from utils.embed_builder import build_v1_embed, build_v2_components


class PubSubListenerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.pubsub_listener())
        self.bot.loop.create_task(self.pubsub_v2_listener())

    async def pubsub_listener(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                pubsub = self.bot.redis.pubsub()
                await pubsub.subscribe("projectw_embed_commands")
                self.bot.logger.info("[SYSTEM] Бот начал прослушивание канала Embed команд.")

                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60.0)
                    
                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            channel_id = int(data.get('channel_id'))
                            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

                            embed = build_v1_embed(data)
                            content = data.get('content')
                            
                            await channel.send(content=content, embed=embed)
                            self.bot.logger.info(f"[ACTION] Embed успешно отправлен в канал {channel_id}.")
                        except Exception as e:
                            self.bot.logger.error(f"[ERROR] Ошибка сборки/отправки Embed: {e}")
                    
                    await pubsub.ping()
                    
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                self.bot.logger.error(f"[ERROR] Потеряно соединение с Redis (V1 Listener): {e}. Переподключение через 5 секунд...")
                await asyncio.sleep(5)
            except Exception as e:
                self.bot.logger.error(f"[ERROR] Сбой PubSub Listener: {e}. Переподключение через 5 секунд...")
                await asyncio.sleep(5)

    async def pubsub_v2_listener(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                pubsub = self.bot.redis.pubsub()
                await pubsub.subscribe("projectw_embed_v2_commands")
                self.bot.logger.info("[SYSTEM] Бот начал прослушивание канала V2 Embed команд.")

                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60.0)
                    
                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            channel_id = int(data.get('channel_id'))
                            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

                            components = build_v2_components(data)
                            await channel.send(
                                components=components,
                                flags=disnake.MessageFlags(is_components_v2=True)
                            )
                            self.bot.logger.info(f"[ACTION] Настоящий V2 Embed успешно отправлен в {channel_id}.")
                        except Exception as e:
                            self.bot.logger.error(f"[ERROR] Ошибка сборки V2 Embed: {e}")

                    await pubsub.ping()

            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                self.bot.logger.error(f"[ERROR] Потеряно соединение с Redis (V2 Listener): {e}. Переподключение через 5 секунд...")
                await asyncio.sleep(5)

            except Exception as e:
                self.bot.logger.error(f"[ERROR] Сбой PubSub V2 Listener: {e}. Переподключение через 5 секунд...")
                await asyncio.sleep(5)

def setup(bot):
    bot.add_cog(PubSubListenerCog(bot))