# Diese Datei stellt die Verbindung zu Twitch her und liest die Nachrichten aus dem Chat aus.
# Die Nachrichten werden in einer Warteschlange gespeichert, die dann in einem bestimmten Zeitintervall abgearbeitet wird.
# Du brauchst diese Datei nicht zu ändern, wenn du nur die Nachrichten aus dem Chat auslesen möchtest.

import sys
import socket
import re
import random
import time

MAX_TIME_TO_WAIT_FOR_LOGIN = 3

class Twitch:
    re_prog = None
    sock = None
    partial = b''
    login_ok = False
    channel = ''
    login_timestamp = 0

    def twitch_connect(self, channel):
        if self.sock: self.sock.close()
        self.sock = None
        self.partial = b''
        self.login_ok = False
        self.channel = channel

        # Compile Regex
        self.re_prog = re.compile(b'^(?::(?:([^ !\r\n]+)![^ \r\n]*|[^ \r\n]*) )?([^ \r\n]+)(?: ([^:\r\n]*))?(?: :([^\r\n]*))?\r\n', re.MULTILINE)

        # Erstelle Socket  
        print('Connecting to Twitch...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Verbinde mit Twitch
        self.sock.connect(('irc.chat.twitch.tv', 6667))

        # Anonym anmelden
        user = 'justinfan%i' % random.randint(10000, 99999)
        print('Mit Twitch verbunden. Anonym angemeldet als %s' % user)

        self.sock.send(('PASS asdf\r\nNICK %s\r\n' % user).encode())
        self.sock.settimeout(1.0/60.0)

        self.login_timestamp = time.time()

    # Erneuter Verbindungsaufbau nach Verbindungsabbruch
    def reconnect(self, delay):
        time.sleep(delay)
        self.twitch_connect(self.channel)

    # Gibt eine Liste mit allen empfangenen Nachrichten zurück
    def receive_and_parse_data(self):
        buffer = b''
        while True:
            received = b''
            try:
                received = self.sock.recv(4096)
            except socket.timeout:
                break
            except Exception as e:
                print('Unexpected connection error. Reconnecting in a second...', e)
                self.reconnect(1)
                return []
                
            if not received:
                print('Connection closed by Twitch. Reconnecting in 5 seconds...')
                self.reconnect(5)
                return []
            buffer += received

        if buffer:
            # Verbleibende Daten aus dem letzten Durchlauf anhängen
            if self.partial:
                buffer = self.partial + buffer
                self.partial = []

            # Nachrichten parsen
            res = []
            matches = list(self.re_prog.finditer(buffer))
            for match in matches:
                res.append({
                    'name':     (match.group(1) or b'').decode(errors='replace'),
                    'command':  (match.group(2) or b'').decode(errors='replace'),
                    'params':   list(map(lambda p: p.decode(errors='replace'), (match.group(3) or b'').split(b' '))),
                    'trailing': (match.group(4) or b'').decode(errors='replace'),
                })

            # Speichere verbleibende Daten für den nächsten Durchlauf
            if not matches:
                self.partial += buffer
            else:
                end = matches[-1].end()
                if end < len(buffer):
                    self.partial = buffer[end:]

                if matches[0].start() != 0:
                    print('irgendetwas mit dem buffer ist schiefgelaufen')

            return res

        return []

    def twitch_receive_messages(self):
        privmsgs = []
        for irc_message in self.receive_and_parse_data():
            cmd = irc_message['command']
            if cmd == 'PRIVMSG':
                privmsgs.append({
                    'username': irc_message['name'],
                    'message': irc_message['trailing'],
                })
            elif cmd == 'PING':
                self.sock.send(b'PONG :tmi.twitch.tv\r\n')
            elif cmd == '001':
                print('Erfolgreich Eingelogt.. Verbindet sich mit dem Kanal %s.' % self.channel)
                self.sock.send(('JOIN #%s\r\n' % self.channel).encode())
                self.login_ok = True
            elif cmd == 'JOIN':
                print('Erfolgreich verbunden mit dem Kanal %s' % irc_message['params'][0])
                
            elif cmd == 'NOTICE':
                print('Server notice:', irc_message['params'], irc_message['trailing'])
            elif cmd == '002': continue
            elif cmd == '003': continue
            elif cmd == '004': continue
            elif cmd == '375': continue
            elif cmd == '372': continue
            elif cmd == '376': continue
            elif cmd == '353': continue
            elif cmd == '366': continue
            else:
                print('Unbehandelte Nachricht:', irc_message)

        if not self.login_ok:
            # Wir haben uns noch nicht angemeldet. Wenn wir zu lange warten, verbinden wir uns neu.
            if time.time() - self.login_timestamp > MAX_TIME_TO_WAIT_FOR_LOGIN:
                print('Keine Antwort von Twitch. Verbindung wird neu aufgebaut...')
                self.reconnect(0)
                return []

        return privmsgs
