# -*- coding: UTF-8 -*-
from django.core.files.storage import FileSystemStorage
from core.utils import Transliterator


class TransliteratedStorage(FileSystemStorage):
    def get_valid_name(self, name):
        str = Transliterator().process(name)
        str = super(TransliteratedStorage, self).get_valid_name(str)
        return str