import telnetlib

import base


class InvalidPasswordException(Exception):
    pass


class Interface(base.Interface):
    PASSWORD_STRING = 'Password:'
    WELCOME_STRING = 'Welcome, Master'
    WRONG_PASSWORD = 'Wrong password.'
    PLAYING = 'state : playing'

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
