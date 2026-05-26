# BrokenMess - Chat Logger

Aplikacja GUI do przechwytywania i wyświetlania wiadomości z czatu gry (działającej na serwerze online).

## Funkcjonalność

- 📡 **Sniffing pakietów sieciowych** - przechwytuje wiadomości UDP z serwera gry
- 🎨 **Kolorowy interfejs** - każdy typ czatu ma inny kolor
- 🔍 **Filtrowanie** - wyszukiwanie po graczu/wiadomości, filtr typów czatów
- ⚡ **Auto-scroll** - automatyczne przewijanie do najnowszych wiadomości
- 💾 **Historia** - przechowuje do 2000 ostatnich wiadomości

## Architektura

```
main.py          - Entry point, inicjalizacja GUI + sniffera
├── gui.py       - Interfejs Tkinter
├── sniffer.py   - Przechwytywanie pakietów UDP (Scapy)
├── parser.py    - Parsowanie raw danych z gry
├── utils.py     - Funkcje pomocnicze (mapowanie typów)
└── config.py    - Konfiguracja (IP, kolory, limity)
```

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom aplikację (wymaga uprawnień admin/root!)
python main.py
```

## Protokół gry

Wiadomości przychodzą jako pakiety UDP w formacie:

```
[0];[1];[2];[nick];[wiadomość];[level];[typ_czatu];[x];[klasa]
```

Przykład:
```
2;10;400845;PaziOo;ryc%20arena%20t5%20last;140;7;0;4
```

- `[3]` = Nick gracza
- `[4]` = Wiadomość (URL-encoded)
- `[5]` = Poziom
- `[6]` = Typ czatu (1=handlowy, 7=wyprawowy, 8=lokalny, 2=globalny)
- `[8]` = Klasa (2=barba, 3=ryc, 4=mo, 7=vd, 8=sh, 10=łuk, 11=druid)

## Problemy naprawione

1. ✅ **Brakujące utils.py** - Dodano mapowanie typów czatów i klas
2. ✅ **Brakujące sniffer.py** - Implementacja sniffingu z Scapy + threading
3. ✅ **GUI state management** - Zoptymalizowana logika odświeżania tekstbox
4. ✅ **Error handling** - Obsługa wyjątków w main.py + logging
5. ✅ **Brakujący stop()** - Sniffer teraz poprawnie się zatrzymuje
6. ✅ **README.md** - Nowa dokumentacja

## Wymagania

- Python 3.7+
- Scapy (wymaga admin/root do przechwytywania pakietów)
- Tkinter (zwykle wbudowany)

## Uwagi

- ⚠️ **Wymaga uprawnień administratora** na Windows / root na Linux
- ⚠️ Zmienna `SERVER_IP` w `config.py` musi być IP serwera gry
- ⚠️ Aplikacja przechowuje max 2000 wiadomości w RAM

## Rozwój

Możliwe ulepszenia:
- Baza danych SQLite dla historii
- Export do CSV/JSON
- Konfiguracja GUI
- Obsługa wielu serwerów
