#!/bin/bash

sudo cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.backup
network="network={\n\tssid=\"$1\"\n\tpsk=\"$2\"\n}"

sudo echo -e $network >> /etc/wpa_supplicant/wpa_supplicant.conf
