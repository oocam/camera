#!/bin/bash

sh /home/pi/switch_ap.sh
git reset --hard
git pull
sh /home/pi/switch_ap.sh
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf.backup /etc/wpa_supplicant/wpa_supplicant.conf
killall python3
sh /home/pi/run.sh