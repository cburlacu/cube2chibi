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
    Misc
"""

import lxml.etree as et
import re

PORT_REGEX = "^P([A-K])([0-9]{1,2})"
MAX_PINS_PER_PORT = 16


def getPortInfo(name):
    m = re.match(PORT_REGEX, name)
    if m is None:
        return None, None
    else:
        return m.group(1), int(m.group(2))


def getPinName(port, pinNo):
    if port is None or pinNo is None:
        return None
    return "{0}{1}".format(port, pinNo)


def getRoot(fileName, parser=None):
    try:
        print("Loading %s" % fileName)
        root = et.parse(fileName, parser).getroot()
        m = re.match('\{.*\}', root.tag)
        return root, m.group(0) if m else ''
    except (OSError, IOError) as ex:
        print("Failed to load %s - %s\n"
              "Is the path right - %s - ?" % (fileName, ex, fileName))
        return et.Element('empty'), ''


def getElems(parent, xpath, ns):
    xpath = xpath.format(ns)
    xpathExpr = ".//%s%s" % (ns, xpath)
    return parent.findall(xpathExpr)


def getElem(parent, xpath, ns):
    if parent is None:
        return None
    xpath = xpath.format(ns)
    xpathExpr = ".//%s%s" % (ns, xpath)
    elem = None
    try:
        elem = parent.find(xpathExpr)
    except Exception as ex:
        print ex
    return elem


def getOrCreateElem(parent, xpath, tag, ns):
    elem = getElem(parent, xpath, ns)
    if elem is None:
        elem = et.Element(tag)
    # just don't care to duplicate the nodes
    # input file won't be saved
    # else:
    #     elem = elem.__copy__()

    return elem


def isEmpty(s):
    return not bool(s and s.strip())