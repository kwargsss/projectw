import disnake
import mafic
import json
import warnings
import redis.asyncio as redis
import multiprocessing

from core.tg_logger import setup_logger
from disnake.ext import commands
from config import Config
from core.player import CustomPlayer


warnings.filterwarnings("ignore", message=".*The version of Lavalink you are using is not supported by Mafic.*")

class WorkerBot(commands.Bot):
    def __init__(self, worker_id: str):
        super().__init__(intents=disnake.Intents.all(), command_prefix="w!")
        self.worker_id = worker_id
        self.redis = redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.pool = mafic.NodePool(self)
        self.logger = setup_logger(f"worker_{worker_id}", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)
        
    async def on_ready(self):
        self.logger.info(f"[WORKER {self.worker_id}] Запущен как {self.user}. Подключаю Lavalink...")
        await self.pool.create_node(
            host=Config.LAVALINK_HOST,
            port=Config.LAVALINK_PORT,
            label=f"NODE_{self.worker_id}",
            password=Config.LAVALINK_PASSWORD
        )
        self.loop.create_task(self.listen_to_redis())

    async def on_node_ready(self, node: mafic.Node):
        self.logger.info(f"[WORKER {self.worker_id}] Lavalink подключен! Готов к работе.")
        await self.redis.sadd("all_workers", self.worker_id)

    async def on_track_end(self, event: mafic.TrackEndEvent):
        player: CustomPlayer = event.player
        reason = str(event.reason).upper()
        
        if "FINISHED" in reason or "STOPPED" in reason or "FAILED" in reason:
            if "FINISHED" in reason:
                if player.loop_mode == 1:
                    await self.redis.lpush(player.queue_key, event.track.id)
                elif player.loop_mode == 2:
                    await self.redis.rpush(player.queue_key, event.track.id)

                try:
                    track_name = f"{event.track.author} - {event.track.title}"[:200]
                    
                    await self.redis.zincrby(f"music_top:guild:{player.guild.id}", 1, track_name)
                    
                    if player.channel:
                        for member in player.channel.members:
                            if not member.bot:
                                await self.redis.zincrby(f"music_top:user:{member.id}", 1, track_name)
                except Exception as e:
                    self.logger.error(f"[STATS ERROR] Ошибка записи статистики: {e}")

            next_track = await player.play_next(finished_track=event.track)
            
            if next_track:
                player.cancel_timeout()
                await player.send_ui_update(next_track)
            else:
                if player.autopilot and ("FINISHED" in reason or "STOPPED" in reason):
                    ap_track = await player.play_autopilot(event.track)
                    if ap_track:
                        player.cancel_timeout()
                        await player.send_ui_update(ap_track)
                        return

                await player.send_ui_update(None)
                player.timeout_task = self.loop.create_task(player.start_timeout(300))

    async def listen_to_redis(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"worker_cmd:{self.worker_id}")
        import random
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                action = data.get("action")
                guild_id = data.get("guild_id")
                guild = self.get_guild(guild_id)
                if not guild: continue

                if action == "connect_and_play":
                    voice_channel = guild.get_channel(data["voice_channel_id"])
                    
                    player = guild.voice_client
                    if not player:
                        try:
                            player = await voice_channel.connect(cls=CustomPlayer)
                            await guild.change_voice_state(channel=voice_channel, self_deaf=True)
                        except Exception as e:
                            self.logger.error(f"[WORKER ERROR] Ошибка входа: {e}")
                            await self.redis.delete(f"vc_worker:{voice_channel.id}")
                            await self.redis.srem(f"guild_active_workers:{guild_id}", self.worker_id)
                            continue
                    
                    if not player.current:
                        track = await player.play_next()
                        if track: await player.send_ui_update(track)
                
                else:
                    player: CustomPlayer = guild.voice_client
                    if not player: continue

                    if action == "pause_resume":
                        if player.paused:
                            await player.resume()
                        else:
                            await player.pause()
                        if player.current:
                            await player.send_ui_update(player.current)
                    
                    elif action == "skip":
                        await player.stop()
                    
                    elif action == "previous":
                        track = await player.play_previous()
                        if track: await player.send_ui_update(track)
                    
                    elif action == "stop":
                        await player.teardown()
                    
                    elif action == "toggle_loop":
                        player.loop_mode = (player.loop_mode + 1) % 3
                        await player.send_ui_update(player.current)
                    
                    elif action == "toggle_autopilot":
                        player.autopilot = not player.autopilot
                        await player.send_ui_update(player.current)
                        
                    elif action == "shuffle":
                        queue = await self.redis.lrange(player.queue_key, 0, -1)
                        if len(queue) > 1:
                            random.shuffle(queue)
                            async with self.redis.pipeline(transaction=True) as pipe:
                                await pipe.delete(player.queue_key)
                                await pipe.rpush(player.queue_key, *queue)
                                await pipe.execute()

    async def on_voice_state_update(self, member, before, after):
        player = getattr(member.guild, "voice_client", None)
        if not player: return
        
        if member.id == self.user.id and not after.channel:
            await player.teardown()
            return
            
        if player.channel:
            non_bots = [m for m in player.channel.members if not m.bot]
            if not non_bots:
                player.cancel_timeout()
                player.timeout_task = self.loop.create_task(player.start_timeout(60))
            else:
                if player.timeout_task:
                    player.cancel_timeout()
                    if not player.current:
                        player.timeout_task = self.loop.create_task(player.start_timeout(300))

def run_worker_process(worker_id: str, token: str):
    bot = WorkerBot(worker_id=worker_id)
    bot.run(token)


if __name__ == "__main__":
    multiprocessing.freeze_support()

    tokens = Config.WORKER_TOKENS
    if not tokens:
        exit()

    processes = []
    for i, token in enumerate(tokens):
        worker_id = str(i + 1)
        p = multiprocessing.Process(target=run_worker_process, args=(worker_id, token))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()