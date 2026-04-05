import disnake

from utils.leveling import (
    REDIS_KEY_XP, REDIS_KEY_MESSAGES, REDIS_KEY_VOICE,
    get_level_from_xp, format_voice_time
)


class LeaderboardView(disnake.ui.View):
    def __init__(self, bot, author: disnake.Member):
        super().__init__(timeout=180.0)
        self.bot = bot
        self.author = author
        self.category = "xp"
        self.page = 0
        self.max_pages = 10
        self.v2_components = []
        self.config = {
            "xp": (REDIS_KEY_XP, "⭐ Топ по уровню"),
            "msg": (REDIS_KEY_MESSAGES, "💬 Топ по сообщениям"),
            "voice": (REDIS_KEY_VOICE, "🎙️ Топ по голосу")
        }
        self.update_buttons()

    def to_components(self):
        return [c.to_component_dict() for c in self.v2_components]

    def update_buttons(self):
        self.btn_xp.style = disnake.ButtonStyle.primary if self.category == "xp" else disnake.ButtonStyle.secondary
        self.btn_msg.style = disnake.ButtonStyle.primary if self.category == "msg" else disnake.ButtonStyle.secondary
        self.btn_voice.style = disnake.ButtonStyle.primary if self.category == "voice" else disnake.ButtonStyle.secondary
        
        self.btn_prev.disabled = self.page == 0
        self.btn_next.disabled = self.page >= self.max_pages - 1

    async def generate_components(self):
        rk, title = self.config[self.category]
        
        top_100 = await self.bot.redis.zrevrange(rk, 0, 99, withscores=True)
        total_users = len(top_100)
        self.max_pages = max(1, (total_users + 9) // 10)
        if self.page >= self.max_pages:
            self.page = max(0, self.max_pages - 1)

        start_idx = self.page * 10
        end_idx = start_idx + 10
        page_data = top_100[start_idx:end_idx]

        description = ""
        user_id_str = str(self.author.id)
        
        if not page_data:
            description = "Список пуст."
        else:
            for i, (uid_raw, _) in enumerate(page_data):
                uid = uid_raw.decode() if isinstance(uid_raw, bytes) else str(uid_raw)
                actual_rank = start_idx + i + 1
                
                user_xp_raw = await self.bot.redis.zscore(REDIS_KEY_XP, uid)
                user_xp = float(user_xp_raw) if user_xp_raw else 0.0
                level = get_level_from_xp(user_xp)

                user_stats = await self.bot.redis.hgetall(f"user_stats:{uid}")
                
                def get_stat(key_str):
                    val = user_stats.get(key_str.encode()) or user_stats.get(key_str)
                    try:
                        return int(val.decode() if isinstance(val, bytes) else val)
                    except:
                        return 0

                msg_count = get_stat("messages")
                v_mins = get_stat("voice_mins")
                voice_str = format_voice_time(v_mins)
                
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(actual_rank, "🔹")
                you_badge = " **(Вы)**" if uid == user_id_str else ""
                
                description += f"{medal} **#{actual_rank}.** <@{uid}>{you_badge}\nУровень: **{level}** | Опыт: **{int(user_xp)}** | Сообщения: **{msg_count}** | Голос: **{voice_str}**\n\n"

            in_page = any((uid.decode() if isinstance(uid, bytes) else str(uid)) == user_id_str for uid, _ in page_data)
            
            if not in_page:
                user_rank_raw = await self.bot.redis.zrevrank(rk, user_id_str)
                if user_rank_raw is not None:
                    actual_rank = user_rank_raw + 1
                    
                    user_xp_raw = await self.bot.redis.zscore(REDIS_KEY_XP, user_id_str)
                    user_xp = float(user_xp_raw) if user_xp_raw else 0.0
                    level = get_level_from_xp(user_xp)

                    user_stats = await self.bot.redis.hgetall(f"user_stats:{user_id_str}")
                    
                    def get_stat_self(key_str):
                        val = user_stats.get(key_str.encode()) or user_stats.get(key_str)
                        try:
                            return int(val.decode() if isinstance(val, bytes) else val)
                        except:
                            return 0

                    msg_count = get_stat_self("messages")
                    v_mins = get_stat_self("voice_mins")
                    voice_str = format_voice_time(v_mins)
                    
                    description += f"...\n\n🔹 **#{actual_rank}.** <@{user_id_str}> **(Вы)**\nУровень: **{level}** | Опыт: **{int(user_xp)}** | Сообщения: **{msg_count}** | Голос: **{voice_str}**\n\n"

        footer_text = f"Страница {self.page + 1}/{self.max_pages} • Запросил {self.author.display_name}"

        components = [
            disnake.ui.Container(
                disnake.ui.ActionRow(self.btn_xp, self.btn_msg, self.btn_voice),
                disnake.ui.TextDisplay(f"## {title}\n{description}\n*{footer_text}*"),
                disnake.ui.ActionRow(self.btn_prev, self.btn_next),
                accent_colour=disnake.Colour.gold()
            )
        ]
        
        self.v2_components = components

    async def update_message(self, inter: disnake.MessageInteraction):
        self.update_buttons()
        await self.generate_components()
        
        await inter.response.edit_message(
            embed=None,
            view=self, 
            flags=disnake.MessageFlags(is_components_v2=True)
        )

    async def check_author(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.author.id:
            await inter.send("Вы не можете переключать страницы в чужом топе!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Опыт", emoji="⭐", style=disnake.ButtonStyle.primary, row=0)
    async def btn_xp(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not await self.check_author(inter): return
        self.category = "xp"
        self.page = 0
        await self.update_message(inter)

    @disnake.ui.button(label="Сообщения", emoji="💬", style=disnake.ButtonStyle.secondary, row=0)
    async def btn_msg(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not await self.check_author(inter): return
        self.category = "msg"
        self.page = 0
        await self.update_message(inter)

    @disnake.ui.button(label="Голос", emoji="🎙️", style=disnake.ButtonStyle.secondary, row=0)
    async def btn_voice(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not await self.check_author(inter): return
        self.category = "voice"
        self.page = 0
        await self.update_message(inter)

    @disnake.ui.button(label="Назад", emoji="◀️", style=disnake.ButtonStyle.secondary, row=1)
    async def btn_prev(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not await self.check_author(inter): return
        self.page -= 1
        await self.update_message(inter)

    @disnake.ui.button(label="Вперед", emoji="▶️", style=disnake.ButtonStyle.secondary, row=1)
    async def btn_next(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not await self.check_author(inter): return
        self.page += 1
        await self.update_message(inter)