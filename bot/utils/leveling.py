import random

XP_PER_MESSAGE_MIN = 15
XP_PER_MESSAGE_MAX = 25
MESSAGE_COOLDOWN = 5
XP_PER_VOICE_MINUTE = 10

def get_message_xp() -> int:
    return random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)

def get_voice_xp(minutes: int) -> int:
    return minutes * XP_PER_VOICE_MINUTE

def get_xp_for_level(level: int) -> int:
    return 100 * (level ** 2)

def get_level_from_xp(xp: float) -> int:
    return int((xp / 100) ** 0.5)

def generate_progress_bar(current_xp: float, level: int, length: int = 15) -> str:
    current_level_xp = get_xp_for_level(level)
    next_level_xp = get_xp_for_level(level + 1)
    
    xp_needed = next_level_xp - current_level_xp
    xp_have = current_xp - current_level_xp
    
    if xp_needed <= 0: return f"[{'█' * length}]"
    
    progress = max(0.0, min(1.0, xp_have / xp_needed))
    filled = int(length * progress)
    return f"[{'█' * filled}{'░' * (length - filled)}]"