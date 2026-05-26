from urllib.parse import unquote
from utils import check_chat_type, check_class


def parse_message(raw_message):
    try:
        message = raw_message.decode("utf-8", errors="ignore")
        fields = message.split(";")

        if len(fields) < 9:
            return None

        return {
            "chat": check_chat_type(int(fields[6])),
            "player": fields[3],
            "level": fields[5],
            "class": check_class(fields[8]),
            "text": unquote(fields[4])
        }

    except Exception:
        return None
