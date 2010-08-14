import unittest

import vlc_rc


class FactoryTestCase(unittest.TestCase):
    def test_invalid(self):
        self.assertRaises(vlc_rc.interfaces.InvalidInterfaceException,
                          vlc_rc.VlcRC().get, 'telephaty')


if __name__ == '__main__':
    unittest.main()
