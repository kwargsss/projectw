import disnake
import json


class MusicPlayerView(disnake.ui.View):
    def __init__(self, bot, guild_id: int, voice_channel_id: int, worker_id: str, loop_mode: int, autopilot: bool, is_paused: bool):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.voice_channel_id = voice_channel_id
        self.worker_id = worker_id

        self.loop.style = disnake.ButtonStyle.success if loop_mode > 0 else disnake.ButtonStyle.secondary
        self.autopilot_btn.style = disnake.ButtonStyle.success if autopilot else disnake.ButtonStyle.secondary

        self.pause_resume.emoji = "▶️" if is_paused else "⏸️"
        self.pause_resume.style = disnake.ButtonStyle.success if is_paused else disnake.ButtonStyle.primary

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if not inter.author.voice or inter.author.voice.channel.id != self.voice_channel_id:
            await inter.response.send_message("❌ Управляйте музыкой из того голосового канала, где сидит бот!", ephemeral=True)
            return False
        return True

    async def send_cmd(self, action: str):
        payload = {"action": action, "guild_id": self.guild_id}
        await self.bot.redis.publish(f"worker_cmd:{self.worker_id}", json.dumps(payload))

    @disnake.ui.button(emoji="⏮️", style=disnake.ButtonStyle.secondary, row=0)
    async def previous(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("previous")

    @disnake.ui.button(emoji="⏯️", style=disnake.ButtonStyle.primary, row=0)
    async def pause_resume(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("pause_resume")

    @disnake.ui.button(emoji="⏭️", style=disnake.ButtonStyle.secondary, row=0)
    async def skip(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("skip")

    @disnake.ui.button(emoji="⏹️", style=disnake.ButtonStyle.danger, row=0)
    async def stop(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("stop")

    @disnake.ui.button(emoji="🔀", style=disnake.ButtonStyle.secondary, row=1)
    async def shuffle(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("shuffle")
        await inter.followup.send("🔀 Очередь перемешана!", ephemeral=True)

    @disnake.ui.button(emoji="🔁", custom_id="loop", style=disnake.ButtonStyle.secondary, row=1)
    async def loop(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("toggle_loop")
            
    @disnake.ui.button(emoji="🛸", custom_id="autopilot_btn", style=disnake.ButtonStyle.secondary, row=1)
    async def autopilot_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.send_cmd("toggle_autopilot")