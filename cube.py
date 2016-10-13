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
args = None

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
                if m and m.groups() >= 1:
                    self.Mode = 'Alternate'
                    self.Alternate = m.group(1)
                    # print(signal, self.Mode, self.Alternate)
                else:
                    print ("Failed to read %s" % signal)
            else:
                print("Failed: %s" % signal, self.CName, self.Pin)
        else:
            print "Invalid description - %s / %s " % (self.Pin, signal)

        return mode

    def update(self, prop, value):
        if prop == 'GPIO_Label':
            self.ID = value
        elif prop == 'GPIO_PuPd':
            self.Resistor = getValue(_resistor, value, "Floating")
        elif prop == 'GPIO_Speed':
            self.Speed = getValue(_speed, value, "Maximum")
        elif prop == 'Signal':
            self.SignalName = value
            self.Mode = self.getModeFromSignal(value)
        elif prop == 'Mode':
            self.ModeCube = value  # the mode will be updated when signal is set
        elif prop == 'PinState':
            self.Level = getValue(_level, value, "Low")
        elif prop == 'GPIO_ModeDefaultOutputPP':
            self.Type = getValue(_type, value, "PushPull")
        else:
            pass
            # print("Property %s is not used" % prop)

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

    def __init__(self):
        pass

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
                # elif key == '':
        print("%s properties of %d GPIOs were updated from CubeMX project" %
              (count, len(dummy)))

    def __str__(self):
        return "MCU: %s\nName: %s" % (self.partNumber, self.name)


def _load_(partNo):
    mcu = MCU()
    mcu.partNumber = partNo

    print("Loading %s" % mcu.partNumber)
    try:
        root, ns = getRoot(args.cube + MCU_FAMILIES_PATH)
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
        mcuDesc, ns = getRoot(args.cube + MCU_PATH + mcu.name + ".xml")
        gpioIp = getElems(mcuDesc, "IP[@Name='GPIO']", ns)
        if len(gpioIp) == 1:
            gpioVersion = gpioIp[0].attrib['Version']
            print("GPIO version is '%s'" % gpioVersion)
            gpioDesc, gns = getRoot(args.cube + IP_PATH + ("GPIO-%s_Modes.xml" % gpioVersion))
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

