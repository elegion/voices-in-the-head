class Interface(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def add_broadcast(self, name):
        raise NotImplementedError

    def add_input(self, path):
        raise NotImplementedError

    def remove_input(self, path):
        raise NotImplementedError
