"""Network packet sniffer for game chat messages with settings fallback."""

import logging
import socket
import threading

from scapy.all import IP, Raw, TCP, sniff

from parser import parse_message
from settings import load_settings

logger = logging.getLogger(__name__)


def get_my_ip_automatically():
    """Automatically detect the local machine IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception as e:
        logger.error(f"Nie udalo sie automatycznie pobrac my_ip: {e}")
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class PacketSniffer:
    """Sniffs TCP packets and parses game chat messages."""

    def __init__(self, callback, debug=False):
        """Initialize sniffer with settings evaluation and auto-detection fallback."""
        self.callback = callback
        self.debug = debug
        self.thread = None
        self.running = False
        self.stats = {
            "total_packets": 0,
            "parsed_messages": 0,
            "parse_errors": 0
        }

        settings = load_settings()
        my_ip = settings.get("my_ip")
        server_ip = settings.get("server_ip")

        if my_ip and str(my_ip).strip():
            self.my_ip = str(my_ip).strip()
            logger.info(f"[SETTINGS] Uzywam adresu IP klienta z settings.json: {self.my_ip}")
        else:
            logger.info("[SETTINGS] Brak my_ip w settings.json. Uruchamiam automatyczne wykrywanie...")
            self.my_ip = get_my_ip_automatically()
            logger.info(f"[AUTO] Wykryto adres IP klienta: {self.my_ip}")

        if server_ip and str(server_ip).strip():
            self.server_ip = str(server_ip).strip()
            self.auto_detect_server = False
            logger.info(f"[SETTINGS] Uzywam stalego adresu IP serwera z settings.json: {self.server_ip}")
        else:
            self.server_ip = None
            self.auto_detect_server = True
            logger.warning("[SETTINGS] Brak server_ip w settings.json. Serwer zostanie wykryty automatycznie przy pierwszym pakiecie gry.")

    def _packet_handler(self, packet):
        """Process incoming packet."""
        try:
            if not (packet.haslayer(IP) and packet.haslayer(TCP) and packet.haslayer(Raw)):
                return

            if packet[IP].dst != self.my_ip:
                return

            if self.server_ip and packet[IP].src != self.server_ip:
                return

            raw_payload = packet[Raw].load
            if not raw_payload or len(raw_payload) < 4:
                return

            if (
                raw_payload[0] == ord("2")
                and raw_payload[2] == ord("1")
                and raw_payload[3] == ord("0")
            ):
                if self.auto_detect_server and self.server_ip is None:
                    self.server_ip = packet[IP].src
                    logger.info(f"[AUTO] Wykryto IP serwera gry w locie: {self.server_ip}")

                self.stats["total_packets"] += 1

                if self.debug:
                    src_port = packet[TCP].sport
                    logger.info(f"[PKT] {packet[IP].src}:{src_port} -> {len(raw_payload)} bytes")
                    print(raw_payload)

                parsed = parse_message(raw_payload)

                if parsed:
                    self.stats["parsed_messages"] += 1
                    self.callback(parsed)
                else:
                    self.stats["parse_errors"] += 1

        except Exception as e:
            logger.debug(f"Error processing packet: {e}")

    def start(self):
        """Start sniffing in background thread."""
        if self.running:
            logger.warning("Sniffer juz dziala.")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._sniff,
            daemon=True,
            name="PacketSniffer"
        )
        self.thread.start()

        logger.info("Sniffer uruchomiony pomyslnie.")
        if self.debug:
            logger.info("Tryb debug aktywny.")

    def _sniff(self):
        """Sniffing loop running in a background thread."""
        try:
            bpf_filter = f"tcp and dst host {self.my_ip}"

            if self.server_ip and not self.auto_detect_server:
                bpf_filter += f" and src host {self.server_ip}"

            sniff(
                prn=self._packet_handler,
                filter=bpf_filter,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except PermissionError:
            logger.error("Brak uprawnien administratora do przechwytywania pakietow.")
            self.running = False
        except Exception as e:
            logger.error(f"Blad krytyczny sniffera: {e}")
            self.running = False

    def stop(self):
        """Stop sniffing."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Sniffer zatrzymany.")
