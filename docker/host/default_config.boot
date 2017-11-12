
/* This is a minimalistic configuration file for Xorp
    
   Since the configuration of most routing protocols requires
   knowledge of the IP addresses this configuration file
   only includes support for Multicast forwarding (IGMP and PIM)
   
   In order for this configuration to work you need to have
   at least two network interfaces (eth0 and eth1).

   If you want to see a more detailed configuration sample please
   take look at /usr/share/doc/xorp/examples/config.boot.sample

*/

interfaces {
    restore-original-config-on-shutdown: false
}

fea {
    unicast-forwarding4 {
	disable: false
    }
}

