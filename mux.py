#!/usr/bin/env python
# -*- coding:utf-8 -*-

from exception_handler import *


# A mux to route HTTP path to correct handler
class Mux(object):
    def __init__(self):
        self.dict = {}
        self.sortedkeys = []

    def register_handler(self, path, handler):
        # register a virutal path to a handler
        if path in self.dict:
            raise DuplicatePath()
        self.dict[path] = handler
        idx = -1
        for i, key in enumerate(self.sortedkeys):
            if path.startswith(key):
                idx = i
                break
        if idx < 0:
            self.sortedkeys.append(path)
        else:
            self.sortedkeys.insert(idx, path)

    def get_handler(self, path):
        for key in self.sortedkeys:
            if path.startswith(key):
                return self.dict[key]
        return None
