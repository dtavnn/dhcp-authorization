from netmiko import ConnectHandler
from flask import Flask
from flask import request
from datetime import datetime
from flask import jsonify
import sys
import os
import json
import requests
import routeros_api
import linecache

## ap config
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

## telegram bot and router credential
api_bot = "1555668877:AAFZfmB6UH-e-FLnJS31GRAAaocYNc8gtaA"
chat_id = 290072690
router = "172.16.8.181"
username = "admin"
password = "123"


## exception
def getException():
    exc = sys.exc_info()
    f = exc.tb_frame
    lineno = exc.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc)

## netmiko connection
def netmiko_conn(host, username, password):
    device = {
        'device_type': 'mikrotik_routeros',
        'host': host,
        'username': username,
        'password': password
    }
    connection = ConnectHandler(**device)
    return connection

## routerosapi connection
def rosapi_conn(host, username, password):
    connection = routeros_api.RouterOsApiPool(
        host, username=username, password=password, plaintext_login=True, 
        use_ssl=True, ssl_verify=False, ssl_verify_hostname=False
    )
    return connection

##logout from netmiko and routeros api connection
def logout(netmiko, rosapi):
    netmiko.disconnect()
    rosapi.disconnect()

def msgencode(text):
    text = text.replace('_', '\\_')
    text = text.replace('*', '\\*')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = text.replace('(', '\\(')
    text = text.replace(')', '\\)')
    text = text.replace('~', '\\~')
    text = text.replace('`', '\\`')
    text = text.replace('>', '\\>')
    text = text.replace('#', '\\#')
    text = text.replace('+', '\\+')
    text = text.replace('-', '\\-')
    text = text.replace('=', '\\=')
    text = text.replace('|', '\\|')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('.', '\\.')
    text = text.replace('!', '\\!')
    print(text)
    return text

# loggin [
#   "mac": {
#       "comment": "XXX"
#       "ip": "X.X.X.X"
#   }
# ]   
def logging(data):
    with open(os.environ.get('LOG_FILE'), "r+") as file: 
        object = json.load(file) 
        for key in data:
            object[key['mac']] = {
                "comment": key['comment'],
                "ip_address": key['ip'],
                "registered": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }

        file.seek(0)
        json.dump(object, file, indent = 4)
        file.truncate()
    
    print(json.dumps(data, indent = 4))



## begin /static_arp
@app.route('/static_arp', methods = ['POST'])
def static_arp():

    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    # get dhcp lease based on mac-address
    leases = api.get_resource('ip/dhcp-server/lease')
    dhcp = leases.get(dynamic="yes")
    return jsonify(dhcp)

    if dhcp:
        result = {
            'status': True,
            'data': []
        }
        print(result)
        x = 0
        for item in dhcp:
            # get the id only
            mac_address = item['mac-address']
            result['data'].append(mac_address)
            netmiko.send_config_set('/ip dhcp-server lease make-static [find mac-address=' + mac_address + ']')
            x+=1
        
        logout(netmiko, rosapi)
        return jsonify(result)

    else:
        result = {
            'status': False,
            'data': None
        }
        logout(netmiko, rosapi)
        return jsonify(result)

    # close the connection



## begin /webhook
@app.route('/webhook', methods = ['POST'])
def webhook():
    if request.is_json:
        input = request.json.get()
        print(input)
        return jsonify(input)

    else:
        return "JSON Empty"
## end webhook


## begin /push_notif
@app.route('/push_notif', methods = ['POST'])
def push_notif():
    url = "https://api.telegram.org/bot" + api_bot + "/sendMessage"

    if request.form:
        data = request.form.copy()
        print(data)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        host = msgencode(data['host'])
        ip = msgencode(data['ip'])
        mac = data['mac']

        headers = {
        'Content-Type': 'application/json'
        }
        payload = {
            "chat_id": chat_id,
            "text": "\\=\\=\\=\\= New Device Connected \\=\\=\\=\\=\nHostname: *" + host +
            "*\nIP: *" + ip + "*\nMAC Address: *" + mac + "*\nConnected At: " + now + "",
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "ALLOW",
                            "callback_data": "{'action':'allow','mac': '"+mac+"'}"
                        },
                        {
                            "text": "DENY",
                            "callback_data": "{'action':'deny','mac': '"+mac+"'}"
                        }
                    ]
                ]
            }
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload)).json()
        print(response)
        return "Sent"
    else:
        print("None")
        return jsonify({"status":False,"data":None})
## end /push_notif


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)