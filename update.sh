#!/bin/bash

chmod +x /home/pi/scripts/switch_ap.sh
chmod +x /home/pi/scripts/update.sh
bash /home/pi/switch_ap.sh
/home/pi/scripts/update.sh
bash /home/pi/switch_ap.sh
reboot