#!/usr/bin/env python
# -*- coding:utf-8 -*-


# templates
error_tpl = u"""
    <html>
        <head>
            <title>Error %d</title>
        </head>
        <body>
            <h1>%d</h1><hr>
            <h2>%s</h2>
        </body>
    </html>
"""

listing_tpl = u"""
    <html>
        <head>
            <title>%s</title>
        </head>
        <body>
            <h1>%s</h1><hr>
            %s
        </body>
    </html>
"""