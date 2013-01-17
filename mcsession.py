#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import pickle
from datetime import timedelta
from uuid import uuid4
from memcache import Client
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin


class McSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class McSessionInterface(SessionInterface):
    serializer = pickle
    session_class = McSession

    def __init__(self, mc=None, prefix="session:"):
        if mc is None:
            mc = Client(['127.0.0.1:11211'], debug=0)
        self.mc = mc
        self.prefix = prefix

    def generate_sid(self):
        return str(uuid4())

    def get_mc_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def _get_mc_key(self, sid):
        key = self.prefix + sid
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return key

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid)
        val = self.mc.get(self._get_mc_key(sid))
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            self.mc.delete(self._get_mc_key(session.sid))
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        mc_exp = self.get_mc_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        self.mc.set(self._get_mc_key(session.sid), val, int(mc_exp.total_seconds()))
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)
