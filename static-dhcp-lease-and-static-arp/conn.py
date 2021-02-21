from netmiko import ConnectHandler
from netmiko.mikrotik import MikrotikRouterOsSSH
import routeros_api

def netmiko(host, username, password):
    connection = {
        'device_type': 'mikrotik_routeros',
        'host': host,
        'username': username,
        'password': password
    }
    return connection

def mikrotikapi(host, username, password):
    # define and start the connection
    connection = routeros_api.RouterOsApiPool(host, username=username, password=password, plaintext_login=True)
    return connection