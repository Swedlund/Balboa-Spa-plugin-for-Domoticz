#
#   Balboa Spa Plugin
#
#   Frix, 2020
#

"""
<plugin key="Balboa" name="Balboa Spa" author="Frix" version="0.2">
    <description>
        <h2>Balboa Spa - Tempature status</h2><br/>
        Creates two temp sensors that shows actual and defined temp of your Balboa Spa.
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.1.1"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import urllib.request
import sys
import os
import subprocess
import json

class BasePlugin:

    def __init__(self):
        self.lastPolled = 0
        self.pollInterval = 5
        self.scriptPath = os.path.dirname(os.path.realpath(__file__))
        return

    def onStart(self):
        Domoticz.Heartbeat(30)

        if (len(Devices) == 0):
            Domoticz.Device(Name="Actual", Unit=1, TypeName="Temperature").Create()
            Domoticz.Device(Name="Defined", Unit=2, TypeName="Temperature").Create()

            Options = {"LevelActions": "|",
                      "LevelNames": "Low|High",
                      "LevelOffHidden": "True",
                      "SelectorStyle": "1"}

            Domoticz.Device(Name="Temp range", Unit=3, TypeName="Selector Switch", Options=Options).Create()

            self.updateTemp()
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        tempRange = self.toggleTempRange()
        
        if str(Command).lower() == "set level" and tempRange == "High":
            Devices[Unit].Update(1,str(10))
        else:
            Devices[Unit].Update(0,str(0))


    def onHeartbeat(self):
        self.lastPolled = self.lastPolled + 1
        if (self.lastPolled > self.pollInterval): 
            self.lastPolled = 0
            self.updateTemp()

    def updateTemp(self):
        Domoticz.Debug("Updating temperature...")
        try:  
            status = self.getPoolStatus()
            Domoticz.Debug("Get actual temp value: "+str(status["TEMP"]))
            if str(status["TEMP"]) != "0.0":
               Domoticz.Debug("Temp known => device update")
               Devices[1].Update(nValue=1, sValue=str(status["TEMP"]), TimedOut=0)
            Domoticz.Debug("Get defined temp value: "+str(status["SET_TEMP"]))
            Devices[2].Update(nValue=1, sValue=str(status["SET_TEMP"]), TimedOut=0)
            if str(status["TEMP_RANGE"]) == "High" and Devices[3].nValue != 1:
                Devices[3].Update(1,str(10))
            elif str(status["TEMP_RANGE"]) == "Low" and Devices[3].nValue != 0:
                Devices[3].Update(0,str(0))
        except:
            Domoticz.Debug("Failed to update!")
            self.lastPolled = self.pollInterval

    def getPoolStatus(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" status", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = json.loads(proc.communicate()[0].decode('utf-8').strip())
            Domoticz.Debug("Output: "+str(output))
        except ValueError as e:
            return ""
        return output

    def toggleTempRange(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" temprange", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = proc.communicate()[0].decode('utf-8').strip()
            Domoticz.Debug("Output: "+str(output))
        except ValueError as e:
            return ""
        return output

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
