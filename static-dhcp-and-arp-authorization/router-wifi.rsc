# mar/13/2021 21:54:06 by RouterOS 6.48.1

/interface wireless
set [ find default-name=wlan1 ] band=2ghz-b/g/n disabled=no frequency=2437 \
    ssid=IDN

/interface l2tp-client
add connect-to=vpnserver.webiptek.com disabled=no name=to-sg-api-server \
    password=passwordvpm user=uservpn

/interface wireless
add arp=reply-only disabled=no keepalive-frames=disabled mac-address=\
    6E:3B:6B:30:8C:88 master-interface=wlan1 multicast-buffering=disabled \
    name=wifi ssid=WIFI-IDN wds-cost-range=0 wds-default-cost=0 wps-mode=\
    disabled

/interface wireless security-profiles
set [ find default=yes ] authentication-types=wpa-psk,wpa2-psk eap-methods="" \
    mode=dynamic-keys supplicant-identity=MikroTik wpa-pre-shared-key=\
    passwordwifi wpa2-pre-shared-key=passwordwifi

/ip pool
add name=dhcp_pool0 ranges=10.10.10.2-10.10.10.254

/ip dhcp-server
add address-pool=dhcp_pool0 disabled=no interface=wifi lease-script=":do {\r\
    \n  :local push \"https://sg1.webiptek.com/push_notif\"\r\
    \n\r\
    \n  :foreach leasecounter in=[/ip dhcp-server lease find where dynamic] do\
    ={\r\
    \n    :local leasename [/ip dhcp-server lease get \$leasecounter host-name\
    ];\r\
    \n    :local leaseip [/ip dhcp-server lease get \$leasecounter address];\r\
    \n    :local leasemac [/ip dhcp-server lease get \$leasecounter mac-addres\
    s];\r\
    \n    :local new \"host=\$leasename&ip=\$leaseip&mac=\$leasemac\"\r\
    \n    :log warning \"!!! NEW LEASE: \$leasename using \$leaseip \$leasemac\
    \_END !!!\";\r\
    \n    /tool fetch url=\$push  http-method=post output=none http-data=\$new\
    \r\
    \n  };\r\
    \n};" name=dhcp1

/ip address
add address=10.10.10.1/24 interface=wifi network=10.10.10.0

/ip dhcp-client
add disabled=no interface=wlan1

/ip dhcp-server network
add address=10.10.10.0/24 gateway=10.10.10.1

/ip firewall nat
add action=masquerade chain=srcnat out-interface=wlan1

/ip route
add comment=to-api-server-via-vpn distance=1 dst-address=10.0.22.0/24 gateway=\
    10.0.22.1

/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set ssh address=10.0.22.58/32
set www-ssl certificate=CA-for-API
set api-ssl address=10.0.22.58/32 certificate=CA-for-API

/system clock
set time-zone-name=Asia/Jakarta

/system identity
set name=Router-WIFI
