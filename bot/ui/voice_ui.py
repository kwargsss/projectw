import disnake


class RenameModal(disnake.ui.Modal):
    def __init__(self, voice_channel: disnake.VoiceChannel):
        self.voice_channel = voice_channel
        components = [
            disnake.ui.TextInput(
                label="Новое название канала", placeholder="Например: Игровая...",
                custom_id="new_name", style=disnake.TextInputStyle.short, max_length=50, required=True
            )
        ]
        super().__init__(title="Смена названия", components=components, custom_id=f"rename_modal_{voice_channel.id}")

    async def callback(self, inter: disnake.ModalInteraction):
        new_name = inter.text_values["new_name"]
        try:
            await self.voice_channel.edit(name=new_name)
            await inter.send(f"✅ Название изменено на **{new_name}**", ephemeral=True)
        except disnake.HTTPException as e:
            if e.code == 50024:
                await inter.send("⏳ Discord разрешает менять название 2 раза в 10 минут. Подождите немного!", ephemeral=True)
            else:
                await inter.send("❌ Ошибка переименования.", ephemeral=True)

class LimitModal(disnake.ui.Modal):
    def __init__(self, voice_channel: disnake.VoiceChannel):
        self.voice_channel = voice_channel
        components = [
            disnake.ui.TextInput(
                label="Лимит (0 - 99, 0 = безлимит)", placeholder="Например: 5",
                custom_id="new_limit", style=disnake.TextInputStyle.short, max_length=2, required=True
            )
        ]
        super().__init__(title="Установка лимита", components=components, custom_id=f"limit_modal_{voice_channel.id}")

    async def callback(self, inter: disnake.ModalInteraction):
        limit_str = inter.text_values["new_limit"]
        if not limit_str.isdigit(): return await inter.send("❌ Введите только число!", ephemeral=True)
        limit = int(limit_str)
        if limit < 0 or limit > 99: return await inter.send("❌ Лимит от 0 до 99.", ephemeral=True)
        
        await self.voice_channel.edit(user_limit=limit)
        await inter.send(f"✅ Лимит установлен на **{'Безлимит' if limit == 0 else limit}**", ephemeral=True)

class PrivateVoiceControlView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def get_owner_channel(self, inter: disnake.MessageInteraction):
        channel_id = await inter.bot.redis.get(f"pv_user:{inter.author.id}")
        if not channel_id:
            await inter.send("❌ У вас нет активного приватного канала!", ephemeral=True)
            return None
            
        channel = inter.guild.get_channel(int(channel_id))
        if not channel:
            await inter.bot.redis.delete(f"pv_user:{inter.author.id}")
            await inter.send("❌ Ваш канал не найден (возможно он был удален).", ephemeral=True)
            return None
        return channel

    @disnake.ui.button(label="Название", emoji="✏️", style=disnake.ButtonStyle.secondary, custom_id="pv_btn_rename", row=0)
    async def btn_rename(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if channel: await inter.response.send_modal(RenameModal(channel))

    @disnake.ui.button(label="Лимит", emoji="👥", style=disnake.ButtonStyle.secondary, custom_id="pv_btn_limit", row=0)
    async def btn_limit(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if channel: await inter.response.send_modal(LimitModal(channel))

    @disnake.ui.button(label="Закрыть / Открыть", emoji="🔒", style=disnake.ButtonStyle.secondary, custom_id="pv_btn_lock", row=0)
    async def btn_lock(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        perms = channel.overwrites_for(inter.guild.default_role)
        is_locked = perms.connect is False
        perms.connect = None if is_locked else False
        await channel.set_permissions(inter.guild.default_role, overwrite=perms)
        await inter.send(f"✅ Канал **{'ОТКРЫТ' if is_locked else 'ЗАКРЫТ'}** для всех.", ephemeral=True)

    @disnake.ui.button(label="Скрыть / Показать", emoji="👁️", style=disnake.ButtonStyle.secondary, custom_id="pv_btn_hide", row=0)
    async def btn_hide(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        perms = channel.overwrites_for(inter.guild.default_role)
        is_hidden = perms.view_channel is False
        perms.view_channel = None if is_hidden else False
        await channel.set_permissions(inter.guild.default_role, overwrite=perms)
        await inter.send(f"✅ Канал **{'ПОКАЗАН' if is_hidden else 'СКРЫТ'}** в списке серверов.", ephemeral=True)

    @disnake.ui.button(label="Инфо", emoji="ℹ️", style=disnake.ButtonStyle.primary, custom_id="pv_btn_info", row=0)
    async def btn_info(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        embed = disnake.Embed(title="ℹ️ Информация о канале", color=0x8B5CF6)
        embed.add_field(name="Название", value=channel.name, inline=True)
        embed.add_field(name="Участников", value=f"{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}", inline=True)
        await inter.send(embed=embed, ephemeral=True)

    @disnake.ui.user_select(placeholder="➕/➖ Впустить/Выгнать (Доступ)", custom_id="pv_sel_access", row=1)
    async def sel_access(self, select: disnake.ui.UserSelect, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        user = select.values[0]
        if user == inter.author: return await inter.send("❌ Нельзя изменить права себе!", ephemeral=True)
        perms = channel.overwrites_for(user)
        has_access = perms.connect is True
        perms.connect = None if has_access else True
        perms.view_channel = None if has_access else True
        await channel.set_permissions(user, overwrite=perms)
        await inter.send(f"✅ Доступ для {user.mention} **{'ЗАБРАН' if has_access else 'ВЫДАН'}**.", ephemeral=True)

    @disnake.ui.user_select(placeholder="🎙️ Право говорить (Mute/Unmute)", custom_id="pv_sel_speak", row=2)
    async def sel_speak(self, select: disnake.ui.UserSelect, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        user = select.values[0]
        perms = channel.overwrites_for(user)
        can_speak = perms.speak is not False
        perms.speak = False if can_speak else None
        await channel.set_permissions(user, overwrite=perms)
        await inter.send(f"✅ Голос для {user.mention} **{'ОТКЛЮЧЕН' if can_speak else 'ВКЛЮЧЕН'}**.", ephemeral=True)

    @disnake.ui.user_select(placeholder="👢 Выгнать участника (Kick)", custom_id="pv_sel_kick", row=3)
    async def sel_kick(self, select: disnake.ui.UserSelect, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        user = select.values[0]
        if user not in channel.members: return await inter.send("❌ Его нет в вашем канале!", ephemeral=True)
        if user == inter.author: return await inter.send("❌ Нельзя выгнать себя!", ephemeral=True)
        await user.move_to(None)
        await inter.send(f"👢 {user.mention} выгнан из канала.", ephemeral=True)

    @disnake.ui.user_select(placeholder="👑 Передать права владельца", custom_id="pv_sel_transfer", row=4)
    async def sel_transfer(self, select: disnake.ui.UserSelect, inter: disnake.MessageInteraction):
        channel = await self.get_owner_channel(inter)
        if not channel: return
        user = select.values[0]
        if user not in channel.members: return await inter.send("❌ Пользователь должен быть в канале!", ephemeral=True)
        if user.bot: return await inter.send("❌ Нельзя передать права боту!", ephemeral=True)
        
        await inter.bot.redis.delete(f"pv_user:{inter.author.id}")
        await inter.bot.redis.set(f"pv_user:{user.id}", channel.id)
        await inter.bot.redis.set(f"pv_owner:{channel.id}", user.id)
                
        await channel.set_permissions(inter.author, connect=None, view_channel=None, manage_channels=None)
        await channel.set_permissions(user, connect=True, view_channel=True, manage_channels=False)
        await inter.send(f"👑 Права переданы {user.mention}!", ephemeral=True)