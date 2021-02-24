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
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

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
                "ip_address": data[key]['ip'],
                "registered": data[key]['comment'],
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
                comment = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
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
                comment = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                netmiko.send_config_set([
                    '/ip dhcp-server lease make-static [find mac-address=' + mac + ']',
                    '/ip dhcp-server lease set [find mac-address=' + mac + '] address=0.0.0.0 block-access=yes comment="' + comment + '"' ,
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

## START: show whitelist
def showWhitelist():
    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    try:
        leases = api.get_resource('ip/dhcp-server/lease')
        dhcp = leases.get(dynamic="no", block_access="no")

        message = "✅ Allowed Device ✅\n\n"
        if dhcp:
            for item in dhcp:
                message += "• " + msgencode(item['host-name']) + "\n"
                message += "MAC: " + item['mac-address'] + "\n"
                message += "IP: " + msgencode(item['address']) + "\n"
                message += "Allowed since: " + msgencode(item['comment']) + "\n\n"

        else:
            message += "Empty Data"

        sendMessage(message)
        logout(netmiko, rosapi)
        return {"status":True, "data": message}
            
    except:
        print(getException())
        sendMessage("⚠️ showWhitelist error: Action failed")
        return {"status":False, "data": "showWhitelist error: Action failed"}
## END: show whitelist


## START: show blacklist
## START: show whitelist
def showWhitelist():
    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    try:
        leases = api.get_resource('ip/dhcp-server/lease')
        dhcp = leases.get(dynamic="no", block_access="yes")

        message = "❌ Blocked Device ❌\n\n"
        if dhcp:
            for item in dhcp:
                message += "• " + msgencode(item['host-name']) + "\n"
                message += "MAC: " + item['mac-address'] + "\n"
                message += "Blocked since: " + msgencode(item['comment']) + "\n\n"

        else:
            message += "Empty Data"

        sendMessage(message)
        logout(netmiko, rosapi)
        return {"status":True, "data": message}
            
    except:
        print(getException())
        sendMessage("⚠️ showBlocklist error: Action failed")
        return {"status":False, "data": "showBlocklist error: Action failed"}
## END: show whitelist

## END: show blacklist


## START: show data by mac address
def showMac(message_data):
    input = message_data.split()
    netmiko = netmiko_conn(router, username, password)
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()

    try:
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
            return {"status":True, "data":"showMac() done."}
        else:
            logout(netmiko, rosapi)
            return {"status":False,"data":"Related DHCP lease not found."}
    except:
        print(getException())
        sendMessage("⚠️ showMac error: action failed")
        logout(netmiko, rosapi)
        return {"status":False,"data":"showMac: Action failed."}
    
## END: show data by mac address


## START: change IP address
def setIP(message_data):
    input = message_data.split()
    rosapi = rosapi_conn(router, username, password)
    api = rosapi.get_api()
    netmiko = netmiko_conn(router, username, password)

    try:
        leases = api.get_resource('ip/dhcp-server/lease')
        dhcp = leases.get(mac_address=input[1], dynamic="no")
        if dhcp:
            for item in dhcp:
                host = item['host-name']
                oldip = item['address']

        try:
            netmiko.send_config_set([
                '/ip dhcp-server lease set [find mac-address=' + input[1] + '] address="' + input[2] + '"',
                '/ip arp set [find mac-address=' + input[1] + '] address="' + input[2] + '"'
            ])
            success = True
        except:
            print(getException())

        if success:
            response = sendMessage("✅ IP Changed ✅\nHostname: *" + msgencode(host) + "*\nMAC Address: *" + input[1] +
                    "*\nOld IP: ~" + msgencode(oldip) + "~\nNew IP: *" + msgencode(input[2]) + "*"
                )
        else:
            response = sendMessage("⚠️ Couldn't change the IP address")

    except :
        print(getException())
        response = sendMessage("⚠️ setIP Error: Action failed")

    logout(netmiko, rosapi)
    return response
## END: change IP address



## begin /webhook
@app.route('/webhook', methods = ['POST'])
def webhook():
    if request.is_json:
        input = request.get_json()
        print(json.dumps(input, indent=4))
        
        try:
            input['callback_query']
            callback = True
        except:
            callback = None

        try:
            input['message']
            message = True
        except:
            message = None

        if callback:
            if input['callback_query']['message']['chat']['id'] == int(chat_id):
                message_id = input['callback_query']['message']['message_id']
                if input['callback_query']['data']:
                    message_data = input['callback_query']['data']
                    response = authorization(message_id, message_data)
                else:
                    response = {"status":False,"data":"Wrong Command."}
            else:
                response = {"status":False,"data":"Unknown source."}

        elif message:

            if input['message']['from']['id'] == int(chat_id):
                message_id = input['message']['message_id']
                message_data = input['message']['text']

                if "/help" in message_data:
                    response = sendMessage("ℹ️ Available Commands ℹ️\n*/help* : Show available commands\\.\n*/whitelist* : Show allowed devices\\.\n*/blocklist* : Show blocked devices\\.\n*/show _\\<mac\\>_* : Show IP based on Mac address\\.\n*/static _\\<mac\\> \\<ip\\>_* :  Change the leased IP address\\.\n*/allow _\\<mac\\>_* : Allow blocked device\\.\n*/deny _\\<mac\\>_* : Deny allowed device\\.\n\nNote:\n*_\\<something\\>_* is required varibale\\.")

                elif "/static" in message_data:
                    response = setIP(message_data)

                elif "/show" in message_data:
                    response = showMac(message_data)

                elif "/whitelist" in message_data:
                    response = showWhitelist()

                elif "/blacklist" in message_data:
                    response = showBlacklist()
                
                elif "/allow" in message_data:
                    pass

                elif "/deny" in message_data:
                    pass
                
                else: 
                    response = {"status":False,"data":"Wrong Command."}
            else:
                response = {"status":False,"data":"Unknown source."}

        else:
            response = {"status":False,"data":"Invalid Message."}

        print(json.dumps(response, indent=4))
        return jsonify(response)
    else:
        print("Feedback: Invalid JSON format.")
        return jsonify({"status":False,"data":"Invalid JSON format."})
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
        print(json.dumps(response, indent=4))
        return jsonify({"status":True,"data":"Notification sent."})
    else:
        print("Feedback: Empty Data Received")
        return jsonify({"status":False,"data":None})
## end /push_notif


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)