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

accessable_proxies = set()
failed_proxies = set()

@route('/run-morestep3')
def run_morestep3():
    session_cookie = str(request.query.session_cookie)
    valid_code = str(request.query.valid_code)
    candidates = request.query.candidates.split(',')
    new_proxies = request.query.proxies.split(',')
    vote_num = 100 #request.query.vote_num or 10
    #deal new_proxies
    for p in new_proxies:
        if p != '':
            p = str(p.strip())
            if ':' not in p:
                p += ':80'
            accessable_proxies.add(p)
    #candidates = [c.encode('utf-8') for c in candidates]
    response.content_type = 'text/plain; charset=utf-8'
    def g(vote_num):
        global failed_proxies, accessable_proxies
        def check_result(result):
            if result == (10, 500):
                return True, '500 Server Error'
            if result[0] == 2:
                return True, 'invalid valid_code'
            if result[0] == 3:
                return True, 'session expired'
            if result[0] == 1:
                return True, 'vote later'
            return result[0] == 0, str(result)

        yield u'总共 '+ unicode(len(accessable_proxies)+ len(failed_proxies)) + u' 个代理地址\n'
        new_failed_proxies = set()
        not_continue = False
        for proxy in accessable_proxies:
            ua = mk.randomua()
            result = mk.step3(session_cookie, valid_code, candidates, ua, proxy)
            r, info = check_result(result)
            yield info + '\n'
            if r and result[0] in (2, 3, 10):
                not_continue = True
                break
            if not r:
                new_failed_proxies.add(proxy)
            if result[0] == 0:
                vote_num -= 1
        accessable_proxies -= new_failed_proxies
        if not not_continue:
            for proxy in failed_proxies:
                ua = mk.randomua()
                result = mk.step3(session_cookie, valid_code, candidates, ua, proxy)
                r, info = check_result(result)
                yield info + '\n'
                if r:
                    accessable_proxies.add(proxy)
                if result[0] == 0:
                    vote_num -= 1
        failed_proxies = new_failed_proxies
    return g(vote_num)

@route('/pic.bmp')
def pic_bmp():
    return bottle.static_file('pic.bmp', root='./')

@route('/print-proxies')
def print_proxies():
    print 'accessable proxies:'
    print accessable_proxies
    print '\nfailed_proxies:'
    print failed_proxies

if __name__ == '__main__':
    mk.init()
    accessable_proxies = set(mk.proxies)
    mk.use_random_candidate = False
    bottle.run(port=8082, host='0.0.0.0')

