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
    All ChibiOS related stuff
"""

from utils import *


# chibi configuration file tags
ct = {
    'root': 'board',
    'conf': 'configuration_settings',
    'template': 'templates_path',
    'out' : 'output_path',
    'hal' : 'hal_version',
    'name' : 'board_name',
    'board_id': 'board_id',
    'subtype': 'subtype',
    'clock': 'clocks',
    'ports': 'ports',
    'func': 'board_functions',
    'hse': 'HSEFrequency',
    'lse': 'LSEFrequency',
    'hseBy': 'HSEBypass',
    'lseBy': 'LSEBypass',
    'vdd': 'VDD',
    'pId': 'ID',
    'pType': 'Type',
    'pLevel': 'Level',
    'pSpeed': 'Speed',
    'pRes': 'Resistor',
    'pMode': 'Mode',
    'pAlt': 'Alternate',
    'lseDrive': 'LSEDrive',
    'gpSw': 'AnalogSwitch',
    'gpLck': 'PinLock',
}

# chibi gpio pin configuration default values
chdef = {
    'Type': 'PushPull',
    'Level': 'High',
    'Speed': 'Maximum',
    'Resistor': 'Floating',
    'Mode': 'Input',
    'Alternate': '0',
    'HSEFrequency': '8000000',
    'LSEFrequency': '32768',
    'HSEBypass': 'false',
    'LSEBypass': 'false',
    'VDD': '330',
    'Family': 'STM32F4xx',
    'AnalogSwitch': 'Disabled',
    'PinLock': 'Disabled',

}

# template location per family
chTemplates = {
    'STM32F0xx': 'resources/gencfg/processors/boards/stm32f0xx/templates',
    'STM32F3xx': 'resources/gencfg/processors/boards/stm32f3xx/templates',
    'STM32F4xx': 'resources/gencfg/processors/boards/stm32f4xx/templates',
    'STM32F2xx': 'resources/gencfg/processors/boards/stm32f4xx/templates',
    'STM32F7xx': 'resources/gencfg/processors/boards/stm32f7xx/templates',
    'STM32L0xx': 'resources/gencfg/processors/boards/stm32l0xx/templates',
    'STM32L1xx': 'resources/gencfg/processors/boards/stm32l1xx/templates',
    'STM32L4xx': 'resources/gencfg/processors/boards/stm32l4xx/templates',
    # 'STM32Fxxx': '',
}

# LSEDrive per family
chLseDriveDefault = {
    'STM32F0xx': '3 High Drive (default)',
    'STM32F3xx': '3 High Drive (default)',
    'STM32F4xx': '',
    'STM32F2xx': '',
    'STM32F7xx': '',
    'STM32L0xx': '3 High Drive (default)',
    'STM32L1xx': '',
    'STM32L4xx': '3 High Drive (default)',
}

# GPIO version per family
chGpioVersion = {
    'STM32F0xx': '2',
    'STM32F3xx': '2',
    'STM32F4xx': '2',
    'STM32F2xx': '2',
    'STM32F7xx': '2',
    'STM32L0xx': '2',
    'STM32L1xx': '2',
    'STM32L4xx': '3',
}

# XML schema location per family
chSchema = {
    'STM32F0xx': 'http://www.chibios.org/xml/schema/boards/stm32f0xx_board.xsd',
    'STM32F3xx': 'http://www.chibios.org/xml/schema/boards/stm32f3xx_board.xsd',
    'STM32F4xx': 'http://www.chibios.org/xml/schema/boards/stm32f4xx_board.xsd',
    'STM32F2xx': 'http://www.chibios.org/xml/schema/boards/stm32f4xx_board.xsd',
    'STM32F7xx': 'http://www.chibios.org/xml/schema/boards/stm32f7xx_board.xsd',
    'STM32L0xx': 'http://www.chibios.org/xml/schema/boards/stm32l0xx_board.xsd',
    'STM32L1xx': 'http://www.chibios.org/xml/schema/boards/stm32l1xx_board.xsd',
    'STM32L4xx': 'http://www.chibios.org/xml/schema/boards/stm32l4xx_board.xsd',
}


def getFamily(micro):
    return micro.Family if not isEmpty(micro.Family) and micro.Family in chTemplates else chdef['Family']


def getValue(dictionary, key, newValue, default=""):
    if isEmpty(default):
        default = chdef[key] if key in chdef else default

    try:
        oldValue = dictionary[key]
    except (KeyError, TypeError) as ex:
        oldValue = None

    if not isEmpty(newValue):
        return newValue
    elif not isEmpty(oldValue):
        return oldValue
    else:
        return default


def make_id(str):
    validChars = []
    validChars += map(chr, xrange(48, 58))
    validChars += map(chr, xrange(65, 91))
    validChars += map(chr, xrange(97, 123))
    validChars += chr(95)
    retVal = ""
    for ch in str:
        retVal += ch if ch in validChars else '_'

    return retVal


def updatePinElem(pinElem, pinObj):
    if pinElem is not None and pinObj is not None:

        pinElem.attrib[ct['pId']] = make_id(getValue(pinElem.attrib, ct['pId'], pinObj.ID))
        pinElem.attrib[ct['pType']] = getValue(pinElem.attrib, ct['pType'], pinObj.Type)
        pinElem.attrib[ct['pLevel']] = getValue(pinElem.attrib, ct['pLevel'], pinObj.Level)
        pinElem.attrib[ct['pSpeed']] = getValue(pinElem.attrib, ct['pSpeed'], pinObj.Speed)
        pinElem.attrib[ct['pRes']] = getValue(pinElem.attrib, ct['pRes'], pinObj.Resistor)
        pinElem.attrib[ct['pMode']] = getValue(pinElem.attrib, ct['pMode'], pinObj.Mode)
        pinElem.attrib[ct['pAlt']] = getValue(pinElem.attrib, ct['pAlt'], pinObj.Alternate)

        try:
            family = getFamily(pinObj.parent)
            if chGpioVersion[family] == '3':
                pinElem.attrib[ct['gpSw']] = getValue(pinElem.attrib, ct['gpSw'], pinObj.AnalogSwitch)
                pinElem.attrib[ct['gpLck']] = getValue(pinElem.attrib, ct['gpLck'], pinObj.AnalogSwitch)
        except:
            pass


def generateConfig(micro, boardIn, boardOut):
    print("Start generatig chibi file for %s" % micro)
    parser = et.XMLParser()
    family = getFamily(micro)
    oldRoot, ns = getRoot(boardIn, parser)

    boardNs = 'http://www.w3.org/2001/XMLSchema-instance'

    # set namespace
    root = et.Element(ct['root'], nsmap={'xsi': boardNs})
    root.attrib["{%s}noNamespaceSchemaLocation" % boardNs] = chSchema[family]

    # set root element to the tree - used to write
    tree = et.ElementTree(root)

    # configuration settings - don't bother if this doesn't exists
    # just insert empty ones - basically it extract the nodes from old xml
    # and add them to the new one
    confElem = getOrCreateElem(oldRoot, ct['conf'], ct['conf'], ns)
    elem = getOrCreateElem(confElem, ct['template'], ct['template'], ns)
    elem.text = chTemplates[family]
    print elem.text
    print family
    confElem.append(elem)

    elem = getOrCreateElem(oldRoot, ct['out'], ct['out'], ns)
    elem.text = getValue(None, None, elem.text, '..')
    confElem.append(elem)

    elem = getOrCreateElem(oldRoot, ct['hal'], ct['hal'], ns)
    elem.text = getValue(None, None, elem.text, '3.0.x')
    confElem.append(elem)
    root.append(confElem)

    # board name
    elem = getOrCreateElem(oldRoot, ct['name'], ct['name'], ns)
    elem.text = getValue(None, None, elem.text, 'Custom board')
    root.append(elem)

    # board id
    elem = getOrCreateElem(oldRoot, ct['board_id'], ct['board_id'], ns)
    elem.text = getValue(None, None, elem.text, 'CUSTOM_BOARD')
    root.append(elem)

    # board functions
    elem = getOrCreateElem(oldRoot, ct['func'], ct['func'], ns)
    elem.text = getValue(None, None, elem.text, '')
    root.append(elem)

    # subtype
    elem = getOrCreateElem(oldRoot, ct['subtype'], ct['subtype'], ns)
    elem.text = getValue(None, None, elem.text, family)
    root.append(elem)

    # clock
    elem = getOrCreateElem(oldRoot, ct['clock'], ct['clock'], ns)
    # HSE
    elem.attrib[ct['hse']] = getValue(elem.attrib, ct['hse'], micro.HSEClock)
    elem.attrib[ct['hseBy']] = getValue(elem.attrib, ct['hseBy'], micro.HSEClock)
    # LSE
    elem.attrib[ct['lse']] = getValue(elem.attrib, ct['lse'], micro.LSEClock)
    elem.attrib[ct['lseBy']] = getValue(elem.attrib, ct['lseBy'], micro.LSEClock)
    if not isEmpty(chLseDriveDefault[family]):
        elem.attrib[ct['lseDrive']] = chLseDriveDefault[family]
    # VDD voltage
    elem.attrib[ct['vdd']] = getValue(elem.attrib, ct['vdd'], micro.VDD)

    root.append(elem)

    # iterate all possible ports
    portsElem = et.Element(ct['ports'])
    root.append(portsElem)
    for port in sorted(micro.ports.keys()):
        chibiPort = "GPIO{0}".format(port)
        portElem = et.Element(chibiPort)
        portsElem.append(portElem)
        for pin in sorted(micro.ports[port]):
            pinName = getPinName(port, pin)
            pinObj = micro.pins[pinName]
            chibiPin = "pin{0}".format(pin)
            pinElem = getOrCreateElem(oldRoot, "{0}/{1}/{2}".format(ct['ports'], chibiPort, chibiPin), chibiPin, ns)
            updatePinElem(pinElem, pinObj)
            portElem.append(pinElem)

    print("Writing the results in '%s'" % boardOut)

    try:
        tree.write(boardOut, encoding='utf-8', xml_declaration=True, pretty_print=True)
    except Exception as ex:
        print("Failed to save the result:", ex)


