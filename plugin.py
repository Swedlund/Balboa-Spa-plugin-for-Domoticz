#
#   Balboa Spa Plugin
#
#   Frix, 2020
#

"""
<plugin key="Balboa" name="Balboa Spa" author="Darrepac" version="0.4">
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
        self.pollInterval = 1
        self.scriptPath = os.path.dirname(os.path.realpath(__file__))
        return

    def onStart(self):
        Domoticz.Heartbeat(30)
        Domoticz.Log("Reading SPA config and updating Domoticz...")
        try: 
            if (len(Devices) == 0):
                Domoticz.Device(Name="Actual", Unit=1, TypeName="Temperature").Create()
                Domoticz.Device(Name="Defined", Unit=2, TypeName="Temperature").Create()

                Options = {"LevelActions": "|",
                           "LevelNames": "Low|High",
                           "LevelOffHidden": "True",
                           "SelectorStyle": "1"}

                Domoticz.Device(Name="Temp range", Unit=3, TypeName="Selector Switch", Options=Options).Create()		
                status = self.getPoolConfig()
                if str(status["PUMP1"]) == "1":
                    Domoticz.Device(Name="Pump 1", Unit=5, TypeName="Switch").Create()			
                elif str(status["PUMP1"]) == "2":
                    Options = {"LevelActions": "|",
                               "LevelNames": "Off|Low|High",
                               "LevelOffHidden": "False",
                               "SelectorStyle": "0"}
                    Domoticz.Device(Name="Pump 1", Unit=5, TypeName="Selector Switch", Options=Options).Create()
                if str(status["PUMP2"]) == "1":
                    Domoticz.Device(Name="Pump 2", Unit=6, TypeName="Switch").Create()			
                elif str(status["PUMP2"]) == "2":
                    Options = {"LevelActions": "|",
                               "LevelNames": "Off|Low|High",
                               "LevelOffHidden": "False",
                               "SelectorStyle": "0"}
                    Domoticz.Device(Name="Pump 2", Unit=6, TypeName="Selector Switch", Options=Options).Create()			   
                if str(status["LIGHTS"]) == "1":
                    Domoticz.Device(Name="Lights", Unit=4, TypeName="Switch").Create()
                if str(status["BLOWER"]) == "1":
                    Domoticz.Device(Name="Blower", Unit=7, TypeName="Switch").Create()
                Options = {"LevelActions": "|",
                               "LevelNames": "Ready|Rest",
                               "LevelOffHidden": "True",
                               "SelectorStyle": "0"}
                Domoticz.Device(Name="Heating Mode", Unit=8, TypeName="Selector Switch", Options=Options).Create()
                Domoticz.Device(Name="Heating", Unit=9, TypeName="Switch").Create()
            else:
                if (len(Devices) == 4):
                    Domoticz.Log("Devices missing")
                    Domoticz.Log("Add the additionnal devices")
                    status = self.getPoolConfig()
                    if str(status["PUMP1"]) == "1":
                        Domoticz.Device(Name="Pump 1", Unit=5, TypeName="Switch").Create()			
                    elif str(status["PUMP1"]) == "2":
                        Options = {"LevelActions": "|",
                                   "LevelNames": "Off|Low|High",
                                   "LevelOffHidden": "False",
                                   "SelectorStyle": "0"}
                        Domoticz.Device(Name="Pump 1", Unit=5, TypeName="Selector Switch", Options=Options).Create()
                    if str(status["PUMP2"]) == "1":
                        Domoticz.Device(Name="Pump 2", Unit=6, TypeName="Switch").Create()			
                    elif str(status["PUMP2"]) == "2":
                        Options = {"LevelActions": "|",
                                   "LevelNames": "Off|Low|High",
                                   "LevelOffHidden": "False",
                                   "SelectorStyle": "0"}
                        Domoticz.Device(Name="Pump 2", Unit=6, TypeName="Selector Switch", Options=Options).Create()
                    if str(status["BLOWER"]) == "1":
                        Domoticz.Device(Name="Blower", Unit=7, TypeName="Switch").Create()
                    Options = {"LevelActions": "|",
                               "LevelNames": "Ready|Rest",
                               "LevelOffHidden": "True",
                               "SelectorStyle": "0"}
                    Domoticz.Device(Name="Heating Mode", Unit=8, TypeName="Selector Switch", Options=Options).Create()
                    Domoticz.Device(Name="Heating", Unit=9, TypeName="Switch").Create()

            self.updateTemp()
            if Parameters["Mode6"] == "Debug":
               Domoticz.Debugging(1)
        except:
            Domoticz.Error("Failed to get config!")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if (Unit == 3):
          tempRange = self.toggleTempRange()
        
          if str(Command).lower() == "set level" and tempRange == "High":
              Devices[Unit].Update(1,str(10))
          else:
              Devices[Unit].Update(0,str(0))
        if (Unit == 4):
          light = self.toggleLights()
          #Devices[Unit].Update(Level, str(Command)


        #update to check the command effect
        self.updateTemp()


    def onHeartbeat(self):
        self.lastPolled = self.lastPolled + 1
        if (self.lastPolled > self.pollInterval): 
            self.lastPolled = 0
            self.updateTemp()

    def updateTemp(self):
        Domoticz.Log("Updating temperature now...")
        try:  
            status = self.getPoolStatus()
            Domoticz.Log("Get actual temp value: "+str(status["TEMP"]))
            if str(status["TEMP"]) != "0.0":
               Domoticz.Log("Temp known => device update")
               Devices[1].Update(nValue=1, sValue=str(status["TEMP"]), TimedOut=0)
            Devices[2].Update(nValue=1, sValue=str(status["SET_TEMP"]), TimedOut=0)
            if str(status["TEMP_RANGE"]) == "High" and Devices[3].nValue != 1:
                Devices[3].Update(1,str(10))
            elif str(status["TEMP_RANGE"]) == "Low" and Devices[3].nValue != 0:
                Devices[3].Update(0,str(0))
            if str(status["LIGHTS"]) == "Off" and Devices[4].nValue  != 0:
                Devices[4].Update(0, "Off")
            elif str(status["LIGHTS"]) == "On" and Devices[4].nValue != 1:
                Devices[4].Update(1, "On")
            if str(status["HEATING_MODE"]) == "Rest" and Devices[8].nValue != 1:
                Devices[8].Update(1,str(10))
            elif str(status["HEATING_MODE"]) == "Ready" and Devices[8].nValue != 0:
                Devices[8].Update(0,str(0))
            if str(status["HEATING"]) == "Off" and Devices[9].nValue  != 0:
                Devices[9].Update(0, "Off")
            elif str(status["HEATING"]) == "On" and Devices[9].nValue != 1:
                Devices[9].Update(1, "On")
            if str(status["PUMP1"]) == "Off" and Devices[5].nValue != 0:
                Devices[5].Update(0,str(0))
            elif str(status["PUMP1"]) == "Low" and Devices[5].nValue != 1:
                Devices[5].Update(1,str(10))
            elif str(status["PUMP1"]) == "High" and Devices[5].nValue != 2:
                Devices[5].Update(2,str(20))
            if str(status["PUMP2"]) == "Off" and Devices[6].nValue  != 0:
                Devices[6].Update(0, "Off")
            elif str(status["PUMP2"]) == "High" and Devices[6].nValue != 1:
                Devices[6].Update(1, "On")
            if str(status["BLOWER"]) == "Off" and Devices[7].nValue  != 0:
                Devices[7].Update(0, "Off")
            elif str(status["BLOWER"]) == "High" and Devices[7].nValue != 1:
                Devices[7].Update(1, "On")

        except:
            Domoticz.Error("Failed to update!")
            self.lastPolled = self.pollInterval

    def getPoolStatus(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" status", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = json.loads(proc.communicate()[0].decode('utf-8').strip())
            Domoticz.Log("Output: "+str(output))
        except ValueError as e:
            return ""
        return output

    def getPoolConfig(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" config", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = json.loads(proc.communicate()[0].decode('utf-8').strip())
            Domoticz.Log("Output: "+str(output))
        except ValueError as e:
            return ""
        return output

    def toggleTempRange(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" temprange", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = proc.communicate()[0].decode('utf-8').strip()
            Domoticz.Log("Output: "+str(output))
        except ValueError as e:
            return ""
        return output

    def toggleLights(self):
        try:
            proc = subprocess.Popen("python3 "+self.scriptPath+"/spaclient.py "+Parameters["Address"]+" lights", shell=True,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = proc.communicate()[0].decode('utf-8').strip()
            Domoticz.Log("Output: "+str(output))
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
