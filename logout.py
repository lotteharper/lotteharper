import re, traceback, requests, json, regex, sys, glob, time, threading, datetime, asyncio, random
from subprocess import Popen, STDOUT, PIPE

def run_command(command):
    cmd = command.split(' ')
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=str("/"))
    time.sleep(0.05)
    proc.kill()
    return proc.stdout.read().decode("unicode_escape")

import random
code = run_command('sudo tail --lines 1 /etc/banner')
new_code = random.randrange(111111, 999999)
run_command("./home/team/lotteh/set_code.sh {}".format(str(new_code)))

with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)

output = ''

def unique(thelist):
    u = []
    for i in thelist:
        if i not in u: u.append(i)
    return u

def check_blacklist(ip):
    try:
        with open('blacklist.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.replace('\n', '') == ip: return True
        return False
    except: pass
    return False

def blacklist(ip):
    with open('blacklist.txt', 'a') as file:
        file.write('{}\n'.format(ip))
        file.close()

logpath = glob.glob('/var/log/auth.log')[-1]

def load_path1():
    global output
#    print(output)

def load_path2():
    global output
    try:
        if glob.glob('/var/log/auth.log.*')[-1]:
            run_command('sudo rm {}*'.format(logpath))
    except:
        run_command('sudo rm {}*'.format(logpath))
    sys.exit(1)
    logpath = glob.glob('/var/log/auth.log.*')[-1]
    output = run_command('tail -n 5000 {}'.format(logpath))

thread_started = False

ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
ipv6_pattern = r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"

output = run_command('sudo tail -n 500 {}'.format(logpath))
#time.sleep(1)
op = output.split('\n')
op.reverse()
output = '\n'.join(op)
ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))

thread_started = False
while not output:
    print('awaiting output')
    time.sleep(3)
    if output:
        op = output.split('\n')
        op.reverse()
        output = '\n'.join(op)
        ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))
        if len(ips) == 0 and thread_started: sys.exit(2)
    if not thread_started:
        thread_started = True
        load_path2()
        break

if len(ips) == 0:
    sys.exit(2)

ip = ips[0]

def thread_function(ip_address, code):
    global ip
    TIMEOUT_SECONDS = 60 * 5
    t = 0
    login = ShellLogin.objects.create(ip_address=ip_address, code=code)
    while True:
        try:
            login = ShellLogin.objects.get(id=login.id)
        except:
            pass
        print('{} {} '.format(login.validated, login.approved))
        if login.validated:
            if not login.approved:
                sys.exit(2)
                run_command('doveadm kick team {}'.format(ip))
            else: sys.exit(0)
        time.sleep(10)
        t = t + 10
        if t > TIMEOUT_SECONDS: sys.exit(2)
    sys.exit(2)

if ip != '127.0.0.1':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
    import django
    django.setup()
    from django.conf import settings
    from requests.auth import HTTPBasicAuth
    from shell.models import ShellLogin
    from security.models import UserIpAddress
    for i in UserIpAddress.objects.filter(ip_address=ip):
        if i.risk_detected:
            sys.exit(2)
    FRAUDGUARD_USER = settings.FRAUDGUARD_USER
    FRAUDGUARD_SECRET = settings.FRAUDGUARD_SECRET
    RISK_LEVEL = 1
    def check_raw_ip_risk(ip_addr, soft=False):
        try:
            ip=requests.get('https://api.fraudguard.io/ip/' + ip_addr, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
            j = ip.json()
            if int(j['risk_level']) > RISK_LEVEL:
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return not soft
        return False
#    for ip in ips:
#        if not ip == '127.0.0.1' and check_raw_ip_risk(ip, True):
#            run_command('doveadm kick team {}'.format(output))
    ip = ips[0]
    print(ip)
    if ip != '127.0.0.1':
         thread_function(ip, code[:6])
#        x = threading.Thread(target=thread_function, args=(ip,))
#        x.start()

