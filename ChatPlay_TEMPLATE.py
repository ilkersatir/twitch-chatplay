# Diese Datei enthält die Hauptlogik, um Twitch-Chat-Nachrichten zu verarbeiten und in Spielbefehle umzuwandeln.
# Der Code ist in Python 3.X geschrieben.
# Es werden 2 weitere Dateien benötigt, um diesen Code auszuführen:
#     # ChatPlay_KeyCodes.py enthält die Tastaturcodes und Funktionen, um Tasten im Spiel zu drücken. Du solltest diese Datei nicht ändern.
#     # ChatPlay_Connection.py ist der Code, der sich tatsächlich mit Twitch verbindet. Du solltest diese Datei nicht ändern.

# Der Quellcode stammt hauptsächlich von:
#     # Wituz's "Twitch Plays" Tutorial: http://www.wituz.com/make-your-own-twitch-plays-stream.html
#     # PythonProgramming's "Python Plays GTA V" Tutorial: https://pythonprogramming.net/direct-input-game-python-plays-gta-v/

# Haftungsausschluss:
#     # Dieser Code ist NICHT dazu gedacht, professionell optimiert oder organisiert zu werden.
#     # Ich habe eine einfache Version erstellt, die gut für Livestreams funktioniert, und ich teile es für private Zwecke.


##########################################################

TWITCH_CHANNEL = 'dervonqusengs' # Ersetze dies mit deinem Twitch-Benutzernamen. MUSS KLEIN GESCHRIEBEN WERDEN.

##########################################################

import keyboard
import ChatPlay_Connection
import pydirectinput
import random
import pyautogui
import concurrent.futures
from ChatPlay_KeyCodes import *

##########################################################

# NACHRICHTEN_INTERVAL = steuert, wie schnell wir eingehende Twitch-Chat-Nachrichten verarbeiten. Es ist die Anzahl der Sekunden, die es dauern wird, alle Nachrichten in der Warteschlange zu verarbeiten.
# Dies wird verwendet, da Twitch Nachrichten in "Stapeln" liefert, anstatt eine nach der anderen. Also verarbeiten wir die Nachrichten über die Dauer der Nachrichtenrate, anstatt die gesamte Stapelung auf einmal zu verarbeiten.
# Eine kleinere Zahl bedeutet, dass wir schneller durch die Nachrichtenwarteschlange gehen, aber wir verbrauchen schnellere Nachrichten und die Aktivität kann "stagnieren", während auf einen neuen Stapel gewartet wird.
# Eine höhere Zahl bedeutet, dass wir langsamer durch die Warteschlange gehen und die Nachrichten gleichmäßiger verteilt sind, aber die Verzögerung aus der Sicht der Zuschauer höher ist.
# Du kannst dies auf 0 setzen, um die Warteschlange zu deaktivieren und alle Nachrichten sofort zu verarbeiten. Wenn jedoch die Wartezeit vor einem anderen "Stapel" von Nachrichten auffälliger ist.
NACHRICHTEN_INTERVAL = 0.5

# MAX_QUEUE_LENGTH = begrenzt die Anzahl der Befehle, die in einem bestimmten "Batch" von Nachrichten verarbeitet werden.
# z.B. Wenn du einen Stapel von 50 Nachrichten erhältst, kannst du nur die ersten 10 verarbeiten und die anderen ignorieren.
# Dies ist nützlich für Spiele, bei denen zu viele Eingaben auf einmal das Gameplay tatsächlich behindern können.
# Auf ~ 50 setzen ist gut für totale Chaos, ~ 5-10 ist gut für 2D-Plattformspiele
MAX_QUEUE_LENGTH = 20  

# MAX_WORKERS = Maximale Anzahl von Threads, die gleichzeitig ausgeführt werden können. Dies ist für die Verarbeitung von Nachrichten gedacht.
MAX_WORKERS = 100 

last_time = time.time()
message_queue = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks = []
pyautogui.FAILSAFE = False

##########################################################

# Eine optionale Countdown-Vorlaufzeit, bevor du mit dem Spiel beginnst. Dies ist nützlich, wenn du ein Spiel startest, das eine lange Ladezeit hat.
countdown = 10
while countdown > 0:
    print(countdown)
    countdown -= 1
    time.sleep(1)

t = ChatPlay_Connection.Twitch();
t.twitch_connect(TWITCH_CHANNEL);

def handle_message(message):
    try:
        msg = message['message'].lower()
        username = message['username'].lower()

        print("Nachricht: [" + msg + "] vom User [" + username + "]")

        # Jetzt, da du eine Chat-Nachricht hast, ist dies der Ort, an dem du deine Spiellogik hinzufügst.
        # Verwende die "HoldKey (KEYCODE)" -Funktion, um eine Tastaturtaste zu drücken und gedrückt zu halten.
        # Verwende die "ReleaseKey (KEYCODE)" -Funktion, um eine bestimmte Tastaturtaste freizugeben.
        # Verwende die "HoldAndReleaseKey (KEYCODE, SECONDS)" -Funktion, um eine Taste für X Sekunden zu drücken und dann loszulassen.
        # Verwende die pydirectinput-Bibliothek, um die Maus zu drücken oder zu bewegen

        # Ich habe unten einige Beispiel-Videospiele-Logikcode hinzugefügt:

        ###################################
        # DARK SOULS 3
        ###################################

        # Wenn die Chat-Nachricht "links" ist, dann wird die A-Taste für 2 Sekunden gedrückt und gehalten.
        if msg == "links": 
            HoldAndReleaseKey(A, 2)

        # Wenn die Chat-Nachricht "rechts" ist, dann wird die D-Taste für 2 Sekunden gedrückt und gehalten.
        if msg == "rechts": 
            HoldAndReleaseKey(D, 2)
            
        # Wenn die Nachricht "vor" ist, dann wird die W-Taste für 2 Sekunden gedrückt und gehalten.
        if msg == "vor": 
            HoldAndReleaseKey(W, 2)

        # Wenn die Nachricht "lauf" ist, dann wird die W-Taste für 10 Sekunden gedrückt und gehalten.
        if msg == "lauf": 
            HoldAndReleaseKey(W, 10)

        # Wenn die Nachricht "stop" ist, dann wird die W-Taste und die S-Taste freigegeben.
        if msg == "stop": 
            ReleaseKey(W)
            ReleaseKey(S)

        # Wenn die Nachricht "roll" ist, dann wird die Leertaste für 0,3 Sekunden gedrückt und gehalten.
        if msg == "roll": 
            HoldAndReleaseKey(SPACE, 0.3)

        # Wenn die Nachricht "hit" ist, dann wird die linke Maustaste gedrückt und nach 1 Sekunde losgelassen.
        if msg == "hit": 
            pydirectinput.mouseDown(button="left")
            time.sleep(1)
            pydirectinput.mouseUp(button="left")

        ####################################
        ####################################

    except Exception as e:
        print("Encountered exception: " + str(e))


while True:

    active_tasks = [t for t in active_tasks if not t.done()]

    # Checkt ob neue Nachrichten verfügbar sind
    new_messages = t.twitch_receive_messages();
    if new_messages:
        message_queue += new_messages; # New messages are added to the back of the queue
        message_queue = message_queue[-MAX_QUEUE_LENGTH:] # Shorten the queue to only the most recent X messages

    messages_to_handle = []
    if not message_queue:
        # Keine Nachrichten in der Warteschlange
        last_time = time.time()
    else:
        # Bestimmt, wie viele Nachrichten wir jetzt verarbeiten sollen
        r = 1 if NACHRICHTEN_INTERVAL == 0 else (time.time() - last_time) / NACHRICHTEN_INTERVAL
        n = int(r * len(message_queue))
        if n > 0:
            # Pop the messages we want off the front of the queue
            messages_to_handle = message_queue[0:n]
            del message_queue[0:n]
            last_time = time.time();

    # Drücke Shift + Backspace, um das Programm automatisch zu beenden
    if keyboard.is_pressed('shift+backspace'):
        exit()

    if not messages_to_handle:
        continue
    else:
        for message in messages_to_handle:
            if len(active_tasks) <= MAX_WORKERS:
                active_tasks.append(thread_pool.submit(handle_message, message))
            else:
                print(f'Warnung: Aktive Aufgaben ({len(active_tasks)}) überschreitet die Anzahl der Threads ({MAX_WORKERS}). ({len(message_queue)} Nachrichten in der Warteschlange)'
