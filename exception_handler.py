#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Exceptions
class WSGIFileNotFound(Exception):
    "Raised when wsgi file is not found in file system"
class WSGIInvalid(Exception):
    "Raised when wsgi file is not a valid python module, or application doesn't exist"
class StaticDirNotValid(Exception):
    "Raised when static dir is not found or is not a directory"
class DuplicatePath(Exception):
    "Raised when defining duplicate path in configuration file"