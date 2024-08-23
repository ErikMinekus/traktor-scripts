#!/usr/bin/env python3
"""
Export playlists to M3U files.
"""

import os
import sys
import xml.etree.ElementTree as ET


def main(inputFile, outputPath):
    collection = ET.parse(inputFile).getroot()

    for node in collection.iterfind('PLAYLISTS/NODE/SUBNODES/NODE'):
        processNode(node, outputPath)


def processNode(node, outputPath):
    nodeType = node.get('TYPE')
    nodeName = node.get('NAME')
    nodeOutputPath = os.path.join(outputPath, nodeName.replace(os.sep, '-'))

    if nodeType == 'FOLDER':
        if not os.path.exists(nodeOutputPath):
            os.mkdir(nodeOutputPath)

        for subnode in node.iterfind('SUBNODES/NODE'):
            processNode(subnode, nodeOutputPath)

    elif nodeType == 'PLAYLIST':
        if nodeName in ['_LOOPS', '_RECORDINGS']:
            return

        outputFile = nodeOutputPath + '.m3u'

        with open(outputFile, 'w') as file:
            for track in node.iterfind('PLAYLIST/ENTRY/PRIMARYKEY[@TYPE="TRACK"]'):
                path = track.get('KEY').replace('/:', os.sep)
                path = path if path[1] == ':' else os.path.join(os.sep, 'Volumes', path)

                file.write(path + '\n')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: playlist-export <input> <output>')
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
