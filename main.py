import tkinter as tk
from gui import ChatLoggerApp
from sniffer import PacketSniffer


def main():
    root = tk.Tk()
    app = ChatLoggerApp(root)

    sniffer = PacketSniffer(
        lambda msg: root.after(0, app.add_message, msg)
    )
    sniffer.start()

    root.mainloop()


if __name__ == "__main__":
    main()
