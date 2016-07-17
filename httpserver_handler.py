#!/usr/bin/env python
# -*- coding:utf-8 -*-

import SocketServer
import mimetools
from log import *
from mux import Mux
from template import *
try:
    import cStringIO as StringIO
except:
    import StringIO


# This is the handler entry point, dispatching requests to different handlers with the help of mux
class HTTPServerHandler(SocketServer.StreamRequestHandler):
    def __init__(self, request, client_addr, server):
        self.error = StringIO.StringIO()
        SocketServer.StreamRequestHandler.__init__(self, request, client_addr, server)

    # Should read the request from self.rfile
    # and write the response to self.wfile
    def handle_one_request(self):
        try:
            # read the first line from request
            request_line = self.rfile.readline()
            words = request_line.strip().split()
            if len(words) != 3:
                self.send_error_response(400, "Invalid HTTP request")
                return
            self.verb, self.path, _ = words
            add_access_log(self.verb + " " + self.path)
            # read the header lines
            self.headers = mimetools.Message(self.rfile, 0)
            connection_type = self.headers.get("Connection", "")
            if connection_type == "close":
                self.close_connection = True
            elif connection_type == "keep-alive":
                self.close_connection = False

            # delegate body handling to mux
            handler = Mux().get_handler(self.path)
            if not handler:
                self.send_error_response(404, "File Not Found")
                return
            handler.handle_request(self)
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()

            # If the request handler write some error messages, record them in log
            if self.error.tell():
                self.error.seek(0)
                add_error_log(self.error.read())
        except Exception, e:
            add_error_log(str(e))
            self.close_connection = True

    def handle(self):
        self.close_connection = True
        self.handle_one_request()
        # supporting keep-alive
        while not self.close_connection:
            self.handle_one_request()

    def send_response_line(self, code, explanation):
        self.send_status_line("%d %s" % (code, explanation))

    def send_status_line(self, status):
        response_line = "HTTP/1.1 %s\r\n" % status
        self.wfile.write(response_line)
        self.send_header("Server", "Neo's HTTP Server")

    def send_header(self, name, value):
        self.wfile.write("%s: %s\r\n" % (name, value))
        if name.lower() == "connection":
            if value.lower() == "close":
                self.close_connection = True
            elif value.lower() == "keep-alive":
                self.close_connection = False

    def end_headers(self):
        self.wfile.write("\r\n")

    def send_error_response(self, code, explanation):
        self.send_response_line(code, explanation)
        self.send_header("Content-type", "text/html")
        self.send_header("Connection", "close")
        self.end_headers()
        message_body = error_tpl % (code, code, explanation)
        self.wfile.write(message_body)
        if not self.wfile.closed:
            self.wfile.flush()