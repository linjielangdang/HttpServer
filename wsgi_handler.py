#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import imp
import urlparse
from exception_handler import *
from log import *

class WSGIHandler(object):
    def __init__(self, virtual_path, app_path):
        self.virtual_path = virtual_path
        self.load_application(app_path)

    def load_application(self, app_path):
        if not os.path.exists(app_path):
            raise WSGIFileNotFound()
        path, filename = os.path.split(app_path)
        modulename, ext = os.path.splitext(filename)
        # Add the path to sys.path
        sys.path.append(path)
        try:
            if ext.lower() == ".py" or ext.lower() == ".wsgi":
                m = imp.load_source(modulename, app_path)
            else:
                m = imp.load_compiled(modulename, app_path)
        except Exception as e:
            add_error_log(str(e))
            raise WSGIInvalid()
        else:
            if not hasattr(m, "application"):
                add_error_log("Wsgi application not found")
                raise WSGIInvalid()
            self.app = m.application
            if not callable(self.app):
                add_error_log("Wsgi application not callable")
                raise WSGIInvalid()

    def get_headers_environ(self, serv):
        headers_environ = {}
        for key in serv.headers:
            val = serv.headers[key]
            if "-" in key:
                key = key.replace("-", "_")
            key = "HTTP_" + key.upper()
            if key not in headers_environ:
                headers_environ[key] = val
            else:
                headers_environ[key] += "," + val
        return headers_environ

    def prepare_environ(self, serv):
        parsed = urlparse.urlparse(serv.path)
        real_path = parsed.path[len(self.virtual_path):]
        if not real_path.startswith("/"):
            real_path = "/" + real_path
        environ = {
            "REQUEST_METHOD": serv.verb,
            "SCRIPT_NAME": self.virtual_path,
            "PATH_INFO": real_path,
            "QUERY_STRING": parsed.query,
            "CONTENT_TYPE": serv.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": serv.headers.get("Content-Length", ""),
            "SERVER_NAME": self.server.server_name,
            "SERVER_PORT": self.server.server_port,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.input": serv.rfile,
            "wsgi.errors": serv.error,
            "wsgi.version": (1, 0),
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "wsgi.multithread": self.server._mode == "thread",
            "wsgi.multiprocess": self.server._mode == "process",
        }
        environ.update(self.get_headers_environ(serv))
        return environ

    def handle_request(self, serv):
        # environ
        environ = self.prepare_environ(serv)

        # start_response
        def start_response(status, response_headers):
            serv.send_status_line(status)
            for k, v in response_headers:
                serv.send_header(k, v)
            serv.end_headers()

        # Get response lines
        try:
            response_chucks = self.app(environ, start_response)
        except Exception as e:
            add_error_log("* ERROR IN WSGI APP *" + str(e))
            raise e
        else:
            for chuck in response_chucks:
                serv.wfile.write(chuck)