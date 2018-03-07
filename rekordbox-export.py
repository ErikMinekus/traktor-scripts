#!/usr/bin/env python3
"""
Export collection to rekordbox.xml file.
"""

from datetime import datetime
import sys
from urllib.request import quote
import xml.etree.ElementTree as ET


class NewCueType:
    Cue     = '0'
    FadeIn  = '1'
    FadeOut = '2'
    Load    = '3'
    Loop    = '4'


class OldCueType:
    Cue     = '0'
    FadeIn  = '1'
    FadeOut = '2'
    Load    = '3'
    Grid    = '4'
    Loop    = '5'


class PlaylistKeyType:
    TrackID  = '0'
    Location = '1'


class PlaylistType:
    Folder   = '0'
    Playlist = '1'


class CueMarker:
    def __init__(self, cue):
        self.Num  = cue.get('HOTCUE')
        self.Type = NewCueType.Cue

        name      = cue.get('NAME', '')
        self.Name = name if name not in ['AutoGrid', 'Beat Marker', 'n.n.'] else ''

        start      = float(cue.get('START'))
        self.Start = '{:.3f}'.format(start / 1000)

        if cue.get('TYPE') == OldCueType.Loop:
            end       = start + float(cue.get('LEN'))
            self.End  = '{:.3f}'.format(end / 1000)
            self.Type = NewCueType.Loop


class GridMarker:
    def __init__(self, cue, bpm):
        self.Battito = '1'
        self.Bpm     = '{:.2f}'.format(bpm)
        self.Inizio  = '{:.3f}'.format(float(cue.get('START')) / 1000)
        self.Metro   = '4/4'


class Track:
    def __init__(self, entry):
        album = entry.find('ALBUM')
        info  = entry.find('INFO')
        loc   = entry.find('LOCATION')
        tempo = entry.find('TEMPO')
        path  = loc.get('VOLUME') + loc.get('DIR').replace('/:', '/') + loc.get('FILE')
        # Fix POSIX path
        path  = path if path[1] == ':' else 'Volumes/' + path

        self.cueMarkers  = []
        self.gridMarkers = []
        self.pk          = loc.get('VOLUME') + loc.get('DIR') + loc.get('FILE')
        self.Name        = entry.get('TITLE', '')
        self.Artist      = entry.get('ARTIST', '')
        self.Location    = 'file://localhost/' + quote(path)

        if album is not None:
            self.Album       = album.get('TITLE', '')
            self.TrackNumber = album.get('TRACK', '0')
        if info is not None:
            importDateStr = info.get('IMPORT_DATE')
            importDate    = datetime.strptime(importDateStr, '%Y/%m/%d') if importDateStr is not None else datetime.today()

            self.Comments  = info.get('COMMENT', '')
            self.DateAdded = '{:%Y-%m-%d}'.format(importDate)
            self.Genre     = info.get('GENRE', '')
            self.Label     = info.get('LABEL', '')
            self.PlayCount = info.get('PLAYCOUNT', '0')
            self.Rating    = info.get('RANKING', '0')
            self.Remixer   = info.get('REMIXER', '')
            self.Size      = str(int(info.get('FILESIZE', 0)) * 1024)
            self.Tonality  = info.get('KEY', '')
            self.TotalTime = info.get('PLAYTIME', '0')
            self.Year      = info.get('RELEASE_DATE', '0').split('/')[0]
        if tempo is not None:
            self.AverageBpm = '{:.2f}'.format(float(tempo.get('BPM', 0)))

        for cue in entry.iterfind('CUE_V2'):
            if cue.get('TYPE') == OldCueType.Grid:
                self.gridMarkers.append(GridMarker(cue, float(tempo.get('BPM', 0))))

                # Store Grid Marker as Hot Cue
                if cue.get('HOTCUE') != '-1':
                    self.cueMarkers.append(CueMarker(cue))
            else:
                self.cueMarkers.append(CueMarker(cue))


def parsePlaylistNode(parent, node, tracks):
    name = node.get('NAME')
    name = name if name != '$ROOT' else 'ROOT'

    folder = ET.SubElement(parent, 'NODE', Name=name, Type=PlaylistType.Folder)
    count  = 0

    for subnode in node.iterfind('SUBNODES/NODE'):
        if subnode.get('TYPE') == 'FOLDER':
            parsePlaylistNode(folder, subnode, tracks)
        else:
            name = subnode.get('NAME')
            if name in ['_LOOPS', '_RECORDINGS']:
                continue

            playlist = ET.SubElement(folder, 'NODE', Name=name, KeyType=PlaylistKeyType.Location, Type=PlaylistType.Playlist)
            entries  = 0

            for track in subnode.iterfind('PLAYLIST/ENTRY/PRIMARYKEY[@TYPE="TRACK"]'):
                ET.SubElement(playlist, 'TRACK', Key=tracks[track.get('KEY')].Location)
                entries += 1

            playlist.set('Entries', str(entries))

        count += 1

    folder.set('Count', str(count))


def main(inputFile, outputFile):
    traktor   = ET.parse(inputFile).getroot()
    rekordbox = ET.Element('DJ_PLAYLISTS', Version='1.0.0')

    ET.SubElement(rekordbox, 'PRODUCT', Company='Erik Minekus', Name='traktor-rekordbox-export', Version='1.0.0')

    collection = ET.SubElement(rekordbox, 'COLLECTION')
    playlists  = ET.SubElement(rekordbox, 'PLAYLISTS')
    tracks     = {}

    for entry in traktor.iterfind('COLLECTION/ENTRY'):
        track = Track(entry)
        tracks[track.pk] = track

        attrs = {key: value for key, value in track.__dict__.items() if key not in ['cueMarkers', 'gridMarkers', 'pk']}
        elem  = ET.SubElement(collection, 'TRACK', attrs)

        for cueMarker in track.cueMarkers:
            ET.SubElement(elem, 'POSITION_MARK', cueMarker.__dict__)

            # Duplicate Hot Cue as Memory Cue
            if cueMarker.Num != '-1':
                ET.SubElement(elem, 'POSITION_MARK', cueMarker.__dict__, Num='-1')

        for gridMarker in track.gridMarkers:
            ET.SubElement(elem, 'TEMPO', gridMarker.__dict__)

    collection.set('Entries', str(len(tracks)))

    parsePlaylistNode(playlists, traktor.find('PLAYLISTS/NODE'), tracks)

    ET.ElementTree(rekordbox).write(outputFile, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: rekordbox-export <input> <output>')
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
