"""Helper functions for message parsing"""


def check_chat_type(chat_id):
    """Map chat type ID to chat name
    
    Args:
        chat_id: Integer ID from packet
        
    Returns:
        Chat type name (str)
    """
    chat_types = {
        1: "Handlowy",      # Trading
        7: "Wyprawowy",     # Expedition
        8: "Lokalny",       # Local
        2: "Globalny",      # Global
        0: "Dla_nowych",    # For new players
        6: "Drużynowy",     # Team
    }
    return chat_types.get(chat_id, "Other")


def check_class(class_id):
    """Map class ID to class name
    
    Args:
        class_id: Integer ID from packet
        
    Returns:
        Class name (str)
    """
    classes = {
        2: "Barba",     # Barbarian
        3: "Ryc",       # Knight
        4: "Mo",        # Mage
        7: "Vd",        # Vampire
        8: "Sh",        # Shadow/Rogue
        10: "Łuk",      # Archer
        11: "Druid",    # Druid
    }
    return classes.get(int(class_id), "Unknown")
