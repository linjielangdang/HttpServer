#!/usr/bin/env python
# -*- coding:utf-8 -*-

import SocketServer, socket
import json
import static_handler
from httpserver_handler import HTTPServerHandler
from proxy_handler import ProxyHandler
from wsgi_handler import WSGIHandler
from mux import Mux
from log import *
from exception_handler import *

# the main server
class WebServer(object):
    # configuration is a json file
    def _read_config(self):
        try:
            f = open("config.json", 'r')
        except:
            add_error_log("Fail to read config file, exiting now ...")
            raise SystemExit()
        try:
            config = json.load(f)
        except ValueError:
            add_error_log("Fail to parse config file, exiting now...")
            raise SystemExit()
        try:
            self._address = config['server']['ip']
            self._port = config['server']["port"]
            self._mode = config['server']['mode']
        except KeyError:
            add_error_log("Missing server basic configuration, using defaults...")
        self._routes = config['routes']

    def __init__(self):
        # defaults
        self._address = "127.0.0.1"
        self._port = 80
        self._mode = "thread"
        # load from config
        self._read_config()
        # initialize the mux
        for path in self._routes:
            d = self._routes[path]
            if d['type'] == "static":
                try:
                    handler = static_handler(path, d['dir'])
                except StaticDirNotValid:
                    add_error_log("Static directory in config file not valid, exiting...")
                    raise SystemExit()
            elif d['type'] == "wsgi":
                try:
                    handler = WSGIHandler(path, d['application'])
                except WSGIInvalid, WSGIFileNotFound:
                    handler = None
                    add_error_log("WSGI file invalid, ignoring path %s"%path)
            elif d['type'] =="proxy":
                handler = ProxyHandler(path, d['proxyurl'])
            else:
                add_error_log("Unsupported path definition: %s"%path)
            # link the handler and self
            handler.server = self
            try:
                Mux().register_handler(path, handler)
            except DuplicatePath:
                add_error_log("Config file contains duplicate path definition, exiting...")
                raise SystemExit()

    def start(self):
        address = (self._address, self._port)
        if self._mode == "thread":
            server = SocketServer.ThreadingTCPServer(address, HTTPServerHandler)
        else:
            server = SocketServer.ForkingTCPServer(address, HTTPServerHandler)
        host, port = server.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        server.serve_forever()


# The driver
def main():
    server = WebServer()
    server.start()

if __name__ == "__main__":
    main()
