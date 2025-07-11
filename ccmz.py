import zipfile
import json
import io
import requests
from midiutil.MidiFile import MIDIFile
import os

class CCMZ:
    def __init__(self):
        self.ver = None
        self.score = None
        self.midi = None

class LibCCMZ:
    @staticmethod
    def download_ccmz(url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            raise Exception(f"下载失败: {response.status_code}")
        except Exception as e:
            print(f"ccmz文件下载失败: {e}")
            return None

    @staticmethod
    def read_ccmz(buffer, callback):
        info = CCMZ()
        version = buffer[0]
        info.ver = version
        data = buffer[1:]

        if version == 1:
            zip_file = zipfile.ZipFile(io.BytesIO(data))
            info.score = zip_file.read("data.xml").decode('utf-8')
            info.midi = zip_file.read("data.mid").decode('utf-8')
        elif version == 2:
            data = bytes([v + 1 if v % 2 == 0 else v - 1 for v in data])
            zip_file = zipfile.ZipFile(io.BytesIO(data))
            info.score = zip_file.read("score.json").decode('utf-8')
            info.midi = zip_file.read("midi.json").decode('utf-8')
        callback(info)

    @staticmethod
    def write_midi(data, output):
        ticks_per_beat = 480
        tempos = data.get('tempos', [])
        if not tempos or not tempos[0].get('tempo'):
            raise ValueError("Invalid tempo data")
        initial_tempo = tempos[0]['tempo']

        tracks = data.get('tracks', [])
        events = data.get('events', [])
        midi = MIDIFile(len(tracks))
        midi.addText(track=0, time=0, text="Made with love by yfishyon from gangqinpu.com") #水印

        for idx, track in enumerate(tracks):
            midi.addTrackName(idx, 0, track.get('name', f"Track{idx}"))
            midi.addTempo(idx, 0, round(60000000 / initial_tempo))
            midi.addProgramChange(idx, 0, 0, 0)

        seen_notes = set()

        for event in events:
            if event.get('duration', 0) <= 0 or 'staff' not in event:
                continue
            ev = event.get('event', [])
            if not isinstance(ev, list) or len(ev) < 2:
                continue

            pitch = ev[1]
            tick = event['tick']
            duration = event['duration']
            staff = event['staff']
            if staff < 1 or staff > len(tracks):
                continue
            track_index = staff - 1

            key = (track_index, tick, pitch)
            if key in seen_notes:
                continue
            seen_notes.add(key)

            start_time = tick / ticks_per_beat
            duration_sec = duration / ticks_per_beat

            midi.addNote(track_index, channel=0, pitch=pitch, time=start_time, duration=duration_sec, volume=80)

        with open(output, 'wb') as f:
            midi.writeFile(f)
        return output
