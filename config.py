from settings import load_settings


_settings = load_settings()
_theme = _settings["theme"]

SERVER_IP = _settings.get("server_ip")
MY_IP = _settings.get("my_ip")
MAX_MESSAGES = _settings["max_messages"]

BG = _theme["bg"]
FG = _theme["fg"]
ENTRY_BG = _theme["entry_bg"]
TEXT_BG = _theme["text_bg"]

CHAT_COLORS = _settings["chat_colors"]
