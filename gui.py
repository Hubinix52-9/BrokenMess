import tkinter as tk
from settings import get_settings_path, load_settings, save_settings


class ChatLoggerApp:
    def __init__(self, root):
        self.root = root

        self.messages = []
        self.settings_path = get_settings_path()
        self.settings = load_settings()
        self._geometry_save_job = None
        self.theme = self.settings["theme"]
        self.chat_colors = self.settings["chat_colors"]
        self.max_messages = self.settings["max_messages"]
        self.menu_visible = tk.BooleanVar(value=self.settings.get("menu_visible", True))

        self.autoscroll = tk.BooleanVar(value=self.settings.get("autoscroll", True))

        self.chat_filters = {
            k: tk.BooleanVar(value=self.settings.get("chat_filters", {}).get(k, True))
            for k in self.chat_colors
        }

        self._build_gui()

    def save_settings(self):
        self.settings["autoscroll"] = self.autoscroll.get()
        self.settings["chat_filters"] = {
            chat: var.get() for chat, var in self.chat_filters.items()
        }
        self.settings["text_filter"] = self.filter_entry.get()
        self.settings["menu_visible"] = self.menu_visible.get()
        self.settings["window_geometry"] = self.root.geometry()
        save_settings(self.settings)

    def _update_filters(self):
        self.save_settings()
        self.refresh_view()

    def _schedule_geometry_save(self, event):
        if event.widget is not self.root:
            return

        if self._geometry_save_job is not None:
            self.root.after_cancel(self._geometry_save_job)

        self._geometry_save_job = self.root.after(300, self._save_geometry)

    def _save_geometry(self):
        self._geometry_save_job = None
        self.save_settings()

    def toggle_menu(self):
        self.menu_visible.set(not self.menu_visible.get())

        if self.menu_visible.get():
            self.left_panel.pack(side=tk.LEFT, fill=tk.Y, before=self.right_panel)
            self.menu_toggle.config(text="<")
        else:
            self.left_panel.pack_forget()
            self.menu_toggle.config(text=">")

        self.save_settings()

    # =========================
    # GUI
    # =========================
    def _build_gui(self):
        self.root.title("BrokenMess")
        self.root.geometry(self.settings.get("window_geometry", "550x300"))
        self.root.attributes("-alpha", 0.85)
        self.root.attributes("-topmost", True)
        self.root.bind("<Configure>", self._schedule_geometry_save)

        self.toggle_bar = tk.Frame(self.root, bg=self.theme["bg"])
        self.toggle_bar.pack(side=tk.LEFT, fill=tk.Y)

        self.menu_toggle = tk.Button(
            self.toggle_bar,
            text="<" if self.menu_visible.get() else ">",
            width=2,
            bg=self.theme["entry_bg"],
            fg=self.theme["fg"],
            activebackground=self.theme["bg"],
            activeforeground=self.theme["fg"],
            command=self.toggle_menu
        )
        self.menu_toggle.pack(fill=tk.Y)

        self.left_panel = tk.Frame(self.root, bg=self.theme["bg"], width=200)
        if self.menu_visible.get():
            self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        for chat, var in self.chat_filters.items():
            tk.Checkbutton(
                self.left_panel,
                text=chat,
                variable=var,
                bg=self.theme["bg"],
                fg=self.chat_colors[chat],
                selectcolor=self.theme["bg"],
                activebackground=self.theme["bg"],
                activeforeground=self.chat_colors[chat],
                command=self._update_filters
            ).pack(anchor=tk.W)

        self.filter_entry = tk.Entry(self.left_panel, bg=self.theme["entry_bg"], fg=self.theme["fg"])
        self.filter_entry.pack(fill=tk.X)
        self.filter_entry.insert(0, self.settings.get("text_filter", ""))
        self.filter_entry.bind("<KeyRelease>", lambda e: self._update_filters())

        self.right_panel = tk.Frame(self.root, bg=self.theme["bg"])
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.textbox = tk.Text(
            self.right_panel,
            bg=self.theme["text_bg"],
            fg=self.theme["fg"],
            wrap=tk.WORD,
            state=tk.DISABLED,
            bd=0
        )
        self.textbox.pack(fill=tk.BOTH, expand=True)


        tk.Button(
            self.left_panel,
            text="Clear",
            bg=self.theme["entry_bg"],
            fg=self.theme["fg"],
            command=self.clear_messages
        ).pack(fill=tk.X, pady=0)

        tk.Checkbutton(
            self.left_panel,
            text="Auto-scroll",
            variable=self.autoscroll,
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            selectcolor=self.theme["bg"],
            activebackground=self.theme["bg"],
            activeforeground=self.theme["fg"],
            command=self._update_filters
        ).pack(anchor=tk.W, pady=(5, 0))
 

        for chat, color in self.chat_colors.items():
            self.textbox.tag_config(chat, foreground=color)

        self.textbox.tag_config("meta", foreground=self.theme["meta_fg"])

    # =========================
    # MESSAGE HANDLING
    # =========================
    def add_message(self, msg):
        self.messages.append(msg)

        if len(self.messages) > self.max_messages:
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
            terms = [
                term.strip()
                for term in text_filter.split("&")
                if term.strip()
            ]
            combined = f'{msg["player"]} {msg["text"]}'.lower()
            return any(term in combined for term in terms)

        return True
