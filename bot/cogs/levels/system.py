import disnake
import time
import io
import os

from ui.leveling_ui import LeaderboardView
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
        max_name_width = 520 
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

        start_x = 230
        y_base = 170
        text_color = (88, 101, 242, 255)

        draw.text((start_x, y_base), "Ранг #", font=font_med, fill=text_color, anchor="ls")
        start_x += int(draw.textlength("Ранг #", font=font_med)) + 4
        
        draw.text((start_x, y_base), str(rank_display), font=font_large, fill=text_color, anchor="ls")
        start_x += int(draw.textlength(str(rank_display), font=font_large)) + 30
        
        draw.text((start_x, y_base), "Уровень ", font=font_med, fill=text_color, anchor="ls")
        start_x += int(draw.textlength("Уровень ", font=font_med)) + 4
        
        draw.text((start_x, y_base), str(level), font=font_large, fill=text_color, anchor="ls")

        voice_text = f"Голос: {format_voice_time(v_mins)}"
        draw.text((760, 120), voice_text, font=font_small, fill=(181, 186, 193, 255), anchor="ra")

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
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        
        view = LeaderboardView(self.bot, inter.author)
        await view.generate_components()
        
        await inter.edit_original_response(
            embed=None,
            view=view,
            flags=disnake.MessageFlags(is_components_v2=True)
        )

def setup(bot):
    bot.add_cog(LevelingSystem(bot))