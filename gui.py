import json
import os
from pathlib import Path
import tkinter as tk
from config import MAX_MESSAGES, BG, FG, ENTRY_BG, TEXT_BG, CHAT_COLORS


class ChatLoggerApp:
    def __init__(self, root):
        self.root = root

        self.messages = []
        self.settings_path = self._get_settings_path()
        self.settings = self._load_settings()

        self.autoscroll = tk.BooleanVar(value=self.settings.get("autoscroll", True))

        self.chat_filters = {
            k: tk.BooleanVar(value=self.settings.get("chat_filters", {}).get(k, True))
            for k in CHAT_COLORS
        }

        self._build_gui()

    def _get_settings_path(self):
        config_dir = os.getenv("APPDATA")
        if config_dir:
            return Path(config_dir) / "BrokenMess" / "settings.json"
        return Path.home() / ".brokenmess_settings.json"

    def _load_settings(self):
        try:
            with self.settings_path.open("r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    def save_settings(self):
        data = {
            "autoscroll": self.autoscroll.get(),
            "chat_filters": {
                chat: var.get() for chat, var in self.chat_filters.items()
            },
            "text_filter": self.filter_entry.get()
        }

        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with self.settings_path.open("w", encoding="utf-8") as settings_file:
                json.dump(data, settings_file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _update_filters(self):
        self.save_settings()
        self.refresh_view()

    # =========================
    # GUI
    # =========================
    def _build_gui(self):
        self.root.title("BrokenMess")
        self.root.geometry("550x300")
        self.root.attributes("-alpha", 0.85)
        self.root.attributes("-topmost", True)

        left = tk.Frame(self.root, bg=BG, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y)

        for chat, var in self.chat_filters.items():
            tk.Checkbutton(
                left,
                text=chat,
                variable=var,
                bg=BG,
                fg=CHAT_COLORS[chat],
                selectcolor=BG,
                activebackground=BG,
                activeforeground=CHAT_COLORS[chat],
                command=self._update_filters
            ).pack(anchor=tk.W)

        self.filter_entry = tk.Entry(left, bg=ENTRY_BG, fg=FG)
        self.filter_entry.pack(fill=tk.X)
        self.filter_entry.insert(0, self.settings.get("text_filter", ""))
        self.filter_entry.bind("<KeyRelease>", lambda e: self._update_filters())

        right = tk.Frame(self.root, bg=BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.textbox = tk.Text(
            right,
            bg=TEXT_BG,
            fg=FG,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bd=0
        )
        self.textbox.pack(fill=tk.BOTH, expand=True)


        tk.Button(left, text="Clear", bg=ENTRY_BG, fg=FG, command=self.clear_messages).pack(fill=tk.X, pady=0)

        tk.Checkbutton(
            left,
            text="Auto-scroll",
            variable=self.autoscroll,
            bg=BG,
            fg=FG,
            selectcolor=BG,
            activebackground=BG,
            activeforeground=FG,
            command=self._update_filters
        ).pack(anchor=tk.W, pady=(5, 0))
 

        for chat, color in CHAT_COLORS.items():
            self.textbox.tag_config(chat, foreground=color)

        self.textbox.tag_config("meta", foreground="#00ff00")

    # =========================
    # MESSAGE HANDLING
    # =========================
    def add_message(self, msg):
        self.messages.append(msg)

        if len(self.messages) > MAX_MESSAGES:
            removed = self.messages.pop(0)

            if self._passes_filters(removed):
                self.refresh_view()
                return

        if self._passes_filters(msg):
            self._append(msg)

    def _append(self, msg):
        self.textbox.config(state=tk.NORMAL)

        meta = f'{msg["player"]} {msg["level"]} {msg["class"]} - '
        self.textbox.insert(tk.END, meta, "meta")
        self.textbox.insert(tk.END, msg["text"] + "\n", msg["chat"])

        self.textbox.config(state=tk.DISABLED)
        
        if self.autoscroll.get():
            self.textbox.see(tk.END)

    def refresh_view(self, *args, **kwargs):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete("1.0", tk.END)

        for msg in self.messages:
            if self._passes_filters(msg):
                meta = f'{msg["player"]} {msg["level"]} {msg["class"]} - '
                self.textbox.insert(tk.END, meta, "meta")
                self.textbox.insert(tk.END, msg["text"] + "\n", msg["chat"])

        self.textbox.config(state=tk.DISABLED)
        
        if self.autoscroll.get():
            self.textbox.see(tk.END)

    def clear_messages(self):
        self.messages.clear()
        self.refresh_view()

    def _passes_filters(self, msg):
        if not self.chat_filters[msg["chat"]].get():
            return False

        text_filter = self.filter_entry.get().lower()
        if text_filter:
            combined = f'{msg["player"]} {msg["text"]}'.lower()
            return text_filter in combined

        return True
