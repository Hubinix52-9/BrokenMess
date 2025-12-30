from scapy.all import sniff, IP, Raw
from urllib.parse import unquote

SERVER_IP = "51.83.239.5"
MY_IP = "192.168.1.76"

def packet_callback(packet):
    if IP in packet:
        if packet[IP].src == SERVER_IP and packet[IP].dst == MY_IP:
            if Raw in packet:
                raw = packet[Raw].load
                if raw and raw[0] == ord('2') and raw[2] == ord('1') and raw[3] == ord('0'):
                    print(raw)
                    decrypt_message(raw)

def check_class(class_value):
    if str(class_value[1]).isnumeric():
        class_id = int(class_value[0:2])
    else:
        class_id = int(class_value[0])
    
    classes = {
        2: "BB",
        3: "RC",
        4: "MO",
        7: "VD",
        8: "SH",
        10: "ŁK",
        11: "DR"}
    return classes[class_id]

def check_chat_type(chat_type_value):
    chat_type = {
        0: "Globalny",
        1: "Handlowy",
        7: "Wyprawowy",
        8: "Lokalny",
        5: "Dla nowych"
    }

    return chat_type.get(chat_type_value, "other")


def decrypt_message(raw_message):
    message = raw_message.decode('utf-8', errors='ignore')
    fields = message.split(';')
    unquoted_message = unquote(fields[4])


    player_class = check_class(fields[8])
    player_name = fields[3]
    player_level = fields[5]
    players_message = unquoted_message
    chat_type = check_chat_type(int(fields[6]))

    print(f'[{chat_type}]')
    print(f'{player_level} {player_class} {player_name} - {players_message}')
    print('-----------------------------------')

sniff(prn=packet_callback, store=False)