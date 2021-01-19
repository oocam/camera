#!/bin/bash

./switch_ap.sh 
git pull 
./switch_ap.sh
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf.backup /etc/wpa_supplicant/wpa_supplicant.conf
