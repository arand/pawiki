#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#from flask import Flask, Markup, escape
from flask import Flask, Markup
from flask import redirect, url_for, request
from flask import session, g, render_template

from pymongo import Connection
# from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId

import markdown

from mcsession import McSessionInterface


app = Flask(__name__)
app.secret_key = '6st3grahy2du'
app.session_interface = McSessionInterface()
app.debug = True
db = Connection().pawiki


@app.before_request
def before_request():
    g.mongo = Connection().pawiki


@app.route('/')
def index():
    return redirect(url_for('view_page', pagename='FrontPage'))


@app.route('/all/')
def all_pages():
    pages = []
    cursor = g.mongo.pawiki.find({ }, {'name': 1}).sort('_id', 1)
    for i in xrange(cursor.count()):
        pages.append(cursor.next()['name'])
    return render_template('list.html', pages=pages)


@app.route('/<pagename>')
def view_page(pagename):
    g.mongo.pawiki.ensure_index('name', unique=True)
    page = g.mongo.pawiki.find_one({'name': pagename})
    if not page:
        return redirect(url_for('edit_page', pagename=pagename))
    session['last'] = pagename
    return render_template('view.html', page=page)


@app.route('/<pagename>/edit', methods=['GET', 'POST'])
def edit_page(pagename):
    g.mongo.pawiki.ensure_index('name', unique=True)
    page = {}
    sahtml = []
    if request.method == 'POST':
        pageid = g.mongo.pawiki.find_one({'name': pagename}, {'_id': 1})
        page['name'] = pagename
        for k in request.form.keys():
            if k == 'salvesta':
                continue
            if k == 'data':
                page['htmldata'] = Markup(markdown.markdown(request.form[k], safe_mode='escape'))
                page[k] = request.form[k]
                continue
            page[k] = request.form[k]
        if page['seealso']:
            for a in page['seealso'].split(' '):
                url = url_for('view_page', pagename=a)
                sahtml.append('<a href="%s">%s</a>' % (url, a))
        page['sahtml'] = sahtml
        if pageid:
            page['_id'] = ObjectId(pageid['_id'])
            g.mongo.pawiki.save(page)
        else:
            g.mongo.pawiki.insert(page)
        return redirect(url_for('view_page', pagename=page['name']))
    page = g.mongo.pawiki.find_one({'name': pagename})
    if not page:
        page = {}
        page['title'] = 'Lehe pealkiri'
        page['subtitle'] = 'Lehe alapeakiri'
        page['sitesub'] = ''
        page['data'] = 'Muuda seda'
        page['name'] = pagename
        page['seealso'] = 'Seotud lehtede nimed'
    session['last'] = pagename
    return render_template('edit.html', page=page)


@app.route('/search', methods=['GET', 'POST'])
def search_page():
    #return render_template('search.html', data=request.form)
    return redirect(url_for('view_page', pagename='FrontPage'))


if __name__ == '__main__':
    app.run('0.0.0.0')
