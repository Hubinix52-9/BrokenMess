import json
import os
from copy import deepcopy
from pathlib import Path


DEFAULT_SETTINGS = {
    "server_ip": "",
    "my_ip": "",
    "max_messages": 2000,
    "theme": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "entry_bg": "#2b2b2b",
        "text_bg": "#121212",
        "meta_fg": "#00ff00"
    },
    "chat_colors": {
        "Globalny": "#ff0000",
        "Handlowy": "#ffff00",
        "Wyprawowy": "#00bfff",
        "Lokalny": "#ffffff",
        "Dla_nowych": "#ffa500",
        "Dru\u017cynowy": "#ff00ff",
        "Other": "#808080"
    },
    "chat_filters": {},
    "text_filter": "",
    "autoscroll": True,
    "menu_visible": True,
    "window_geometry": "550x300"
}


def get_settings_path():
    config_dir = os.getenv("APPDATA")
    if config_dir:
        return Path(config_dir) / "BrokenMess" / "settings.json"
    return Path.home() / ".brokenmess_settings.json"


def _merge_settings(defaults, saved):
    merged = deepcopy(defaults)

    for key, value in saved.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value

    _normalize_chat_name(merged, "Dru\u0139\u013dynowy", "Dru\u017cynowy")
    return merged


def _normalize_chat_name(settings, old_name, new_name):
    for section in ("chat_colors", "chat_filters"):
        values = settings.get(section)
        if not isinstance(values, dict) or old_name not in values:
            continue

        old_value = values.pop(old_name)
        values.setdefault(new_name, old_value)


def load_settings():
    settings_path = get_settings_path()

    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            saved_settings = json.load(settings_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        saved_settings = {}

    if not isinstance(saved_settings, dict):
        saved_settings = {}

    settings = _merge_settings(DEFAULT_SETTINGS, saved_settings)
    save_settings(settings)
    return settings


def save_settings(settings):
    settings_path = get_settings_path()

    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with settings_path.open("w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, ensure_ascii=False, indent=2)
    except OSError:
        pass
