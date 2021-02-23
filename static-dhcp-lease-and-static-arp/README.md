# Static DHCP Lease and Static ARP

## A. Preparation

I am using python3.8.x.
Make sure you already in the _static-dhcp-lease-and-static-arp_ directory.

We will use [RouterOS-api](https://pypi.org/project/RouterOS-api/) python library.

1. Install PIP for python3 via [PIP docummentation](https://pip.pypa.io/en/stable/installing/) or use following command.
```
$ sudo apt-get install python3-pip
```

2. Install python3 virtualenv.
```
$ sudo apt-get install python3-venv
```

3. Create virtual environmen use "venv" folder within.
```
$ python3 -m venv venv
```

4. Before you work on your project, activate the corresponding environment:
```
$ . venv/bin/activate
```

5. Install the required modules.
```
$ cd static-dhcp-lease-and-static-arp/
$ pip3 install -r requirements.txt
```

6. Add required environment variables.
```
export API_BOT="1555959235:AAFZfmB6UH-e-FLnJS31GRAAaocYNc8hrqU"
export CHAT_ID=240072653
export ROUTER="10.0.22.2"
export ROUTER_USER="admin"
export ROUTER_PASSWORD="123"
export LOG_FILE="/home/xdnroot/Documents/repository/mikrotik-scripting/static-dhcp-lease-and-static-arp/log.json"
```

## B. How to Run

Then start the script by execute the main.py file.
```
$ python3 main.py
```
