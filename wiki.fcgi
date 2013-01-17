#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flup.server.fcgi import WSGIServer
from main import app
#from werkzeug.contrib.fixers import LighttpdCGIRootFix as fix

if __name__ == '__main__':
    WSGIServer(app).run()
