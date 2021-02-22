# Static DHCP Lease and Static ARP

## A. Preparation

I am using python3.8.x.
Make sure you already in the _static-dhcp-lease-and-static-arp_ directory.

We will use [RouterOS-api](https://pypi.org/project/RouterOS-api/) python library.

1. Create a project folder and a venv folder within.
```
$ python3 -m venv venv
```

2. [Install PIP for Python3](https://pip.pypa.io/en/stable/installing/)


3. Before you work on your project, activate the corresponding environment:
```
$ . venv/bin/activate
```

4. Install the required modules.
```
$ pip3 install -r requirements.txt
```

5. Add required environment variables.
```
export API_BOT="1555959235:AAFZfmB6UH-e-FLnJS31GRAAaocYNc8hrqU"
export CHAT_ID=290072690
export ROUTER="172.16.8.181"
export ROUTER_USER="admin"
export ROUTER_PASSWORD="123"
export LOG_FILE="/home/xdnroot/Documents/repository/mikrotik-scripting/static-dhcp-lease-and-static-arp/log.json"
```

```
nmcli connection add connection.id to-chr con-name to-chr type VPN vpn-type l2tp ifname -- connection.autoconnect no ipv4.method auto vpn.data "gateway = 54.255.107.223, ipsec-enabled = no, mru = 1400, mtu = 1400, password-flags = 0, refuse-chap = yes, refuse-mschap = yes, refuse-pap = yes, require-mppe = yes, user = dynamic" vpn.secrets password=idnmantab

```



## B. How to Run

Then start the script by execute the main.py file.
```
$ python3 main.py
```
