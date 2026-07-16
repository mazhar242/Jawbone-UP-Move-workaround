# Jawbone-UP-Move-workaround
Trying to bring life to an old Jawbone UP Move fitness tracker with help from AI tools available. Zero coding experience.
step 1: detect the device over BLE protocol and reading GATT services ( jwbn up detection.py , success).
It is also possible to extract Modelname and versions. (code not uploaded).
step 2: record live reading from the device, keeping live communication and read data change (jwbnkeepalive.py, partially works).
Some example output files are added, to show the services that are found.
