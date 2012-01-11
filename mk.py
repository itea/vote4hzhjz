#!/usr/bin/python
import pycurl, re, random, sys, urllib
import cStringIO as StringIO

httpHeader1 = ["Accetp: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Charset:GBK,utf-8;q=0.7,*;q=0.3",
        "Accept-Encoding:gzip,deflate",
        "Accept-Language:zh-CN;q=0.8,zh;q=0.6,en-US;q=0.4",
        "Cache-Control:max-age=0",
        "Origin:http://www.hzhjz.com",
        "Connection:keep-alive" ]
useragent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
session_cookie = None
valid_code = None
proxy = None # proxy address
nostep3 = False # skip step3
morestep3 = False # more step3 (repeat)
globalproxy = False #
use_random_candidate = True # 
use_random_proxy = True # 
output_proxy = False
vote_count = 999999 # 
candidates = []
ualist = []
proxies = set()

def load_ua(): # load user agents from ua.txt
    global ualist
    with open('ua.txt', 'r') as fua:
        for line in fua:
            if len(line) > 1 and line[0] != '#':
                ualist.append(line.strip())
    print 'load_ua> '+ str(len(ualist)) +' userAgent loaded'

def load_proxy(): # load proxy address from proxy.txt
    global proxies
    with open('proxy.txt', 'r') as f:
        for line in f:
            if len(line) > 1 and line[0] != '#':
                s = line.strip()
                if ':' not in s:
                    s += ':80'
                proxies.add(s)
    print 'load_proxy> '+ str(len(proxies)) +' proxy loaded'

def load_candidate(): # load candidate from candidate.txt
    global candidates
    with open('candidates.txt', 'rb') as f:
        for line in f:
            if len(line) > 1 and line[0] != '#':
                candidates.append(line.strip())
    print 'load_candidate> '+ str(len(candidates)) +' candidate loaded'

def randomua():
    return ualist[int(random.random() * len(ualist))]

def step1(): # step 1, get session id
    print '\nBEGIN STEP1'
    scookie = []
    curl = pycurl.Curl()
    curl.setopt(curl.URL, 'http://www.hzhjz.com/webvoteAction1.asp')
    curl.setopt(curl.USERAGENT, useragent)
    curl.setopt(curl.HTTPHEADER, httpHeader1)
    curl.setopt(curl.NOBODY, 1) # head only
    def get_cookie(buf):
        if buf[0:5] == 'HTTP/':
            print '| '+ buf.strip()
        prog = re.compile('(ASPSESSIONID\w+)=(\w+);', re.M)
        m = prog.search(str(buf))
        if m:
            scookie.append(m.group(1) +'='+ m.group(2))
    curl.setopt(curl.HEADERFUNCTION, get_cookie)
    def noop(*args): pass
    curl.setopt(curl.WRITEFUNCTION, noop)
    if globalproxy and proxy is not None:
        curl.setopt(curl.PROXY, proxy)
    curl.perform()
    curl.close()
    return scookie[0] if len(scookie) > 0 else None

def step2(session_cookie=None): # step 2, get validCode
    print '\nBEGIN STEP2'
    if session_cookie is None:
        print 'session_cookie is None'
        exit(1)
    curl = pycurl.Curl()
    curl.setopt(curl.URL, 'http://www.hzhjz.com/inc/GetCodeComtz.asp?t=0.'+ str(int(random.random() * 10000000000000000)))
    curl.setopt(curl.USERAGENT, useragent)
    curl.setopt(curl.HTTPHEADER, httpHeader1)
    curl.setopt(curl.COOKIE, session_cookie)
    curl.setopt(curl.REFERER, 'http://www.hzhjz.com/webvoteAction1.asp')
    f = open('pic.bmp', 'w+b')
    def printhead(buf):
        if buf[0:5] == 'HTTP/':
            print '| '+ buf.strip()
    curl.setopt(curl.HEADERFUNCTION, printhead)
    curl.setopt(curl.WRITEFUNCTION, f.write)
    if globalproxy and proxy is not None:
        curl.setopt(curl.PROXY, proxy)
    curl.perform()
    curl.close()
    f.close()
    if __name__ == '__main__':
        return raw_input('valid code:')
    else:
        return

def gen_postfields(valid_code, candidates, use_random=False):
    ls = ['ValidCode='+ valid_code]
    for e in candidates:
        if not use_random or (random.random() > 0.4):
            if type(e) == str:
                e = unicode(e, 'utf-8').encode('gbk')
            elif type(e) == unicode:
                e = e.encode('gbk')
            ls.append('xs_id='+ urllib.quote(e))
            if len(ls) >= 5: break
    return '&'.join(ls)

def step3(session_cookie, valid_code, candidates, useragent, proxy=None): # step 3, vote
    print '\nBEGIN STEP3'
    print 'using agent: '+ useragent
    curl = pycurl.Curl()
    curl.setopt(curl.URL, 'http://www.hzhjz.com/Vote_doIP.asp')
    curl.setopt(curl.POST, 1)
    curl.setopt(curl.USERAGENT, useragent)
    curl.setopt(curl.HTTPHEADER, httpHeader1)
    curl.setopt(curl.COOKIE, session_cookie)
    curl.setopt(curl.REFERER, 'http://www.hzhjz.com/webvoteAction1.asp')
    curl.setopt(curl.POSTFIELDS, gen_postfields(valid_code, candidates, use_random_candidate))
    curl.setopt(curl.TIMEOUT, 40) # 40 seconds
    content = StringIO.StringIO()
    def printhead(buf):
        print '| '+ buf.strip()
        #if re.search('^HTTP/1\.[01]\S+(\d{3})', buf):
        #    result.append(re.search('HTTP/1\.[01]\S+(\d{3})', buf).group(1))
    def lastout(buf):
        content.write(buf)
    curl.setopt(curl.HEADERFUNCTION, printhead)
    curl.setopt(curl.WRITEFUNCTION, lastout)
    if proxy is not None:
        curl.setopt(curl.PROXY, proxy)
        print 'using proxy: '+ proxy
    try:
        curl.perform()
        state_code = curl.getinfo(curl.RESPONSE_CODE)
        buf = unicode(content.getvalue(), 'gbk').encode('utf8')
        if state_code == 200:
            m = re.search('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', buf)
            if m and re.search('images/success\.gif', buf):
                result = (0, m.group(0))
                print 'DONE: '+ result[1]
            elif re.search('\xe8\xaf\xb7\xe7\xa8\x8d\xe5\x90\x8e\xe5\x86\x8d\xe6\x9d\xa5\xe6\x8a\x95\xe7\xa5\xa8', buf): # 'please vote later
                result = (1, None)
                print 'FAILED: \xe8\xaf\xb7\xe7\xa8\x8d\xe5\x90\x8e\xe5\x86\x8d\xe6\x9d\xa5\xe6\x8a\x95\xe7\xa5\xa8'
            elif re.search('\xe9\xaa\x8c\xe8\xaf\x81\xe7\xa0\x81\xe9\x94\x99\xe8\xaf\xaf', buf): # valid_code incorrect
                result = (2, None)
                print 'FAILED: \xe9\xaa\x8c\xe8\xaf\x81\xe7\xa0\x81\xe9\x94\x99\xe8\xaf\xaf'
            elif re.search('\xe4\xbd\xa0\xe6\x8f\x90\xe4\xba\xa4\xe7\x9a\x84\xe8\xb7\xaf\xe5\xbe\x84\xe6\x9c\x89\xe8\xaf\xaf', buf): # session expired
                result = (3, None)
            else:
                result = (9, buf)
                print 'FAILED: '+ buf
        elif state_code == 503:
            result = (10, 503)
        else:
            print 'FAILED, proxy: '+ str(proxy) +', state: '+ str(state_code)
            print buf
            content.close()
            result = (10, state_code)
        return result
    except KeyboardInterrupt:
        raise
    except:
        info = sys.exc_info()
        print "FAILED: ", info
        return (20, str(info))
    finally:
        curl.close()

def more_step3(proxies, use_random=False):
    global useragent
    i = 1
    out = None
    if output_proxy:
        out = open('proxy.out', 'w+')
    for addr in proxies:
        if i > vote_count: break
        if not use_random or (random.random() > 0.46):
            useragent = randomua()
            code, info = step3(session_cookie, valid_code, candidates, useragent, addr)
            if code == 0 and output_proxy:
                out.write(addr)
                out.write('\n')
                out.flush()
            i += 1
    if out is not None:
        out.close()

#######
def parse_arg(arg):
    global proxy, valid_code, session_cookie, globalproxy, nostep3, morestep3, use_random_proxy, use_random_candidate, vote_count, output_proxy
    if re.search('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', arg):
        proxy = arg
        if ':' not in proxy:
            proxy += ':80'
    elif re.search('\d{4}', arg):
        valid_code = arg
    elif arg == 'globalproxy':
        globalproxy = True
    elif arg == 'nostep3':
        nostep3 = True
    elif arg == 'morestep3':
        morestep3 = True
    elif arg == 'not_random_candidate':
        use_random_candidate = False
    elif arg == 'output_proxy':
        output_proxy = True
    elif arg == 'not_random_proxy':
        use_random_proxy = False
    elif re.search('vote_count:(\d+)', arg):
        m = re.search('vote_count:(\d+)', arg)
        vote_count = int(m.group(1))
        morestep3 = True
    elif re.search('ASPSESSIONID', arg):
        session_cookie = arg

for i in range(1, len(sys.argv)):
    parse_arg(sys.argv[i])

print '=========== BEGIN ==========='
print 'proxy: '+ str(proxy)
print 'session_cookie: '+ str(session_cookie)
print 'valid_code: '+ str(valid_code)
#print 'vote_count: '+ vote_count

def init():
    load_ua()
    load_proxy()
    load_candidate()

if __name__ == '__main__':
    init()

    useragent = randomua()
    print 'useragent: '+ useragent

    if session_cookie is None:
        session_cookie = step1()
        print 'session_cookie: '+ str(session_cookie)
    
    if valid_code is None:
        valid_code = step2(session_cookie)
        print 'valid_code: '+ str(valid_code)
    
    if morestep3:
        more_step3(proxies, use_random_proxy)
    elif not nostep3:
        step3(session_cookie, valid_code, candidates, useragent, proxy)

