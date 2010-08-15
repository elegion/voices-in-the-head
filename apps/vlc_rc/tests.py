import unittest

import rc
import interfaces.telnet


class FactoryTestCase(unittest.TestCase):
    def test_telnet(self):
        iface = rc.VlcRC().get(rc.INTERFACE_TELNET)
        from interfaces.telnet import Interface
        self.assertEquals(Interface, iface)

    def test_invalid(self):
        self.assertRaises(rc.interfaces.InvalidInterfaceException,
                          rc.VlcRC().get, 'telephaty')


class TelnetTestCase(unittest.TestCase):
    class MyTelnet(object):
        def __init__(self, *args, **kwargs):
            self.open = True
            self.logged_in = False
            self.password = 'peace'
            self.buffer = 'Password:'

        def close(self):
            self.open = False

        def write(self, string):
            string = string.strip()
            if not self.logged_in:
                data = self.authenticate(string)
            else:
                data = self.execute(string)
            self.buffer += data

        def read_until(self, string, *args, **kwargs):
            pos = self.buffer.index(string)
            read = self.buffer[0:pos + len(string)]
            self.buffer = self.buffer[pos + len(string):]
            return read

        def expect(self, expects, *args, **kwargs):
            string = None
            for string in expects:
                try:
                    string = self.read_until(string)
                except ValueError:
                    pass
                else:
                    break
            if string:
                return (expects.index(string), string, string)
            raise ValueError

        def read_some(self, *args, **kwargs):
            read = self.buffer
            self.buffer = ''
            return read

        def authenticate(self, password):
            if password == self.password:
                self.logged_in = True
                return interfaces.telnet.Interface.WELCOME_STRING
            else:
                return interfaces.telnet.Interface.WRONG_PASSWORD

        def execute(self, string):
            return ''

    def setUp(self):
        interfaces.telnet.telnetlib.Telnet = self.MyTelnet
        self.iface = interfaces.telnet.Interface(None, None)

    def test_connect_wrong_passwd(self):
        self.assertRaises(interfaces.telnet.InvalidPasswordException,
                          self.iface.connect, 'emotion')

    def test_connect_successful(self):
        self.iface.connect(password='peace')


if __name__ == '__main__':
    unittest.main()
