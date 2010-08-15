import telnetlib
import re

import base


class InvalidPasswordException(Exception):
    pass


class Interface(base.Interface):
    PASSWORD_STRING = 'Password:'
    WELCOME_STRING = 'Welcome, Master'
    WRONG_PASSWORD = 'Wrong password.'
    PLAYING = 'state : playing'
    INPUTS = 'inputs'
    OUTPUT = 'output : '
    TIME = 'time : '
    POSITION = 'position : '
    INDEX = 'playlistindex : '
    int_regex = re.compile(r'.*(\d+).*')

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _write(self, string):
        command = str('%s\n' % string)
        return self.telnet.write(command)

    def connect(self, password='admin'):
        self.telnet = telnetlib.Telnet(host=self.host, port=self.port)
        if password:
            self.telnet.read_until(self.PASSWORD_STRING)
            self._write(password)
            match = self.telnet.expect([self.WELCOME_STRING,
                                        self.WRONG_PASSWORD])
            if match[0] == 1:
                raise InvalidPasswordException
        self.name = self.add_broadcast()

    def close(self):
        self.telnet.close()

    def add_broadcast(self, name='bcast'):
        self._write('new %s broadcast enabled' % name)
        return name

    def add_input(self, path):
        self._write('setup %s input %s' % (self.name, path))
        if not self._playing():
            self._write('control %s play' % self.name)

    def _playing(self):
        self._write('show %s' % self.name)
        data = self.telnet.read_until(self.PLAYING, 1)
        return self.PLAYING in data

    def remove_input(self, path):
        self._write('setup %s inputdel %s' % (self.name, path))

    def now_playing(self):
        """
        Returns the file URL and current position (0..1).
        """
        url = None
        time_percentage = None

        self._write('show %s' % self.name)
        self.telnet.read_until(self.INPUTS, 1)
        try:
            playlist = [l.strip() for l in self.telnet.read_until(self.OUTPUT, 1).splitlines() if l.strip()][0:-1]
            if ' : ' in playlist[0]:
                playlist = [l.partition(' : ')[2] for l in playlist]
        except IndexError:
            pass
        else:
            if self.PLAYING in self.telnet.read_until(self.PLAYING, 1):
                data = [l.strip() for l in self.telnet.read_until(self.TIME, 1).splitlines()]
                line = [l for l in data if l.startswith(self.POSITION)][0]
                name, _, value = [v.strip() for v in line.partition(':')]
                time_percentage = float(value)
                self.telnet.read_until(self.INDEX, 1)
                data = self.telnet.read_some()
                try:
                    playlist_index = int(self.int_regex.match(data).groups()[0])
                    url = playlist[playlist_index - 1]
                except (ValueError, IndexError):
                    pass
        return url, time_percentage

