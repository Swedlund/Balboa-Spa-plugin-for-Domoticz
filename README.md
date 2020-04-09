# Balboa-Spa-plugin-for-Domoticz
A Domoticz plugin to corntoll and monitor the temperature of your Balboa Spa Hot Tub.

## Prerequisites
1. Request libary for Python 3: https://pypi.org/project/requests/
1. Sockets libary for Python 3: https://pypi.org/project/sockets/
1. crc8 libary for Python 3: https://pypi.org/project/crc8/ 

## Installation
1. Clone repository into your Domoticz plugins folder
    ```
    cd domoticz/plugins
    git clone https://github.com/Frixzon/Balboa-Spa-plugin-for-Domoticz.git
    ```
1. Restart domoticz
    ```
    sudo service domoticz.sh restart
    ```
1. Make sure that "Accept new Hardware Devices" is enabled in Domoticz settings
1. Go to "Hardware" page
1. Enter the Name
1. Select Type: `Balboa Spa`
1. Click `Add`

## Update
1. Go to plugin folder and pull new version
    ```
    cd domoticz/plugins/Balboa-Spa-plugin-for-Domoticz
    git pull
    ```
1. Restart domoticz
    ```
    sudo service domoticz.sh restart
    ```

## Devices
The following devices are created:

| Type                | Name                      | Description
| :---                | :---                      | :---
| Selector Switch | Temp range                     | Can set the temerature range High or Low
| Temperature | Actual                         | Shows the actual water temperatue
| Temperature | Defined                        | Shows the configured water temperature level
