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
#print(json.dumps(dhcp, indent=4))

# TODO: make static lease
for item in dhcp:
    # get the id only
    id = item['id']
    print("id =" + id)
    leases.set(id=id, address="10.10.10.20")

# close the connection
connection.disconnect()