#!/usr/bin/env python

import os, sys
import argparse
import cube


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

def generateConfig(micro, boardFile):
    print(micro.partNumber, boardFile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parsing a STM32CubeMX project file")
    parser.add_argument("--ioc", required=True, help="The file to convert")
    parser.add_argument("--cube", required=True, help="STM32CubeMX installation folder")
    parser.add_argument("--output", required=False, default='board.chcfg', help="The .chcfg file output")
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
    properties = loadIOC(args.ioc)
    try:
        partNo = properties['PCC.PartNumber']
        print(partNo)
        mcu = cube.MCU(partNo)
        mcu.updatePins(properties)

        generateConfig(mcu, args.output)
    except KeyError:
        print("Cannot find the MCU in the %s" % args.ioc)
