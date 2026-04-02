import random

REDIS_KEY_XP = "global_xp"
REDIS_KEY_MESSAGES = "global_messages"
REDIS_KEY_VOICE = "global_voice_mins"

XP_PER_MESSAGE_MIN = 15
XP_PER_MESSAGE_MAX = 25
MESSAGE_COOLDOWN = 1
XP_PER_VOICE_MINUTE = 10

def get_message_xp() -> int:
    return random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)

def get_voice_xp(minutes: int) -> int:
    return minutes * XP_PER_VOICE_MINUTE

def get_xp_for_level(level: int) -> int:
    return 100 * (level ** 2)

def get_level_from_xp(xp: float) -> int:
    return int((xp / 100) ** 0.5)

def format_voice_time(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        return f"{hours}ч {minutes}м"
    return f"{minutes}м"

def get_progress_bar_stats(current_xp: float, level: int):
    current_level_xp = get_xp_for_level(level)
    next_level_xp = get_xp_for_level(level + 1)
    
    xp_needed = next_level_xp - current_level_xp
    xp_have = current_xp - current_level_xp
    
    if xp_needed <= 0:
        return 100.0, xp_have, xp_needed
        
    percentage = max(0.0, min(100.0, (xp_have / xp_needed) * 100))
    return percentage, xp_have, xp_needed