import routeros_api, json

# data
ip = '172.16.8.181'
username = 'admin'
password = '123'
mac = '70:5E:55:6B:CE:2D'

# define and start the connection
connection = routeros_api.RouterOsApiPool(ip, username=username, password=password, plaintext_login=True)
api = connection.get_api()

# get dhcp lease based on mac-address
leases = api.get_resource('ip/dhcp-server/lease')
dhcp = leases.get(mac_address=mac)

# fetch all data
print(json.dumps(dhcp, indent=4))

for item in dhcp:
    # print the id only
    print(item['id'])

# close the connection
connection.disconnect()