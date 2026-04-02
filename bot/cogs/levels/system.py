import disnake
import time
import io
import os

from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
from utils.leveling import (
    get_message_xp, get_voice_xp, get_level_from_xp, 
    get_xp_for_level, format_voice_time, get_progress_bar_stats,
    MESSAGE_COOLDOWN, REDIS_KEY_XP, REDIS_KEY_MESSAGES, REDIS_KEY_VOICE
)


class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild: return
        user_id = message.author.id
        cd_key = f"xp_cd:{user_id}"

        if await self.bot.redis.get(cd_key): return
        await self.bot.redis.set(cd_key, "1", ex=MESSAGE_COOLDOWN)
        
        await self.bot.redis.hincrby(f"user_stats:{user_id}", "messages", 1)
        await self.bot.redis.zincrby(REDIS_KEY_MESSAGES, 1, str(user_id))
        
        xp_gained = get_message_xp()
        old_xp = await self.bot.redis.zscore(REDIS_KEY_XP, str(user_id))
        old_level = get_level_from_xp(float(old_xp) if old_xp else 0.0)

        new_xp = await self.bot.redis.zincrby(REDIS_KEY_XP, xp_gained, str(user_id))
        new_level = get_level_from_xp(float(new_xp))

        if new_level > old_level:
            embed = disnake.Embed(
                title="✨ Уровень повышен!",
                description=f"{message.author.mention}, ты достиг **{new_level} уровня**!",
                color=disnake.Color.brand_green()
            )
            await message.channel.send(embed=embed, delete_after=10)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot: return
        user_id = member.id
        join_key = f"voice_join:{user_id}"

        if before.channel is None and after.channel is not None:
            await self.bot.redis.set(join_key, int(time.time()))
        elif before.channel is not None and after.channel is None:
            join_time = await self.bot.redis.get(join_key)
            if join_time:
                minutes = (int(time.time()) - int(join_time)) // 60
                await self.bot.redis.delete(join_key)
                if minutes > 0:
                    await self.bot.redis.hincrby(f"user_stats:{user_id}", "voice_mins", minutes)
                    await self.bot.redis.zincrby(REDIS_KEY_VOICE, minutes, str(user_id))
                    await self.bot.redis.zincrby(REDIS_KEY_XP, get_voice_xp(minutes), str(user_id))

    @commands.slash_command(name="ранг", description="Показать вашу карточку активности")
    async def rank(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        target = inter.author
        user_id = target.id
        user_id_str = str(user_id)

        xp_raw = await self.bot.redis.zscore(REDIS_KEY_XP, user_id_str)
        if xp_raw is None:
            return await inter.edit_original_response(content=f"У {target.display_name} еще нет активности.")

        xp = float(xp_raw)
        level = get_level_from_xp(xp)
        rank_idx = await self.bot.redis.zrevrank(REDIS_KEY_XP, user_id_str)
        rank_display = rank_idx + 1 if rank_idx is not None else "?"

        stats = await self.bot.redis.hgetall(f"user_stats:{user_id}")
        def get_stat(key):
            val = stats.get(key) or stats.get(key.encode())
            if val is None: return "0"
            return val.decode() if isinstance(val, bytes) else str(val)

        v_mins = int(get_stat("voice_mins"))
        messages = get_stat("messages")

        percentage, xp_have, xp_needed = get_progress_bar_stats(xp, level)

        bg_color = (30, 31, 34, 255)
        background = Image.new("RGBA", (800, 250), bg_color)

        bg_filename_raw = await self.bot.redis.get(f"user_bg:{user_id_str}")
        if bg_filename_raw:
            bg_filename = bg_filename_raw.decode() if isinstance(bg_filename_raw, bytes) else str(bg_filename_raw)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            bg_path = os.path.join(project_root, "backend", "uploads", "backgrounds", bg_filename)
            
            if os.path.exists(bg_path):
                try:
                    custom_bg = Image.open(bg_path).convert("RGBA")
                    custom_bg = ImageOps.fit(custom_bg, (800, 250), Image.Resampling.LANCZOS)
                    dark_overlay = Image.new("RGBA", (800, 250), (0, 0, 0, 100))
                    background = Image.alpha_composite(custom_bg, dark_overlay)
                except Exception as e:
                    print(f"[LEVELS] Ошибка открытия фона {bg_filename}: {e}")

        draw = ImageDraw.Draw(background)

        try:
            font_large = ImageFont.truetype("arial.ttf", 38)
            font_med = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except OSError:
            font_large = font_med = font_small = ImageFont.load_default()

        avatar_bytes = await target.display_avatar.with_format("png").with_size(256).read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((160, 160), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (160, 160), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 160, 160), fill=255)
        avatar.putalpha(mask)
        background.paste(avatar, (40, 45), avatar)

        name_text = target.display_name
        max_name_width = 390 
        ellipsis = "..."
        
        bbox = draw.textbbox((0, 0), name_text, font=font_large)
        current_width = bbox[2] - bbox[0]
        
        if current_width > max_name_width:
            for i in range(len(name_text), 0, -1):
                truncated_name = name_text[:i] + ellipsis
                t_bbox = draw.textbbox((0, 0), truncated_name, font=font_large)
                if t_bbox[2] - t_bbox[0] <= max_name_width:
                    name_text = truncated_name
                    break
            else:
                name_text = ellipsis 

        draw.text((230, 45), name_text, font=font_large, fill=(255, 255, 255, 255))

        stats_text = f"Сообщений: {messages}   |   В войсе: {format_voice_time(v_mins)}"
        draw.text((230, 105), stats_text, font=font_small, fill=(149, 165, 166, 255))

        draw.text((760, 45), f"Уровень {level}", font=font_med, fill=(88, 101, 242, 255), anchor="ra") 
        draw.text((760, 80), f"Ранг #{rank_display}", font=font_small, fill=(149, 165, 166, 255), anchor="ra")
        xp_text = f"{int(xp_have)} / {xp_needed} XP"
        draw.text((760, 150), xp_text, font=font_small, fill=(181, 186, 193, 255), anchor="ra")

        bar_x, bar_y = 230, 180
        bar_width, bar_height = 530, 25
        radius = 12
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], radius=radius, fill=(43, 45, 49, 255))
        if percentage > 0:
            fill_width = max(radius * 2, int(bar_width * (percentage / 100))) 
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)], radius=radius, fill=(88, 101, 242, 255))

        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        file = disnake.File(fp=buffer, filename="rank_card.png")
        await inter.edit_original_response(file=file)

    @commands.slash_command(name="лидеры", description="Таблицы лидеров сервера")
    async def leaderboard(
        self, 
        inter: disnake.ApplicationCommandInteraction,
        category: str = commands.Param(
            name="категория",
            choices={
                "⭐ По уровню": "xp",
                "💬 По сообщениям": "msg",
                "🎙️ По голосу": "voice"
            }
        )
    ):
        config = {
            "xp": (REDIS_KEY_XP, "⭐ Топ по уровню", "Ур. {val} • {score} XP"),
            "msg": (REDIS_KEY_MESSAGES, "💬 Топ по сообщениям", "{score} сообщ."),
            "voice": (REDIS_KEY_VOICE, "🎙️ Топ по голосу", "{val}")
        }
        
        rk, title, fmt = config[category]
        top = await self.bot.redis.zrevrange(rk, 0, 9, withscores=True)
        
        if not top:
            return await inter.response.send_message("Список пуст.", ephemeral=True)

        user_id_str = str(inter.author.id)
        in_top = any((uid.decode() if isinstance(uid, bytes) else str(uid)) == user_id_str for uid, _ in top)
        
        user_appended = False
        target_rank = None
        
        if not in_top:
            user_score_raw = await self.bot.redis.zscore(rk, user_id_str)
            if user_score_raw is not None:
                user_rank_raw = await self.bot.redis.zrevrank(rk, user_id_str)
                user_score = float(user_score_raw)
                target_rank = user_rank_raw + 1
                user_appended = True
                top.append((user_id_str.encode(), user_score))

        embed = disnake.Embed(title=title, color=disnake.Color.gold())
        if inter.guild.icon: embed.set_thumbnail(url=inter.guild.icon.url)
        
        description = ""
        for i, (uid_raw, score_raw) in enumerate(top):
            uid = uid_raw.decode() if isinstance(uid_raw, bytes) else str(uid_raw)
            score = int(float(score_raw))
            
            is_target = user_appended and i == len(top) - 1
            actual_rank = target_rank if is_target else i + 1
            
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(actual_rank, f"`{actual_rank}.` ")
            
            if category == "xp":
                val = fmt.format(val=get_level_from_xp(score), score=score)
            elif category == "voice":
                val = fmt.format(val=format_voice_time(score))
            else:
                val = fmt.format(score=score)
            
            if is_target:
                description += "...\n\n"
                
            you_badge = " **(Вы)**" if uid == user_id_str else ""
            description += f"{medal} <@{uid}>{you_badge}\n└─ {val}\n\n"

        embed.description = description
        embed.set_footer(text=f"Запросил {inter.author.display_name}", icon_url=inter.author.display_avatar.url)
        
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(LevelingSystem(bot))