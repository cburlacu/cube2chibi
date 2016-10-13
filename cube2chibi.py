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

import os
import sys
import argparse
import cube
import chibi


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parsing a STM32CubeMX project file")
    parser.add_argument("--ioc", required=True, help="The file to convert")
    parser.add_argument("--cube", required=True, help="The STM32CubeMX installation folder")
    parser.add_argument("--output", required=False, default='board.chcfg', help="The .chcfg file output")
    parser.add_argument("--chibi", required=False, default=None, help="The .chcfg file input")
    args = parser.parse_args()
    cube.args = args
    print("Starting to parse %s" % args.ioc)
    # validate params
    if not os.path.isfile(args.ioc):
        print("File %s doesn't exist" % args.ioc)
        sys.exit(-2)
    if not os.path.isdir(args.cube):
        print("Folder %s doesn't exist" % args.cube)
        sys.exit(-3)
    properties = cube.loadIOC(args.ioc)
    partNo = None
    for key in ['PCC.PartNumber', 'Mcu.UserName']:
        try:
            partNo = properties[key]
            break
        except KeyError as ex:
            pass
    print(partNo)
    if partNo is not None:
        mcu = cube.getMCU(partNo)
        if mcu:
            mcu.updateProperties(properties)
            mcu.CubeFile = args.ioc
            chibi.generateConfig(mcu, args.chibi, args.output)
        else:
            print("Failed to load %s" % partNo)
    else:
        print("Failed to identify the part number in the specified file %s"
                % args.ioc)
