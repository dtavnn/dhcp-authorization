from netmiko import ConnectHandler
from netmiko.mikrotik import MikrotikRouterOsSSH
from flask import Flask
from flask import jsonify
import json
import routeros_api
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

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
    connection = routeros_api.RouterOsApiPool(host, username=username, password=password, plaintext_login=True)
    return connection

def logout(netmiko, rosapi):
    netmiko.disconnect()
    rosapi.disconnect()

## begin /static_arp
@app.route('/static_arp')
def static_arp():
    # data
    host = '172.16.8.181'
    username = 'admin'
    password = '123'
    mac = '70:5E:55:6B:CE:2D'

    netmiko = netmiko_conn(host, username, password)
    rosapi = rosapi_conn(host, username, password)
    api = rosapi.get_api()


    # get dhcp lease based on mac-address
    leases = api.get_resource('ip/dhcp-server/lease')
    dhcp = leases.get(dynamic="yes")

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


