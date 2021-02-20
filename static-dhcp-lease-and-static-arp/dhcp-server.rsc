:do {
  :local newtvs 0;
  :local debug "no";
  :local foundtv "no";

  :foreach leasecounter in=[/ip dhcp-server lease find where dynamic] do={
    :local leasename [/ip dhcp-server lease get $leasecounter host-name];
    :local leaseip [/ip dhcp-server lease get $leasecounter address];
    :local leasemac [/ip dhcp-server lease get $leasecounter mac-address];
    :log warning "!!! NEW LEASE: $leasename using $leaseip $leasemac END !!!";
  };
};


 ip dhcp-server lease make-static [find mac-address=70:5E:55:6B:CE:2D]
[admin@IDN-Rizqi] > ip dhcp-server lease set [find mac-address=70:5E:55:6B:CE:2D] 
comment=r3p
[admin@IDN-Rizqi] > ip arp add address=10.10.10.254 mac-address=70:5E:55:6B:CE:2D interface=wifi
