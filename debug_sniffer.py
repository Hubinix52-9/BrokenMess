"""Debug script to test packet sniffing and parsing"""

import logging
import time
import sys
from sniffer import PacketSniffer
from config import SERVER_IP

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def message_callback(msg):
    """Callback for parsed messages"""
    print(f"\n✓ MESSAGE PARSED: {msg['player']} ({msg['class']}, lvl {msg['level']})")
    print(f"  Chat: {msg['chat']}")
    print(f"  Text: {msg['text']}\n")


def main():
    logger.info("=" * 60)
    logger.info("BrokenMess - Packet Sniffer Debug Mode")
    logger.info("=" * 60)
    logger.info(f"Listening on server: {SERVER_IP}")
    logger.info("Looking for UDP packets...")
    logger.info("Press Ctrl+C to stop\n")
    
    sniffer = PacketSniffer(
        callback=message_callback,
        server_ip=SERVER_IP,
        debug=True  # Enable debug logging
    )
    
    try:
        sniffer.start()
        
        # Print statistics every 10 seconds
        while True:
            time.sleep(10)
            stats = sniffer.get_stats()
            logger.info(f"Stats - Total UDP packets: {stats['total_packets']}, "
                       f"Parsed messages: {stats['parsed_messages']}, "
                       f"Parse errors: {stats['parse_errors']}")
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        sniffer.stop()
        stats = sniffer.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total UDP packets captured: {stats['total_packets']}")
        logger.info(f"Successfully parsed messages: {stats['parsed_messages']}")
        logger.info(f"Parse errors: {stats['parse_errors']}")
        
        if stats['total_packets'] == 0:
            logger.warning("\n⚠️  No UDP packets captured!")
            logger.warning("Possible causes:")
            logger.warning("  1. Not running with admin/root privileges")
            logger.warning("  2. Wrong SERVER_IP in config.py")
            logger.warning("  3. Server is not sending packets right now")
            logger.warning("  4. Firewall blocking packets")
        elif stats['parsed_messages'] == 0 and stats['total_packets'] > 0:
            logger.warning("\n⚠️  Captured packets but none matched the format!")
            logger.warning("Check if the packet format matches what parser.py expects")
        
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
