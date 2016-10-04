#!/usr/bin/env python
import sys
import xml.etree.ElementTree as et
import re

MCU_PATH = '/db/mcu/'
IP_PATH = '/db/mcu/IP/'
MCU_FAMILIES_PATH = '/db/mcu/families.xml'
args = None


def getRoot(fileName):
    try:
        print("Loading %s" % fileName)
        root = et.parse(fileName).getroot()
        m = re.match('\{.*\}', root.tag)
        return root, m.group(0) if m else ''
    except Exception as ex:
        print("Failed to load %s - %s" % (fileName, ex))
        return None, None


def getElems(elem, xpath, ns):
    xpath = xpath.format(ns)
    xpathExpr = ".//%s%s" % (ns, xpath)
    return elem.findall(xpathExpr)

def getElem(elem, xpath, ns):
    xpath = xpath.format(ns)
    xpathExpr = ".//%s%s" % (ns, xpath)
    return elem.find(xpathExpr)


def getValue(properties, key, default):
    if key in properties:
        return properties[key]
    else:
        return default


class Pin:
    pinNo = -1
    Pin = "N/A"
    SignalName = ""
    ID = ""
    Type = "PushPull"
    Level = "High"
    Speed = "Maximum"
    Resistor = "Floating"
    Mode = "Input"
    ModeCube = "N/A"
    Alternate = 0
    _gpioDesc = None
    _gpioNs = ''

    __resistor = {
        'GPIO_PULLUP': 'PullUp',
        'GPIO_PULLDOWN': 'PullDown',
    }

    __speed = {
        'GPIO_SPEED_FREQ_LOW': 'Minimum',
        'GPIO_SPEED_FREQ_MEDIUM': 'Low',
        'GPIO_SPEED_FREQ_HIGH': 'High',
        'GPIO_SPEED_FREQ_VERY_HIGH': 'Maximum',
    }

    # by default CubeMX is setting the GPIO as low
    __level = {
        'PinState': 'GPIO_PIN_SET',
    }

    __signal = {
        r'GPIO_Input': 'Input',
        r'GPIO_Output': 'Output',
        r'ADC[0-9x]+_IN[0-9]+': 'Analog',
        r'IN[0-9]{1,2}': 'Analog'
    }

    def __init__(self):
        pass

    def getModeFromSignal(self, signal):
        mode = None

        for key in self.__signal:
            if re.match(key, signal):
                mode = self.__signal[key]
                return mode
        # find alternate function
        if self._gpioDesc is not None:
            pinSignal = getElem(self._gpioDesc, "PinSignal[@Name='%s']//{0}PossibleValue" % signal, self._gpioNs)
            if pinSignal is not None:
                print ("Success for %s" % pinSignal.text)
                expr = r'GPIO_AF([0-9]{1,2}).*'
                m = re.match(expr, pinSignal.text)
                if m and m.groups() >= 1:
                    self.Mode = 'Alternate'
                    self.Alternate = int(m.group(1))
                    print(signal, self.Mode, self.Alternate)
                else:
                    print ("Failed to read %s" % signal)
            else:
                print("Failed: %s" % signal)
        else:
            print "Invalid description - %s / %s " % (self.Pin, signal)

        return mode

    def update(self, prop, value):
        if prop == 'GPIO_Label':
            self.ID = value
        elif prop == 'GPIO_PuPd':
            self.Resistor = getValue(self.__resistor, value, "Floating")
        elif prop == 'GPIO_Speed':
            self.Speed = getValue(self.__speed, value, "Maximum")
        elif prop == 'Signal':
            self.SignalName = value
            self.Mode = self.getModeFromSignal(value)
        elif prop == 'Mode':
            self.ModeCube = value  # the mode will be updated when signal is set
        elif prop == 'PinState':
            self.Level = getValue(self.__level, value, "Low")
        else:
            pass
            # print("Property %s is not used" % prop)

    def __str__(self):
        return"Pin: %s, %s, %s, %s, %s" % (self.Pin, self.SignalName, self.Mode, self.Speed, self.Resistor)


class MCU:
    partNumber = None
    name = ""
    pins = {}
    gpiosDesc = None

    def __load__(self, partNo):
        self.partNumber = partNo

        print("Loading %s" % self.partNumber)
        try:
            root, ns = getRoot(args.cube + MCU_FAMILIES_PATH)
            elems = getElems(root, "Mcu[@RefName='%s']" % self.partNumber, ns)
            if len(elems) != 1:
                print("Cannot identify the MCU (%s)" % self.partNumber)
                sys.exit(-4)
            mcu = elems[0]
            self.name = mcu.attrib['Name']
            mcuDesc, ns = getRoot(args.cube + MCU_PATH + self.name + ".xml")
            gpioIp = getElems(mcuDesc, "IP[@Name='GPIO']", ns)
            if len(gpioIp) == 1:
                gpioVersion = gpioIp[0].attrib['Version']
                print(gpioVersion)
                gpioDesc, gns = getRoot(args.cube + IP_PATH + ("GPIO-%s_Modes.xml" % gpioVersion))
                self.gpiosDesc = getElems(gpioDesc, "GPIO_Pin", gns)
                # print(self.gpiosDesc)
            else:
                print ("Invalid GPIO description")
            pinsDesc = getElems(mcuDesc, "Pin", ns)
            print(len(pinsDesc))
            count = 0
            alreadyExists = 0
            for pinDesc in pinsDesc:
                pin = Pin()
                pin.pinNo = int(pinDesc.attrib['Position'])
                pin.Pin = pinDesc.attrib['Name']
                pinDescs = [i for i in self.gpiosDesc if i.attrib['Name'] == pin.Pin]
                pin._gpioDesc = pinDescs[0] if len(pinDescs) >= 1 else None
                pin._gpioNs = gns

                # print(pin.Pin)
                if pin.Pin in self.pins:
                    # print("%s - already exists" % pin.Pin)
                    alreadyExists += 1
                self.pins[pin.Pin] = pin
                count += 1
            print("%s has %d pins (%d) (%d duplicates)" % (self.partNumber, len(self.pins), count, alreadyExists))
        except Exception as xxx:
            self.partNumber = None
            self.name = None
            print("Failed to load %s because of %s" % (self.partNumber, xxx))

    def __init__(self, partNo):
        self.__load__(partNo)

    def updatePins(self, props):
        count = 0
        for key in props:
            m = re.match(r'(P[A-K][0-9]+)\.(.*)', key, flags=re.IGNORECASE)
            if m and len(m.groups()) == 2:
                gpioName = m.group(1)
                gpioProp = m.group(2)
                pin = self.pins[gpioName] if gpioName in self.pins else None
                if pin is not None:
                    pin.update(gpioProp, props[key])
                    count += 1
                else:
                    print("%s was not found in pins??" % gpioName)
        #     else:
        #         print("%s is not a GPIO" % key)
        print("%s GPIOs updated from CubeMX project" % count)

    def __str__(self):
        return "MCU: %s\nName: %s" % (self.partNumber, self.name)