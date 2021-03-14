# Static DHCP Lease and Static ARP

Make sure the API server can be accessed from internet using static public IP or using DMZ zone. Because the API server have to receive data from Telegram.
Also, make sure the API server can communicate with the Router.

Demo: [[Video] Static DHCP Lease Authorization using Telegram](https://youtu.be/NB3frpB1xrU).

## A. Run the API server (flask)

I am using python3.8.x.
Make sure you already in the _static-dhcp-and-arp-authorization_ directory.

We will use [routeros-api](https://pypi.org/project/RouterOS-api/) python library.

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
export API_BOT="1555959235:AAHCGtLj5NDazIDW7qTaohqcv9SUNyVXZ5g"
export CHAT_ID=290072888
export ROUTER="10.0.22.100"
export ROUTER_USER="admin"
export ROUTER_PASSWORD="123"
export DHCP_INTERFACE="wifi"
export SSH_PORT=22
export LOG_FILE="/home/user/mikrotik-scripting/static-dhcp-and-arp-authorization/log.json"
```

7. Consider to turn off debug mode end of _main.py_
```
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
```

8. The best practice is running the flask server using WSGI. But, it requires more configuration. So, I start the flask script by executing the _main.py_ file.
```
$ python3 main.py
```
```
 * Serving Flask app "main" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: of
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 187-258-023

```



## B. Secure The API (Web server) using SSL

If needed, you can secure your API server using SSL.
In the following example, we using nginx configured as reverse proxy to flask (localhost port 5000).


1. Create virtualhost using your domain name.
```
$ sudo nano /etc/nginx/sites-available/example.com
```
```
server {
    server_name example.com;
    listen 80;
    location / {
        include proxy_params;
        proxy_set_header   X-Real-IP          $remote_addr;
        proxy_set_header   X-Forwarded-Proto  $scheme;
        proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_pass         http://127.0.0.1:5000;
        proxy_headers_hash_max_size 512;
        proxy_headers_hash_bucket_size 64;
    }
}
```

2. Install certbot for nginx
```
$ sudo apt-get install python-certbot-nginx
```

3. Request the certificate.
```
$ sudo certbot --nginx -d example.com
```

4. If that’s successful, certbot will ask how you’d like to configure your HTTPS settings.
```
Please choose whether or not to redirect HTTP traffic to HTTPS, removing HTTP access.
-------------------------------------------------------------------------------
1: No redirect - Make no further changes to the webserver configuration.
2: Redirect - Make all requests redirect to secure HTTPS access. Choose this for
new sites, or if you're confident your site works on HTTPS. You can undo this
change by editing your web server's configuration.
-------------------------------------------------------------------------------
Select the appropriate number [1-2] then [enter] (press 'c' to cancel):
```
I recomended to select option 2.

5. Done. Now, your API server runnning in https port 443.



## C. Configuration on Router

Make sure you have configured ARP reply-only on the appropriate interface (interface to clients).

Add the following script to IP > DHCP Server > _Select the coresponding DHCP Server_
At tab "Script".
```
:do {
  :local push "https://example.com/push_notif"

  :foreach leasecounter in=[/ip dhcp-server lease find where dynamic] do={
    :local leasename [/ip dhcp-server lease get $leasecounter host-name];
    :local leaseip [/ip dhcp-server lease get $leasecounter address];
    :local leasemac [/ip dhcp-server lease get $leasecounter mac-address];
    :local new "host=$leasename&ip=$leaseip&mac=$leasemac"
    :log warning "!!! NEW LEASE: $leasename using $leaseip $leasemac END !!!";
    /tool fetch url=$push  http-method=post output=none http-data=$new
  };
};
```
Change "https://example.com/push_notif" to appropriate web URL.
That script will be executed when Router leased an IP address.

