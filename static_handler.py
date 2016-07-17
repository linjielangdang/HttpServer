#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import shutil
import mimetypes
import urlparse
import urllib
from exception_handler import *
from template import *
from util import *

# implementation of handlers, each handler class should implement a handle_request(serv) method
# For now, static handler only accept GET requests
class StaticHandler(object):
    def __init__(self, virtual_path, static_dir):
        self.virtual_path = virtual_path
        self.static_dir = static_dir
        if not os.path.exists(static_dir) or not os.path.isdir(static_dir):
            raise StaticDirNotValid

    def handle_request(self, serv):
        if serv.verb.lower() != "get":
            serv.send_error_response(400, "Unsupported HTTP Method")
        # get the file system real path for the file/dir
        parsed = urlparse.urlparse(serv.path)
        relative_path = parsed.path[len(self.virtual_path):]
        unquoted_path = urllib.unquote(relative_path)
        real_path = self.static_dir + unquoted_path.decode(sys.getfilesystemencoding())

        if not os.path.exists(real_path):
            serv.send_error_response(404, "File/directory not found.")
            return
        # handle differently for dir and file
        if os.path.isdir(real_path):
            # get the file listing
            listing = os.listdir(real_path)
            if not relative_path.endswith("/"):
                relative_path = relative_path + "/"

                # first try index.html if exists
            index_files = ["index.html", "index.htm"]
            for index in index_files:
                if index in listing:
                    serv.send_response_line(302, "Redirected")
                    index_path = os.path.join(self.virtual_path + relative_path, index)
                    serv.send_header("Location", index_path)
                    serv.end_headers()
                    return

            # index.html not present, generate the listing html
            # Send the response line and headers
            serv.send_response_line(200, "OK")
            serv.send_header("Content-Type", "text/html;charset=%s" % sys.getfilesystemencoding())
            serv.send_header("Connection", "close")
            # Construct HTML
            listing_str = ""
            if relative_path != "/":
                # if not root, add parent directory link
                parent_path = "/".join(relative_path.split("/")[:-2])
                href = self.virtual_path + parent_path
                line = u"<a href='%s'>..</a><br>" % href
                listing_str += line
            # construct the file list
            for item in listing:
                if isinstance(item, unicode):
                    # decode to unicode
                    stritem = item.encode(sys.getfilesystemencoding())
                    unicodeitem = item
                else:
                    stritem = item
                    unicodeitem = item.decode(sys.getfilesystemencoding())
                # urllib.quote must be given str, not unicode
                quoted_item = urllib.quote(stritem)
                # construct url with quoted file name
                href = os.path.join(self.virtual_path + relative_path, quoted_item)
                snippet = u"<a href='%s'>%s</a><br>" % (href, unicodeitem)
                listing_str += snippet

            display_path = self.virtual_path + relative_path
            listing_html = listing_tpl % (display_path, display_path, listing_str)
            listing_html = listing_html.encode(sys.getfilesystemencoding())
            serv.send_header("Content-Length", len(listing_html))
            serv.end_headers()
            serv.wfile.write(listing_html)
        else:
            try:
                f = open(real_path, "rb")
            except:
                serv.send_error_response(404, "File not found")
                return
            serv.send_response_line(200, "OK")
            _, ext = os.path.splitext(real_path)
            # ignore case of extension
            ext = ext.lower()
            # make a guess based on mimetypes
            content_type = mimetypes.types_map.get(ext, '')
            if not content_type:
                # default to text/html
                content_type = "text/html"
            serv.send_header("Content-Type", content_type)
            # content-length and last-modified
            stat = os.fstat(f.fileno())
            serv.send_header("Content-Length", str(stat.st_size))
            serv.send_header("Last-Modified", timestamp_to_string(stat.st_mtime))
            serv.send_header("Connection", "close")
            serv.end_headers()
            # now copy the file over
            shutil.copyfileobj(f, serv.wfile)