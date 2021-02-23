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

## App config
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

## telegram bot and router credential
api_bot = os.environ.get('API_BOT')
chat_id = os.environ.get('CHAT_ID')
router = os.environ.get('ROUTER')
username = os.environ.get('ROUTER_USER')
password = os.environ.get('ROUTER_PASSWORD')


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

## logout from netmiko and routeros api connection
def logout(netmiko, rosapi):
    netmiko.disconnect()
    rosapi.disconnect()
    return True

## encode telegram message
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
    return text

## add data to logs
def logging(data):
    print('******add data to logs******')
    with open(os.environ.get('LOG_FILE'), "r+") as file: 
        object = json.load(file) 
        for key in data:
            object[key] = {
                "comment": data[key]['comment'],
                "ip_address": data[key]['ip'],
                "registered": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }

        file.seek(0)
        json.dump(object, file, indent = 4)
        file.truncate()
        return True

## send message to telegram
def sendMessage(message, keyboard=None):
    url = "https://api.telegram.org/bot" + api_bot + "/sendMessage"
    headers = {
        'Content-Type': 'application/json'
    }

    if keyboard:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
            "reply_markup": keyboard
        }
    else:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True
        }

    return requests.request("POST", url, headers=headers, data=json.dumps(payload)).json()

## delete message by message_id
def deleteMessage(message_id):
    url = "https://api.telegram.org/bot" + api_bot + "/deleteMessage"
    headers = {
        'Content-Type': 'application/json'
        }
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
    }
    return requests.request("POST", url, headers=headers, data=json.dumps(payload)).json()


## START authorize new connected device
def authorization(message_id, message_data):
    input = json.loads(message_data)

    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    # get dhcp lease based on mac-address
    leases = api.get_resource('ip/dhcp-server/lease')
    dhcp = leases.get(mac_address=input['mac'], dynamic="yes")

    if dhcp:
        result = {}
        for item in dhcp:
            # get the id only
            host = item['host-name']
            ip = item['address']
            mac = item['mac-address']
            interface = os.environ.get('DHCP_INTERFACE')

            if input['action'] == 'allow':
                comment = "allow " + host
                netmiko.send_config_set([
                    '/ip dhcp-server lease make-static [find mac-address=' + mac + ']',
                    '/ip dhcp-server lease set [find mac-address=' + mac + '] comment="' + comment + '"',
                    '/ip arp add address=' + ip + ' mac-address=' + mac + ' interface=' + interface
                ])
                sendMessage("✅ Device Allowed ✅\nHostname: *" + msgencode(host) +
                    "*\nIP: *" + msgencode(ip) + "*\nMAC Address: *" + mac + "*"
                )
                deleteMessage(message_id)
            else:
                comment = "deny " + host
                netmiko.send_config_set([
                    '/interface wireless access-list add authentication=no forwarding=no mac-address=' + mac + ' comment="' + comment + '"',
                    '/ip dhcp-server lease remove [find mac-address=' + mac + ']',
                ])
                sendMessage("❌ Device Denied ❌\nHostname: *" + msgencode(host) +
                    "*\nIP: *" + msgencode(ip) + "*\nMAC Address: *" + mac + "*"
                )
                deleteMessage(message_id)

            result[mac] =  {
                "comment": comment,
                "ip": ip
            }

        logging(result)
        logout(netmiko, rosapi)
        return result
    else:
        return {"status":False,"data":"Related DHCP lease not found."}
## END: authorize new connected device


## START: show data by mac address
def showMac(message_data):
    input = message_data.split()

    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    # get dhcp lease based on mac-address
    leases = api.get_resource('ip/dhcp-server/lease')
    dhcp = leases.get(mac_address=input[1], dynamic="no")

    if dhcp:
        for item in dhcp:
            # get the id only
            host = item['host-name']
            ip = item['address']
            mac = item['mac-address']
            sendMessage("ℹ️ Device Info ℹ️\nHostname: *" + msgencode(host) +
                "*\nIP: *" + msgencode(ip) + "*\nMAC Address: *" + mac + "*"
            )

        logout(netmiko, rosapi)
        return "showMac() done."
    else:
        return {"status":False,"data":"Related DHCP lease not found."}
## END: show data by mac address


## START: change IP address
def setIP(message_data):
    input = message_data.split()

    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    leases = api.get_resource('ip/dhcp-server/lease')
    dhcp = leases.get(mac_address=input[1], dynamic="no")
    if dhcp:
        for item in dhcp:
            host = item['host-name']
            oldip = item['address']

    try:
        netmiko.send_config_set([
            '/ip dhcp-server lease make-static set [find mac-address=' + input[1] + '] address="' + input[2] + '"',
            '/ip arp set [find mac-address=' + input[1] + '] address="' + input[2] + '"'
        ])
        success = True
    except:
        print(getException())

    if success:
        sendMessage("ℹ️ IP Changed ℹ️\nHostname: *" + msgencode(host) + "*\nMAC Address: *" + input[1] +
                "*\nOld IP: *" + msgencode(oldip) + "*\nNew IP: *" + input[2] + "*"
            )
    else:
        sendMessage("⚠️ Error: Last action failed.")

    logout(netmiko, rosapi)
    return "setIP() done."
## END: change IP address



## begin /webhook
@app.route('/webhook', methods = ['POST'])
def webhook():
    if request.is_json:
        input = request.get_json()
        print(json.dumps(input, indent=4))

        if ['callback_query']:
            message_id = input['callback_query']['message']['message_id']
            if input['callback_query']['data']:
                message_data = input['callback_query']['data']
                response = authorization(message_id, message_data)
            else:
                response = {"status":False,"data":"Wrong Command."}

        else:
            message_id = input['message']['message_id']
            message_data = input['message']['text']
            if "/static" in message_data:
                response = setIP(message_data)
            elif "/show" in message_data:
                response = showMac(message_data)
            else: 
                response = {"status":False,"data":"Wrong Command."}
        print(response)
        return jsonify(response)
    else:
        print("Feedback: Wrong JSON format.")
        return jsonify({"status":False,"data":"Wrong JSON format."})
## end webhook


## begin /push_notif
@app.route('/push_notif', methods = ['POST'])
def push_notif():
    url = "https://api.telegram.org/bot" + api_bot + "/sendMessage"
    if request.form:
        data = request.form.copy()
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        host = msgencode(data['host'])
        ip = msgencode(data['ip'])
        mac = data['mac']
        message = "\\=\\=\\=\\= New Device Connected \\=\\=\\=\\=\nHostname: *" + host + "*\nIP: *" + ip + "*\nMAC Address: *" + mac + "*\nConnected At: " + now + ""
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "ALLOW",
                        "callback_data": "{\"action\":\"allow\",\"mac\":\""+mac+"\"}"
                    },
                    {
                        "text": "DENY",
                        "callback_data": "{\"action\":\"deny\",\"mac\":\""+mac+"\"}"
                    }
                ]
            ]
        }
        
        response = sendMessage(message, keyboard)
        print("=========== Feedback: Notification sent ===========")
        print(response)
        return jsonify({"status":True,"data":"Notification sent."})
    else:
        print("Feedback: Empty Data Received")
        return jsonify({"status":False,"data":None})
## end /push_notif


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)