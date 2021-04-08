#!/bin/bash
git reset --hard
git pull
pip install -r openoceancamera/requirements.txt
cp $HOME/etc/dhcpcd.conf /etc/dhcpcd.conf.backup
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf.backup /etc/wpa_supplicant/wpa_supplicant.conf
