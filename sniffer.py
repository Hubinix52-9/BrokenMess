"""Network packet sniffer for game chat messages"""

import threading
import logging
from scapy.all import sniff, UDP
from parser import parse_message
from config import SERVER_IP

logger = logging.getLogger(__name__)


class PacketSniffer:
    """Sniffs UDP packets and parses game chat messages"""
    
    def __init__(self, callback, server_ip=SERVER_IP, debug=False):
        """Initialize sniffer
        
        Args:
            callback: Function to call with parsed message dict
            server_ip: IP address to filter packets from
            debug: Enable debug logging of all UDP packets
        """
        self.callback = callback
        self.server_ip = server_ip
        self.debug = debug
        self.thread = None
        self.running = False
        self.stats = {
            'total_packets': 0,
            'parsed_messages': 0,
            'parse_errors': 0
        }
    
    def _packet_handler(self, packet):
        """Process incoming packet"""
        try:
            # Check if packet has UDP layer
            if not packet.haslayer(UDP):
                return
            
            self.stats['total_packets'] += 1
            
            # Skip DNS queries/responses
            if packet[UDP].sport == 53 or packet[UDP].dport == 53:
                return
            
            # Extract raw payload
            raw_payload = bytes(packet[UDP].payload)
            
            if self.debug:
                src_ip = packet[1].src if len(packet) > 1 else "?"
                src_port = packet[UDP].sport
                payload_len = len(raw_payload)
                logger.info(f"[PKT] {src_ip}:{src_port} -> {payload_len} bytes")
                if payload_len < 200:
                    try:
                        decoded = raw_payload.decode('utf-8', errors='ignore')
                        logger.info(f"     Payload: {decoded[:100]}")
                    except:
                        pass
            
            # Parse message
            parsed = parse_message(raw_payload)
            
            if parsed:
                self.stats['parsed_messages'] += 1
                self.callback(parsed)
                if self.debug:
                    logger.info(f"✓ Parsed: {parsed['player']} -> {parsed['chat']}")
            else:
                self.stats['parse_errors'] += 1
                if self.debug and len(raw_payload) > 0:
                    logger.debug(f"✗ Parse failed for {len(raw_payload)} byte payload")
        
        except Exception as e:
            logger.debug(f"Error processing packet: {e}")
    
    def start(self):
        """Start sniffing in background thread"""
        if self.running:
            logger.warning("Sniffer already running")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._sniff,
            daemon=True,
            name="PacketSniffer"
        )
        self.thread.start()
        logger.info(f"Sniffer started, listening on {self.server_ip}")
        if self.debug:
            logger.info("DEBUG MODE ENABLED - Logging all packets")
    
    def _sniff(self):
        """Sniffing loop (runs in thread)"""
        try:
            # Try filtering by IP first
            sniff(
                prn=self._packet_handler,
                filter=f"udp and host {self.server_ip}",
                store=False,
                stop_filter=lambda x: not self.running
            )
        except PermissionError:
            logger.error(
                "Packet sniffing requires admin/root privileges. "
                "Please run as administrator."
            )
            self.running = False
        except Exception as e:
            logger.error(f"Sniffer error: {e}")
            self.running = False
    
    def get_stats(self):
        """Return statistics about captured packets"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics counter"""
        self.stats = {
            'total_packets': 0,
            'parsed_messages': 0,
            'parse_errors': 0
        }
    
    def stop(self):
        """Stop sniffing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Sniffer stopped")
