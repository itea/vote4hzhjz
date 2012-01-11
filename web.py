#!/usr/bin/python
# -*- coding: utf-8 -*-

import bottle, mk
from bottle import route, template, request, response

bottle.TEMPLATE_PATH.append('./')
@route('/')
def index():
    return template('index.html')

@route('/list-candidates')
def list_candidate():
    return {'candidates': list(mk.candidates)}

@route('/list-proxies')
def list_proxies():
    return {'proxies': list(mk.proxies)}

@route('/run-step1')
def run_step1():
    return {'session_cookie': mk.step1()}

@route('/run-step2', method='POST')
def run_step2():
    print request.forms.session_cookie
    mk.step2(str(request.forms.session_cookie))
    return {}

@route('/run-step1n2')
def run_step1n2():
    result = {'session_cookie': mk.step1()}
    mk.step2(result['session_cookie'])
    return result

@route('/run-morestep3')
def run_morestep3():
    session_cookie = str(request.query.session_cookie)
    valid_code = str(request.query.valid_code)
    candidates = request.query.candidates.split(',')
    #candidates = [c.encode('utf-8') for c in candidates]
    response.content_type = 'text/plain; charset=utf-8'
    def g():
        yield u'总共 '+ unicode(len(mk.proxies)) + u' 个代理地址\n'
        for proxy in mk.proxies:
            ua = mk.randomua()
            result = mk.step3(session_cookie, valid_code, candidates, ua, proxy)
            yield str(result) + '\n'
            if result == (10, 500):
                break
    return g()

@route('/pic.bmp')
def pic_bmp():
    return bottle.static_file('pic.bmp', root='./')

if __name__ == '__main__':
    mk.init()
    mk.use_random_candidate = False
    bottle.run(port=8082)

