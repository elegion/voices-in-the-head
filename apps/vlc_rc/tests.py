import unittest

import rc


class FactoryTestCase(unittest.TestCase):
    def test_telnet(self):
        iface = rc.VlcRC().get(rc.INTERFACE_TELNET)
        from interfaces.telnet import Interface
        self.assertEquals(Interface, iface)

    def test_invalid(self):
        self.assertRaises(rc.interfaces.InvalidInterfaceException,
                          rc.VlcRC().get, 'telephaty')


if __name__ == '__main__':
    unittest.main()
