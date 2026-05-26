"""Network packet sniffer for game chat messages with Config & Auto-IP fallback"""

import threading
import logging
import socket
from scapy.all import sniff, TCP, IP, Raw
from parser import parse_message

# Importujemy zmienne z konfiguracji
try:
    from config import SERVER_IP, MY_IP
except ImportError:
    # Zabezpieczenie na wypadek, gdyby plik config nie istniał podczas testów
    SERVER_IP = None
    MY_IP = None

logger = logging.getLogger(__name__)


def get_my_ip_automatically():
    """Automatycznie pobiera lokalny adres IP maszyny"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))  # Fikcyjne połączenie do DNS Google
        ip = s.getsockname()[0]
    except Exception as e:
        logger.error(f"Nie udało się automatycznie pobrać MY_IP: {e}")
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class PacketSniffer:
    """Sniffs TCP packets and parses game chat messages"""
    
    def __init__(self, callback, debug=False):
        """Initialize sniffer with config evaluation and auto-detection fallback
        
        Args:
            callback: Function to call with parsed message dict
            debug: Enable debug logging
        """
        self.callback = callback
        self.debug = debug
        self.thread = None
        self.running = False
        self.stats = {
            'total_packets': 0,
            'parsed_messages': 0,
            'parse_errors': 0
        }
        
        # --- LOGIKA CONFIG vs AUTO-DETEKCJA ---
        
        # 1. Walidacja MY_IP
        if MY_IP and str(MY_IP).strip():
            self.my_ip = str(MY_IP).strip()
            logger.info(f"[CONFIG] Używam adresu IP klienta z configu: {self.my_ip}")
        else:
            logger.info("[CONFIG] Brak MY_IP w configu. Uruchamiam automatyczne wykrywanie...")
            self.my_ip = get_my_ip_automatically()
            logger.info(f"[AUTO] Wykryto adres IP klienta: {self.my_ip}")

        # 2. Walidacja SERVER_IP
        if SERVER_IP and str(SERVER_IP).strip():
            self.server_ip = str(SERVER_IP).strip()
            self.auto_detect_server = False
            logger.info(f"[CONFIG] Używam stałego adresu IP serwera z configu: {self.server_ip}")
        else:
            self.server_ip = None
            self.auto_detect_server = True
            logger.warning("[CONFIG] Brak SERVER_IP w configu. Serwer zostanie wykryty automatycznie przy pierwszym pakiecie gry.")
            
        # --------------------------------------
    
    def _packet_handler(self, packet):
        """Process incoming packet"""
        try:
            # Podstawowa weryfikacja warstw sieciowych
            if not (packet.haslayer(IP) and packet.haslayer(TCP) and packet.haslayer(Raw)):
                return
            
            # Ruch musi iść bezpośrednio do nas
            if packet[IP].dst != self.my_ip:
                return

            # Jeśli serwer został już zdefiniowany/wykryty, odrzucamy pakiety z innych IP
            if self.server_ip and packet[IP].src != self.server_ip:
                return

            raw_payload = packet[Raw].load
            if not raw_payload or len(raw_payload) < 4:
                return

            # Sprawdzenie unikalnej sygnatury pakietu czatu gry
            if (raw_payload[0] == ord('2') and 
                raw_payload[2] == ord('1') and 
                raw_payload[3] == ord('0')):
                
                # --- DYNAMICZNA AUTODETEKCJA IP SERWERA ---
                if self.auto_detect_server and self.server_ip is None:
                    self.server_ip = packet[IP].src
                    logger.info(f"[AUTO] Sukces! Wykryto IP serwera gry w locie: {self.server_ip}")
                # ------------------------------------------

                self.stats['total_packets'] += 1
                
                if self.debug:
                    src_port = packet[TCP].sport
                    logger.info(f"[PKT] {packet[IP].src}:{src_port} -> {len(raw_payload)} bytes")
                    print(raw_payload)

                parsed = parse_message(raw_payload)
                
                if parsed:
                    self.stats['parsed_messages'] += 1
                    self.callback(parsed)
                else:
                    self.stats['parse_errors'] += 1
                            
        except Exception as e:
            logger.debug(f"Error processing packet: {e}")
    
    def start(self):
        """Start sniffing in background thread"""
        if self.running:
            logger.warning("Sniffer już działa.")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._sniff,
            daemon=True,
            name="PacketSniffer"
        )
        self.thread.start()
        
        logger.info("Sniffer uruchomiony pomyślnie.")
        if self.debug:
            logger.info("TRYB DEBUG AKTYWNY - Logowanie szczegółów pakietów włączone.")
    
    def _sniff(self):
        """Sniffing loop (runs in thread)"""
        try:
            # Ponieważ filtrujemy pakiety kierowane na nasz adres IP:
            bpf_filter = f"tcp and dst host {self.my_ip}"
            
            # Jeśli od początku znamy stałe IP serwera, optymalizujemy filtr BPF na poziomie jądra
            if self.server_ip and not self.auto_detect_server:
                bpf_filter += f" and src host {self.server_ip}"

            sniff(
                prn=self._packet_handler,
                filter=bpf_filter,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except PermissionError:
            logger.error("BŁĄD: Brak uprawnień administratora (root/sudo) do przechwytywania pakietów.")
            self.running = False
        except Exception as e:
            logger.error(f"Błąd krytyczny sniffera: {e}")
            self.running = False

    def stop(self):
        """Stop sniffing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Sniffer zatrzymany.")