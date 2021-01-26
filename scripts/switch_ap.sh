#!/bin/bash 

#Ensure that WiFI radio is not blocked 
sudo rfkill unblock wlan

#reverting dhcpcd.conf 
sudo mv /etc/dhcpcd.conf /etc/dhcpcd.conf.tmp 
sudo mv /etc/dhcpcd.conf.backup /etc/dhcpcd.conf
sudo mv /etc/dhcpcd.conf.tmp /etc/dhcpcd.conf.backup

#reverting dnsmasq.conf
sudo mv /etc/dnsmasq.conf.orig /etc/dnsmasq.conf.tmp 
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo mv /etc/dnsmasq.conf.tmp /etc/dnsmasq.conf

if [[ "$(hostname -I)" =~ "192.168.5.1" ]]; then 
	#switch to WiFi mode
	echo "Switching to Wifi mode"
	sudo systemctl stop hostapd
	sudo systemctl disable hostapd  
	sudo systemctl mask hostapd  
	echo "Restarting services"
	sudo systemctl restart dnsmasq
	sudo systemctl restart dhcpcd 
else
	#switch to AP mode 
	echo "Switching to AP mode"
        sudo systemctl unmask hostapd
	sudo systemctl enable hostapd  
	sudo systemctl restart dnsmasq
       	sudo ip link set wlan0 down 
	sudo ip link set wlan0 up
	sudo systemctl restart dhcpcd
	sudo systemctl restart hostapd
fi
