import re, traceback, requests, json, regex, sys, glob, time, threading, datetime, asyncio
with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)
from subprocess import Popen, STDOUT, PIPE

output = ''

def run_command(command):
    cmd = command.split(' ')
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=str("/"))
    time.sleep(0.1)
    proc.kill()
    return proc.stdout.read().decode("unicode_escape")

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
time.sleep(1)
op = output.split('\n')
op.reverse()
output = '\n'.join(op)
ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))

print(output)
thread_started = False
while False and not output:
    print('awaiting output')
    time.sleep(3)
    if output:
        op = output.split('\n')
        op.reverse()
        output = '\n'.join(op)
        ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))
#        if len(ips) == 0 and thread_started: sys.exit(2)
    if not thread_started and not output:
        thread_started = True
        load_path2()
        break

#print(output)

print(ips)
if len(ips) == 0:
    sys.exit(2)
#    logpath = glob.glob('/var/log/auth.log.*')[-1]
#    if logpath: output2 = run_command('sudo tail -n 5000 {}'.format(logpath))
#    op = output2.split('\n')
#    op.reverse()
#    output = '\n'.join(op)
#    ips = unique(re.findall(IPV4ADDR + '|' + IPV6ADDR, output))
#if len(ips) == 0:
#    import sys
#    sys.exit(0)
ip = ips[0]
print(ip)
if ip != '127.0.0.1':
    print('Foreign IP')
    import os
    from requests.auth import HTTPBasicAuth
    FRAUDGUARD_USER = keys['FRAUDGUARD_USER']
    FRAUDGUARD_SECRET = keys['FRAUDGUARD_SECRET']
    ANTIDEO_KEY = keys['ANTIDEO_KEY']
    RISK_LEVEL = 1
    def check_raw_ip_risk(ip_addr, soft=False, guard=True):
        if not guard:
            try:
                ip=requests.get('https://api.antideo.com/ip/health/' + ip_addr + '&apiKey={}'.format(ANTIDEO_KEY))
                j = None
                try:
                    j = ip.json()
                except: pass
                if j and j['health']['toxic'] or j['health']['spam']:
                    return True
                else:
                    return not soft
            except:
                print(traceback.format_exc())
                return not soft
        try:
            ip=requests.get('https://api.fraudguard.io/v2/ip/' + ip_addr, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
            for resp in ip.history: print(resp.status_code)
            print(ip)
            j = ip.json()
            if int(j['risk_level']) > RISK_LEVEL:
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return not soft
        return False
    blacklisted = check_blacklist(ip)
    if not ip == '127.0.0.1' and (blacklisted or check_raw_ip_risk(ip, soft=True)):
        run_command('doveadm kick team {}'.format(output))
        if not blacklisted:
            blacklist(ip)
        sys.exit(1)
    print(blacklisted)
    sys.exit(0)
    ip = ips[0]
