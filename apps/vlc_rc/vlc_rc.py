import interfaces


INTERFACE_TELNET = 'telnet'


class VlcRC(object):
    def get(self, interface_name):
        try:
            interface = interfaces.get_by_name(interface_name)
        except interfaces.InvalidInterfaceException:
            raise
        return interface
