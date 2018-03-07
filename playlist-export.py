#!/usr/bin/env python3
"""
Export playlists to M3U files.
"""

import os.path
import sys
import xml.etree.ElementTree as ET


def main(inputFile, outputPath):
    traktor = ET.parse(inputFile).getroot()

    for node in traktor.iterfind('PLAYLISTS/NODE/SUBNODES/NODE[@TYPE="PLAYLIST"]'):
        name = node.get('NAME')
        if name in ['_LOOPS', '_RECORDINGS']:
            continue

        outputFile = os.path.join(outputPath, name.replace(os.sep, '-') + '.m3u')

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
