#!/bin/bash

bash /home/pi/switch_ap.sh
git reset --hard
git pull
bash /home/pi/switch_ap.sh
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf.backup /etc/wpa_supplicant/wpa_supplicant.conf
killall python3
bash /home/pi/run.sh