#!/usr/bin/env python

# Copyright (C) Cezar Burlacu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    All CubeMX parsing and the "models: mcu, pin"
"""

import sys
from utils import *
from collections import defaultdict

MCU_PATH = '/db/mcu/'
IP_PATH = '/db/mcu/IP/'
MCU_FAMILIES_PATH = '/db/mcu/families.xml'
CUBE_PATH = None

_resistor = {
    'GPIO_PULLUP': 'PullUp',
    'GPIO_PULLDOWN': 'PullDown',
    'GPIO_NOPULL': 'Floating'
}

_speed = {
    'GPIO_SPEED_FREQ_LOW': 'Minimum',
    'GPIO_SPEED_FREQ_MEDIUM': 'Low',
    'GPIO_SPEED_FREQ_HIGH': 'High',
    'GPIO_SPEED_FREQ_VERY_HIGH': 'Maximum',
}

# by default CubeMX is setting the GPIO as low
_level = {
    'GPIO_PIN_SET': 'High',
    'GPIO_PIN_RESET': 'Low',
}

_signal = {
    r'GPIO_Input': 'Input',
    r'GPIO_Output': 'Output',
    r'ADC[0-9x]+_IN[0-9]+': 'Analog',
    r'IN[0-9]{1,2}': 'Analog'
}

_type = {
    'GPIO_MODE_OUTPUT_OD': 'OpenDrain',
    'GPIO_MODE_OUTPUT_PP': 'PushPull'
}

_defaultValues = {}


def getChibiValue(prop, cube2ch, cube):
    if cube in cube2ch:
        return cube2ch[cube]
    elif prop in _defaultValues:
        if _defaultValues[prop] in cube2ch:
            return cube2ch[_defaultValues[prop]]
    return None


class Pin:
    pinNo = -1
    CName = "N/A"  # cube mx name
    Pin = "N/A"
    SignalName = None
    AnalogSwitch = None
    PinLocked = None
    ID = None
    Type = None
    Level = None
    Speed = None
    Resistor = None
    Mode = None
    ModeCube = None
    Alternate = None
    _gpioDesc = None
    _gpioNs = ''
    parent = None

    def __init__(self):
        pass

    def getModeFromSignal(self, signal):
        mode = "Input"

        for key in _signal:
            if re.match(key, signal):
                mode = _signal[key]
                return mode
        # find alternate function
        if self._gpioDesc is not None:
            pinSignal = getElem(self._gpioDesc, "PinSignal[@Name='%s']//{0}PossibleValue" % signal, self._gpioNs)
            if pinSignal is not None:
                # print ("Success for %s" % pinSignal.text)
                expr = r'GPIO_AF([0-9]{1,2}).*'
                m = re.match(expr, pinSignal.text)
                if m and len(m.groups()) >= 1:
                    self.Mode = 'Alternate'
                    self.Alternate = m.group(1)
                    # print(signal, self.Mode, self.Alternate)
                else:
                    print("Failed to read %s" % signal)
            else:
                print("Failed: %s" % signal, self.CName, self.Pin)
        else:
            print("Invalid description - %s / %s " % (self.Pin, signal))

        return mode

    def update(self, prop, value):
        updated = False
        if prop == 'GPIO_Label':
            self.ID = value
            updated = True
        elif prop == 'GPIO_PuPd':
            self.Resistor = getChibiValue(prop, _resistor, value)
            updated = True
        elif prop == 'GPIO_Speed':
            self.Speed = getChibiValue(prop, _speed, value)
            updated = True
        elif prop == 'Signal':
            self.SignalName = value
            self.Mode = self.getModeFromSignal(value)
            updated = True
        elif prop == 'Mode':
            self.ModeCube = value  # the mode will be updated when signal is set
            updated = True
        elif prop == 'PinState':
            self.Level = getChibiValue(prop, _level, value)
            updated = True
        elif prop == 'GPIO_ModeDefaultOutputPP':
            self.Type = getChibiValue(prop, _type, value)
            updated = True
        else:
            print("{0}: property {1} is not used? {2}".format(self.CName, prop, value))

        # load all default values for a Pin that is defined in Cube project
        # in this way, all default Chibi properties should be overridden
        if updated:
            self.loadDefaults()

    # Load default value ONLY if is not loaded yet
    # these default values are default in CubeMX
    def loadDefaults(self):
        emptyDict = {}
        self.ID = '' if self.ID is None else self.ID
        self.Resistor = getChibiValue('GPIO_PuPd', _resistor, 'N/A') if self.Resistor is None else self.Resistor
        self.Speed = getChibiValue('GPIO_Speed', _speed, 'N/A') if self.Speed is None else self.Speed
        self.Mode = 'Input' if self.Mode is None else self.Mode
        self.Level = getChibiValue('PinState', _level, 'N/A') if self.Level is None else self.Level
        self.Type = getChibiValue('GPIO_ModeDefaultOutputPP', _type, 'N/A') if self.Type is None else self.Type
        self.Alternate = '0' if self.Alternate is None else self.Alternate

    def __str__(self):
        return"Pin: %s, %s, %s, %s, %s" % (self.Pin, self.SignalName, self.Mode, self.Speed, self.Resistor)


class MCU:
    partNumber = None
    name = ""
    pins = {}
    ports = defaultdict(list)
    gpiosDesc = None
    HSEClock = None
    LSEClock = None
    VDD = None
    Family = None
    CubeFile = ""

    def __init__(self, partNo):
        self.partNumber = partNo
        self.name = ""
        self.pins = {}
        self.ports = defaultdict(list)
        self.gpiosDesc = None
        self.HSEClock = None
        self.LSEClock = None
        self.VDD = None
        self.Family = None
        self.CubeFile = ""

    def updateProperties(self, props):
        count = 0
        dummy = {}
        for key in props:
            processed = False
            m = re.match(r'(P[A-K][0-9]{1,2})\.(.*)', key, flags=re.IGNORECASE)
            if m and len(m.groups()) == 2:
                gpioName = m.group(1)
                gpioProp = m.group(2)
                port, pin = getPortInfo(gpioName)
                pinName = getPinName(port, pin)
                pin = self.pins[pinName] if pinName in self.pins else None
                if pin is not None:
                    dummy[pin.Pin] = "dummy"
                    pin.update(gpioProp, props[key])
                    count += 1
                else:
                    print("%s was not found in pins??" % gpioName)

        #     else:
        #         print("%s is not a GPIO" % key)
            if not processed:  # try RCC - clocks
                if key == 'RCC.HSE_VALUE':
                    self.HSEClock = props[key]
                elif key == 'PCC.Vdd':
                    try:
                        vdd = float(props[key]) * 100
                        self.VDD = str(int(vdd))
                    except:
                        pass
                elif key == 'RCC.LSE_VALUE':
                    self.LSEClock = props[key]
                # elif key == '':
                # elif key == '':
        print("%s properties of %d GPIOs were updated from CubeMX project" %
              (count, len(dummy)))

    def __str__(self):
        return "MCU: %s\nName: %s" % (self.partNumber, self.name)


def getDefaultValue(parent, ns, refName):
    retVal = None
    elem = getElem(parent, "RefParameter[@Name='%s']" % refName, ns)
    if elem is not None and 'DefaultValue' in elem.attrib:
        retVal = elem.attrib['DefaultValue']

    return retVal


def loadDefaultValues(gpio, ns):
    retVal = {}

    val = getDefaultValue(gpio, ns, 'PinState')
    if val is not None:
        retVal['PinState'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_ModeDefaultOutputPP')
    if val is not None:
        retVal['GPIO_ModeDefaultOutputPP'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_Speed')
    if val is not None:
        retVal['GPIO_Speed'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_PuPd')
    if val is not None:
        retVal['GPIO_PuPd'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_ModeDefaultPP')
    if val is not None:
        retVal['GPIO_ModeDefaultPP'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_ModeDefaultOutputPP')
    if val is not None:
        retVal['GPIO_ModeDefaultOutputPP'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_ModeDefaultEXTI')
    if val is not None:
        retVal['GPIO_ModeDefaultEXTI'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_AF')
    if val is not None:
        retVal['GPIO_AF'] = val

    val = getDefaultValue(gpio, ns, 'GPIO_Speed_High_Default')
    if val is not None:
        retVal['GPIO_Speed_High_Default'] = val

    return retVal


def _load_(partNo):
    mcu = MCU(partNo)

    print("Loading %s" % mcu.partNumber)
    try:
        root, ns = getRoot(CUBE_PATH + MCU_FAMILIES_PATH)
        if root is None or ns is None:
            return None
        elems = getElems(root, "Mcu[@RefName='%s']" % mcu.partNumber, ns)
        if elems is None or len(elems) != 1:
            print("Cannot identify the MCU (%s)" % mcu.partNumber)
            sys.exit(-4)
        mcuDesc = elems[0]
        try:
            mcu.Family = mcuDesc.getparent().getparent().attrib['Name'] + 'xx'
        except:
            pass

        mcu.name = mcuDesc.attrib['Name']
        mcuDesc, ns = getRoot(CUBE_PATH + MCU_PATH + mcu.name + ".xml")
        gpioIp = getElems(mcuDesc, "IP[@Name='GPIO']", ns)
        if len(gpioIp) == 1:
            gpioVersion = gpioIp[0].attrib['Version']
            print("GPIO version is '%s'" % gpioVersion)
            gpioDesc, gns = getRoot(CUBE_PATH + IP_PATH + ("GPIO-%s_Modes.xml" % gpioVersion))
            global _defaultValues
            _defaultValues = loadDefaultValues(gpioDesc, gns)
            mcu.gpiosDesc = getElems(gpioDesc, "GPIO_Pin", gns)
            # print(self.gpiosDesc)
        else:
            print ("Invalid GPIO description")
        pinsDesc = getElems(mcuDesc, "Pin", ns)
        print("%s has %d pins" % (partNo, len(pinsDesc)))
        count = 0
        alreadyExists = 0
        duplicates = {}
        for pinDesc in pinsDesc:
            pin = Pin()
            pin.parent = mcu
            pin.pinNo = pinDesc.attrib['Position']
            pin.CName = pinDesc.attrib['Name']
            port, pinNo = getPortInfo(pin.CName)
            pinName = getPinName(port, pinNo)
            pin.Pin = pinName if not isEmpty(pinName) else pin.CName

            # find gpio description from gpio-xxx_modes.xml
            gpio_desc = [i for i in mcu.gpiosDesc if
                        i.attrib['Name'] == pin.CName]
            pin._gpioDesc = gpio_desc[0] if len(gpio_desc) >= 1 else None

            pin._gpioNs = gns

            if pin.Pin in mcu.pins:
                alreadyExists += 1
                duplicates[pin.Pin] = "dummy"
            mcu.pins[pin.Pin] = pin
            count += 1

            if port is not None and pinNo is not None:
                mcu.ports[port].append(pinNo)

        print("%s has %d pins (%d) (%d duplicates - %s)" % (
            mcu.partNumber, len(mcu.pins), count, alreadyExists, str(duplicates.keys())))
    except KeyError as xxx:
        mcu = None
        print("Failed to load %s because of %s" % (partNo, xxx))

    return mcu


def getMCU(partNo):
    mcu = _load_(partNo)
    return mcu


def loadIOC(filename):
    lines = {}
    with open(filename) as f:
        while True:
            line = f.readline().strip()
            if not line:
                break
            if line[0] == '#':
                continue
            # print(line)
            vals = line.split('=', 2)
            key = vals[0]
            value = vals[1]
            lines[key] = value

    return lines

