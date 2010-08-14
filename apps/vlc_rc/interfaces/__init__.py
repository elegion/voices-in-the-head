class InvalidInterfaceException(Exception):
    pass


def get_by_name(name):
    module_name = '%s.%s' % ('interfaces', name)
    try:
        module = __import__(module_name)
    except ImportError:
        raise InvalidInterfaceException
    try:
        return getattr(module, name).Interface
    except AttributeError:
        raise InvalidInterfaceException
