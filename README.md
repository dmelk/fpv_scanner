# fpv_scanner
FPV AV Video scanner

## Installation

This is Python code build for luckfox Pico Plus board: https://wiki.luckfox.com/Luckfox-Pico/Luckfox-Pico-RV1103/Luckfox-Pico-Plus-Mini/Luckfox-Pico-quick-start

To install it you need to change the firmware to inclue package `paho-mqtt`

Next simply create `scanner_config.json` and copy all files to the `/fpv_scanner` directory.

Lower all S99 priorities:
```bash
cd /etc/init.d/
mv S99_auto_reboot S98_auto_reboot
mv S99hciinit S98hciinit
mv S99python S98python
mv S99luckfoxconfigload  S98luckfoxconfigload
mv S99rtcinit S98rtcinit
mv S99usb0config S98usb0config
```

Then copy `./init.d/S99zscanner` to `/etc/init.d/` and make it executable:
```bash

cp /fpv_scanner/init.d/S99scanner /etc/init.d/
chmod +x /etc/init.d/S99scanner
```