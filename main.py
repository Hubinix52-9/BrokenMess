import tkinter as tk
import logging
from gui import ChatLoggerApp
from sniffer import PacketSniffer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        root = tk.Tk()
        app = ChatLoggerApp(root)

        sniffer = PacketSniffer(
            lambda msg: root.after(0, app.add_message, msg)
        )
        
        try:
            sniffer.start()
        except Exception as e:
            logger.error(f"Failed to start packet sniffer: {e}")
            root.destroy()
            return

        def on_closing():
            sniffer.stop()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
