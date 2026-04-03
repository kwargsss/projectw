import disnake
import random


class MusicPlayerView(disnake.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    @disnake.ui.button(emoji="⏮️", style=disnake.ButtonStyle.secondary, row=0)
    async def previous(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        track = await self.player.play_previous()
        if track:
            await self.player.update_player_ui(track)
        else:
            await inter.followup.send("История пуста!", ephemeral=True)

    @disnake.ui.button(emoji="⏯️", style=disnake.ButtonStyle.primary, row=0)
    async def pause_resume(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.player.paused:
            await self.player.resume()
            await inter.response.send_message("▶️ Возобновлено", ephemeral=True)
        else:
            await self.player.pause()
            await inter.response.send_message("⏸️ Пауза", ephemeral=True)

    @disnake.ui.button(emoji="⏭️", style=disnake.ButtonStyle.secondary, row=0)
    async def skip(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.player.stop() 
        await inter.followup.send("⏭️ Пропущено", ephemeral=True)

    @disnake.ui.button(emoji="⏹️", style=disnake.ButtonStyle.danger, row=0)
    async def stop(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.player.teardown()

    @disnake.ui.button(emoji="🔀", style=disnake.ButtonStyle.secondary, row=1)
    async def shuffle(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        queue = await self.player.redis.lrange(self.player.queue_key, 0, -1)
        
        if len(queue) < 2:
            return await inter.response.send_message("❌ Слишком мало треков в очереди для перемешивания!", ephemeral=True)
        
        random.shuffle(queue)
        
        async with self.player.redis.pipeline(transaction=True) as pipe:
            await pipe.delete(self.player.queue_key)
            await pipe.rpush(self.player.queue_key, *queue)
            await pipe.execute()
            
        await inter.response.send_message("🔀 Очередь успешно перемешана!", ephemeral=True)

    @disnake.ui.button(emoji="🔁", style=disnake.ButtonStyle.secondary, row=1)
    async def loop(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.player.loop_mode = (self.player.loop_mode + 1) % 3
        await self.player.update_player_ui(self.player.current)
        await inter.response.send_message(f"Режим повтора изменен", ephemeral=True)
            
    @disnake.ui.button(emoji="🛸", style=disnake.ButtonStyle.secondary, row=1)
    async def autopilot_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.player.autopilot = not self.player.autopilot
        
        button.style = disnake.ButtonStyle.success if self.player.autopilot else disnake.ButtonStyle.secondary
        
        status = "включена" if self.player.autopilot else "выключена"
        
        await self.player.update_player_ui(self.player.current)
        await inter.response.send_message(f"🛸 Моя волна {status}. Бот будет подбирать похожие треки, когда очередь закончится!", ephemeral=True)