import os
import disnake
import json
import asyncio
import redis.asyncio as redis
import io

from datetime import datetime
from disnake.ext import commands, tasks
from dotenv import load_dotenv
from tg_logger import setup_logger

load_dotenv()

logger = setup_logger("bot", os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID"))

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    health_check_interval=30,
    socket_connect_timeout=2
)

bot = commands.Bot(
    command_prefix="!", 
    intents=disnake.Intents.all(),
    help_command=None
)

bot.redis = redis_client
bot.logger = logger

async def pubsub_listener():
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("projectw_embed_commands")
            logger.info("[SYSTEM] Бот начал прослушивание канала Embed команд.")

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
            logger.error(f"[ERROR] Сбой PubSub Listener: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)

async def pubsub_v2_listener():
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("projectw_embed_v2_commands")
            logger.info("[SYSTEM] Бот начал прослушивание канала V2 Embed команд.")

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
                        logger.info(f"[ACTION] Настоящий V2 Embed успешно отправлен в {channel_id}.")
                    except Exception as e:
                        logger.error(f"[ERROR] Ошибка сборки V2 Embed: {e}")

        except Exception as e:
            logger.error(f"[ERROR] Сбой PubSub V2 Listener: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)

async def ticket_action_listener():
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("site_ticket_actions", "site_ticket_messages")
            logger.info("[SYSTEM] Бот начал прослушивание команд тикетов с сайта.")

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    channel_id = int(data['ticket_id'])
                    channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                    
                    if not channel: continue

                    if message['channel'] == 'site_ticket_messages':
                        embed = disnake.Embed(description=data['content'], color=0x8B5CF6)
                        embed.set_author(name=f"Агент: {data['admin_name']}", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                        embed.set_footer(text="Отправлено с панели управления")
                        embed.timestamp = datetime.now()
                        await channel.send(embed=embed)

                    elif message['channel'] == 'site_ticket_actions':
                        action = data['action']
                        admin_name = data['admin_name']

                        if action == 'close':
                            creator_id = None
                            if channel.topic and "от " in channel.topic:
                                try: creator_id = int(channel.topic.split("от ")[1])
                                except: pass
                            
                            if creator_id:
                                member = channel.guild.get_member(creator_id)
                                if member: await channel.set_permissions(member, overwrite=None)
                            
                            embed = disnake.Embed(
                                title="🔒 Тикет закрыт",
                                description=f"Работа по данному обращению приостановлена агентом **{admin_name}** (с сайта).\nПользователь больше не может писать в этот канал.",
                                color=0xEF4444
                            )
                            await channel.send(embed=embed)
                            await redis_client.publish("discord_ticket_updates", json.dumps({"ticket_id": str(channel.id), "event": "closed"}))

                        elif action == 'delete':
                            await channel.send(embed=disnake.Embed(title="⏳ Удаление...", description=f"Запрошено агентом **{admin_name}** с сайта. Генерация архива...", color=0xF59E0B))
                            import chat_exporter
                            try:
                                transcript = await chat_exporter.export(channel)
                                if transcript:
                                    archive_channel = channel.guild.get_channel(int(os.getenv("ARCHIVE_CHANNEL_ID")))
                                    if archive_channel:
                                        transcript_file = disnake.File(io.BytesIO(transcript.encode()), filename=f"archive-{channel.name}.html")
                                        embed = disnake.Embed(title="🗃️ Новый архив тикета", description=f"**Канал:** `{channel.name}`\n**Удалил:** {admin_name} (Сайт)", color=0x8B5CF6)
                                        await archive_channel.send(embed=embed, file=transcript_file)
                            except Exception as e:
                                logger.error(f"[ERROR] chat_exporter: {e}")
                            
                            await channel.delete()
                            await redis_client.publish("discord_ticket_updates", json.dumps({"ticket_id": str(channel.id), "event": "deleted"}))
                            
        except Exception as e:
            logger.error(f"[ERROR] Сбой Ticket Listener: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)

async def send_notification(member: disnake.Member, event_type: str):
    settings_str = await redis_client.get("notification_settings")
    if not settings_str: 
        return
    
    try:
        settings = json.loads(settings_str)
        config = settings.get(event_type)
        event_name = "Приветствие" if event_type == "welcome" else "Прощание"
        
        if not config or not config.get("enabled"): 
            return

        chan_id = str(config.get("channel_id", ""))
        if not chan_id or not chan_id.isdigit(): 
            logger.warning(f"[ВНИМАНИЕ] {event_name} включено, но канал не выбран! Отмена.")
            return

        channel_id = int(chan_id)
        channel = member.guild.get_channel(channel_id) or await member.guild.fetch_channel(channel_id)
        if not channel: 
            logger.warning(f"[ВНИМАНИЕ] Канал {channel_id} для {event_name} не найден!")
            return

        def fmt(text):
            if not text: return ""
            return text.replace("{user}", member.mention)\
                       .replace("{user.name}", member.name)\
                       .replace("{server}", member.guild.name)\
                       .replace("{count}", str(member.guild.member_count))

        content = fmt(config.get("content"))
        color_hex = config.get("color", "#5865F2").replace("#", "")
        color_int = int(color_hex, 16) if color_hex else 0x5865F2

        if config.get("embed_type") == "v2":
            comps = []

            if content:
                comps.append(disnake.ui.TextDisplay(content))
                if config.get('blocks'):
                    comps.append(disnake.ui.Separator(divider=True))
            
            for block in config.get('blocks', []):
                b_type = block.get('type')
                if b_type == 'text_display' and block.get('content'): 
                    comps.append(disnake.ui.TextDisplay(fmt(block['content'])))
                elif b_type == 'media_gallery' and block.get('url'):
                    comps.append(disnake.ui.MediaGallery(disnake.MediaGalleryItem(media=disnake.UnfurledMediaItem(url=fmt(block['url'])), description=fmt(block.get('description', '')))))
                elif b_type == 'separator':
                    comps.append(disnake.ui.Separator(divider=True))
                elif b_type == 'section':
                    accessory = None
                    if block.get('button_label') and block.get('button_url'):
                        accessory = disnake.ui.Button(style=disnake.ButtonStyle.link, label=fmt(block['button_label']), url=fmt(block['button_url']))
                    if block.get('content'):
                        comps.append(disnake.ui.Section(disnake.ui.TextDisplay(fmt(block['content'])), accessory=accessory))
                elif b_type == 'file' and block.get('url'): 
                    comps.append(disnake.ui.File(file={"url": fmt(block['url'])}, spoiler=False))

            now_ts = int(datetime.now().timestamp())
            comps.append(disnake.ui.Separator(divider=True))
            comps.append(disnake.ui.TextDisplay(f"Система оповещений • <t:{now_ts}:f>"))

            container = disnake.ui.Container(*comps, accent_colour=disnake.Colour(color_int), spoiler=False)

            await channel.send(components=[container], flags=disnake.MessageFlags(is_components_v2=True))
            logger.info(f"[ACTION] {event_name} (V2) успешно отправлено для {member.name} в канал #{channel.name}.")

        else:
            embed = disnake.Embed(color=color_int)
            title = fmt(config.get("title"))
            description = fmt(config.get("description"))
            if title: embed.title = title
            if description: embed.description = description
            if config.get("image_url"): embed.set_image(url=config["image_url"])
            if config.get("thumbnail_url"): embed.set_thumbnail(url=config["thumbnail_url"])

            await channel.send(content=content if content else None, embed=embed)
            logger.info(f"[ACTION] {event_name} (V1) успешно отправлено для {member.name} в канал #{channel.name}.")
            
    except Exception as e:
        logger.error(f"[ERROR] Ошибка сборки/отправки оповещения {event_type} для {member.name}: {e}")

@bot.event
async def on_message(message: disnake.Message):
    if not message.author.bot: 
        try:
            await asyncio.wait_for(redis_client.incr("stats_messages_24h"), timeout=1.0)
        except: pass

    if message.channel.name.startswith("ticket-"):
        msg_data = {
            "ticket_id": str(message.channel.id),
            "id": str(message.id),
            "content": message.content,
            "author": message.author.display_name,
            "author_avatar": message.author.display_avatar.url if message.author.display_avatar else None,
            "timestamp": message.created_at.timestamp(),
            "is_bot": message.author.bot,
            "embeds": [e.to_dict() for e in message.embeds],
            "attachments": [a.url for a in message.attachments]
        }
        await redis_client.publish("discord_ticket_messages", json.dumps(msg_data))

    await bot.process_commands(message)

@bot.listen("on_application_command")
async def stats_command_tracker(inter: disnake.ApplicationCommandInteraction):
    try:
        await asyncio.wait_for(redis_client.incr("stats_commands_24h"), timeout=1.0)
    except Exception:
        pass

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
    
    try:
        await redis_client.ping()
        logger.info("[SYSTEM] Успешное подключение к Redis! 🟢")
    except Exception as e:
        logger.error(f"[ERROR] REDIS НЕ ОТВЕЧАЕТ: {e} 🔴")

    bot.loop.create_task(pubsub_listener())
    bot.loop.create_task(pubsub_v2_listener())
    bot.loop.create_task(ticket_action_listener())
    update_stats_cache.start()

@bot.event
async def on_member_join(member: disnake.Member):
    await send_notification(member, "welcome")

@bot.event
async def on_member_remove(member: disnake.Member):
    await send_notification(member, "goodbye")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    cogs_dir = os.path.join(base_dir, "cogs")
    
    if os.path.exists(cogs_dir):
        for root, dirs, files in os.walk(cogs_dir):
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("__"):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, base_dir)
                    cog_path = rel_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        bot.load_extension(cog_path)
                    except Exception as e:
                        logger.error(f"[ERROR] Ошибка при загрузке модуля {cog_path}: {e}")
    else:
        logger.warning("[SYSTEM] Папка 'cogs' не найдена. Модули не загружены.")

    bot.run(os.getenv("BOT_TOKEN"))