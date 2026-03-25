import os
import disnake
import json
import asyncio
import redis.asyncio as redis

from datetime import datetime
from disnake.ext import commands, tasks
from dotenv import load_dotenv
from tg_logger import setup_logger

load_dotenv()

logger = setup_logger("bot", os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID"))

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    health_check_interval=30
)

intents = disnake.Intents.default()
intents.members = True          
intents.presences = True        
intents.message_content = True  

bot = commands.InteractionBot(intents=intents)

async def pubsub_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("projectw_embed_commands")
    logger.info("[SYSTEM] Бот начал прослушивание канала Embed команд.")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    channel_id = int(data.get('channel_id'))
                    channel = bot.get_channel(channel_id)

                    if not channel:
                        try:
                            channel = await bot.fetch_channel(channel_id)
                        except:
                            logger.error(f"[ERROR] Канал {channel_id} не найден или нет доступа.")
                            continue

                    embed = disnake.Embed()
                    
                    if data.get('title'): embed.title = data['title']
                    if data.get('description'): embed.description = data['description']
                    if data.get('url'): embed.url = data['url']

                    color_hex = data.get('color', '#5865F2').replace('#', '')
                    if color_hex: embed.color = int(color_hex, 16)
                    
                    if data.get('author_name'):
                        embed.set_author(
                            name=data['author_name'],
                            icon_url=data.get('author_icon') if data.get('author_icon') else None,
                            url=data.get('author_url') if data.get('author_url') else None
                        )
                    
                    if data.get('image_url'): embed.set_image(url=data['image_url'])
                    if data.get('thumbnail_url'): embed.set_thumbnail(url=data['thumbnail_url'])

                    if data.get('footer'):
                        embed.set_footer(text=data['footer']['text'], icon_url=data['footer'].get('icon_url'))
                        embed.timestamp = datetime.utcnow()
                    
                    for field in data.get('fields', []):
                        if field.get('name') and field.get('value'):
                            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
                    
                    content = data.get('content') if data.get('content') else None
                    
                    await channel.send(content=content, embed=embed)
                    logger.info(f"[ACTION] Embed успешно отправлен в канал {channel_id}.")
                except Exception as e:
                    logger.error(f"[ERROR] Ошибка сборки/отправки Embed: {e}")
    except Exception as e:
        logger.error(f"[ERROR] Сбой PubSub Listener: {e}")

async def pubsub_v2_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("projectw_embed_v2_commands")
    logger.info("[SYSTEM] Бот начал прослушивание канала V2 Embed команд.")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    channel_id = int(data.get('channel_id'))
                    channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                    
                    components_list = []

                    for block in data.get('blocks', []):
                        b_type = block.get('type')
                        
                        if b_type == 'text_display':
                            if block.get('content'):
                                components_list.append(disnake.ui.TextDisplay(block['content']))
                                
                        elif b_type == 'media_gallery':
                            if block.get('url'):
                                media_obj = disnake.UnfurledMediaItem(url=block['url'])
                                
                                components_list.append(
                                    disnake.ui.MediaGallery(
                                        disnake.MediaGalleryItem(
                                            media=media_obj, 
                                            description=block.get('description', '')
                                        )
                                    )
                                )
                                
                        elif b_type == 'separator':
                            components_list.append(disnake.ui.Separator(divider=True))
                            
                        elif b_type == 'section':
                            accessory = None
                            if block.get('button_label') and block.get('button_url'):
                                accessory = disnake.ui.Button(
                                    style=disnake.ButtonStyle.link,
                                    label=block['button_label'],
                                    url=block['button_url']
                                )
                            if block.get('content'):
                                components_list.append(disnake.ui.Section(
                                    disnake.ui.TextDisplay(block['content']),
                                    accessory=accessory
                                ))
                                
                        elif b_type == 'file':
                            if block.get('url'):
                                components_list.append(disnake.ui.File(file={"url": block['url']}, spoiler=False))

                    if data.get('footer'):
                        components_list.append(disnake.ui.Separator(divider=True))
                        now_ts = int(datetime.now().timestamp())
                        footer_text = f"{data['footer']['text']} • <t:{now_ts}:f>"
                        components_list.append(disnake.ui.TextDisplay(footer_text))

                    color_hex = data.get('color', '#5865F2').lstrip('#')
                    container = disnake.ui.Container(
                        *components_list,
                        accent_colour=disnake.Colour(int(color_hex, 16)),
                        spoiler=False
                    )

                    await channel.send(
                        components=[container],
                        flags=disnake.MessageFlags(is_components_v2=True)
                    )
                    logger.info(f"[ACTION] V2 Embed успешно отправлен в {channel_id}.")
                except Exception as e:
                    logger.error(f"[ERROR] Ошибка сборки V2 Embed: {e}")
    except Exception as e:
        logger.error(f"[ERROR] Сбой PubSub V2 Listener: {e}")

@bot.event
async def on_message(message: disnake.Message):
    if not message.author.bot: await redis_client.incr("stats_messages_24h")

@bot.event
async def on_application_command(inter: disnake.ApplicationCommandInteraction):
    await redis_client.incr("stats_commands_24h")

@tasks.loop(seconds=5)
async def update_stats_cache():
    if not bot.guilds: return
    guild = bot.guilds[0]
    
    msg_count = await redis_client.get("stats_messages_24h")
    cmd_count = await redis_client.get("stats_commands_24h")
    online_count = sum(1 for m in guild.members if m.status != disnake.Status.offline)

    text_channels = [{"id": str(c.id), "name": c.name} for c in guild.text_channels]
    await redis_client.set("guild_channels", json.dumps(text_channels), ex=30)

    today_str = datetime.now().strftime("%d.%m")
    history_str = await redis_client.get("weekly_history")
    history = json.loads(history_str) if history_str else []

    if not history or history[-1]["date"] != today_str:
        await redis_client.set("stats_messages_24h", 0)
        await redis_client.set("stats_commands_24h", 0)
        msg_count = cmd_count = 0
        logger.info(f"[STATS] Наступил новый день ({today_str})! Суточная статистика сброшена.")
        if len(history) >= 7: history.pop(0)
        history.append({"date": today_str, "messages": 0, "commands": 0})

    history[-1]["messages"] = int(msg_count) if msg_count else 0
    history[-1]["commands"] = int(cmd_count) if cmd_count else 0
    await redis_client.set("weekly_history", json.dumps(history))

    stats = { "name": guild.name, "member_count": guild.member_count, "online": online_count, "messages_24h": int(msg_count) if msg_count else 0, "commands_24h": int(cmd_count) if cmd_count else 0 }
    await redis_client.set("guild_stats", json.dumps(stats), ex=30)

@bot.event
async def on_ready():
    logger.info(f"[SYSTEM] Бот успешно запущен как {bot.user}")
    bot.loop.create_task(pubsub_listener())
    bot.loop.create_task(pubsub_v2_listener())
    update_stats_cache.start()

@bot.slash_command(description="Тестовая команда для проверки графика")
async def test_graph(inter: disnake.ApplicationCommandInteraction):
    logger.info(f"[ACTION] Пользователь {inter.author.name} использовал команду /test_graph")
    await inter.response.send_message("Команда успешно засчитана в реальный график! 🚀", ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))