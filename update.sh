#!/bin/bash

sudo chmod +x /home/pi/scripts/switch_ap.sh
sudo chmod +x /home/pi/scripts/update.sh
bash /home/pi/scripts/switch_ap.sh
/home/pi/scripts/update.sh
bash /home/pi/scripts/switch_ap.sh
reboot