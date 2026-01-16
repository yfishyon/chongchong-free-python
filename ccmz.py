import zipfile
import json
import io
import requests
from midiutil.MidiFile import MIDIFile

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
            info.midi = zip_file.read("data.mid")
        elif version == 2:
            data = bytes([v + 1 if v % 2 == 0 else v - 1 for v in data])
            zip_file = zipfile.ZipFile(io.BytesIO(data))
            info.score = zip_file.read("score.json").decode('utf-8')
            info.midi = zip_file.read("midi.json").decode('utf-8')
        callback(info)

    @staticmethod
    def parse_midi_event(event_bytes):
        if not event_bytes or len(event_bytes) == 0:
            return None
        
        first_byte = event_bytes[0]
        
        if (first_byte & 0xF0) != 0xF0:
            event_type = first_byte >> 4
            channel = first_byte & 0x0F
            
            if len(event_bytes) < 2:
                return None
                
            event = {'type': 'channel', 'channel': channel}
            
            if event_type == 0x8:
                event['subtype'] = 'noteOff'
                event['noteNumber'] = event_bytes[1]
                if len(event_bytes) > 2:
                    event['velocity'] = event_bytes[2]
            elif event_type == 0x9:
                event['noteNumber'] = event_bytes[1]
                if len(event_bytes) > 2:
                    event['velocity'] = event_bytes[2]
                event['subtype'] = 'noteOff' if event.get('velocity', 0) == 0 else 'noteOn'
            elif event_type == 0xA:
                event['subtype'] = 'noteAftertouch'
                event['noteNumber'] = event_bytes[1]
                if len(event_bytes) > 2:
                    event['amount'] = event_bytes[2]
            elif event_type == 0xB:
                event['subtype'] = 'controller'
                event['controllerType'] = event_bytes[1]
                if len(event_bytes) > 2:
                    event['value'] = event_bytes[2]
            elif event_type == 0xC:
                event['subtype'] = 'programChange'
                event['programNumber'] = event_bytes[1]
            elif event_type == 0xD:
                event['subtype'] = 'channelAftertouch'
                event['amount'] = event_bytes[1]
            elif event_type == 0xE:
                event['subtype'] = 'pitchBend'
                event['value'] = event_bytes[1] + ((event_bytes[2] << 7) if len(event_bytes) > 2 else 0)
            else:
                event['subtype'] = 'unknown'
            
            return event
        
        elif first_byte == 0xFF:
            if len(event_bytes) < 2:
                return None
            
            event = {'type': 'meta'}
            meta_type = event_bytes[1]
            
            length = 0
            pos = 2
            if pos < len(event_bytes):
                byte = event_bytes[pos]
                pos += 1
                while byte & 0x80 and pos < len(event_bytes):
                    length = (length << 7) + (byte & 0x7F)
                    byte = event_bytes[pos]
                    pos += 1
                length = (length << 7) + (byte & 0x7F)
            
            if meta_type == 0x00:
                if length == 2:
                    event['subtype'] = 'sequenceNumber'
                    if pos + 1 < len(event_bytes):
                        event['number'] = (event_bytes[pos] << 8) + event_bytes[pos + 1]
            elif meta_type == 0x01:
                event['subtype'] = 'text'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x02:
                event['subtype'] = 'copyrightNotice'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x03:
                event['subtype'] = 'trackName'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x04:
                event['subtype'] = 'instrumentName'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x05:
                event['subtype'] = 'lyrics'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x06:
                event['subtype'] = 'marker'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x07:
                event['subtype'] = 'cuePoint'
                if pos + length <= len(event_bytes):
                    event['text'] = event_bytes[pos:pos+length].decode('utf-8', errors='ignore')
            elif meta_type == 0x20:
                if length == 1:
                    event['subtype'] = 'midiChannelPrefix'
                    if pos < len(event_bytes):
                        event['channel'] = event_bytes[pos]
            elif meta_type == 0x2F:
                if length == 0:
                    event['subtype'] = 'endOfTrack'
            elif meta_type == 0x51:
                if length == 3:
                    event['subtype'] = 'setTempo'
                    if pos + 2 < len(event_bytes):
                        event['microsecondsPerBeat'] = (event_bytes[pos] << 16) + (event_bytes[pos + 1] << 8) + event_bytes[pos + 2]
            elif meta_type == 0x54:
                if length == 5:
                    event['subtype'] = 'smpteOffset'
                    if pos + 4 < len(event_bytes):
                        byte = event_bytes[pos]
                        event['frameRate'] = {0: 24, 32: 25, 64: 29, 96: 30}.get(byte & 0x60, 30)
                        event['hour'] = byte & 0x1F
                        event['min'] = event_bytes[pos + 1]
                        event['sec'] = event_bytes[pos + 2]
                        event['frame'] = event_bytes[pos + 3]
                        event['subframe'] = event_bytes[pos + 4]
            elif meta_type == 0x58:
                if length == 4:
                    event['subtype'] = 'timeSignature'
                    if pos + 3 < len(event_bytes):
                        event['numerator'] = event_bytes[pos]
                        event['denominator'] = 2 ** event_bytes[pos + 1]
                        event['metronome'] = event_bytes[pos + 2]
                        event['thirtyseconds'] = event_bytes[pos + 3]
            elif meta_type == 0x59:
                if length == 2:
                    event['subtype'] = 'keySignature'
                    if pos + 1 < len(event_bytes):
                        event['key'] = event_bytes[pos] if event_bytes[pos] <= 127 else event_bytes[pos] - 256
                        event['scale'] = event_bytes[pos + 1]
            elif meta_type == 0x7F:
                event['subtype'] = 'sequencerSpecific'
                if pos + length <= len(event_bytes):
                    event['data'] = event_bytes[pos:pos+length]
            else:
                event['subtype'] = 'unknown'
                if pos + length <= len(event_bytes):
                    event['data'] = event_bytes[pos:pos+length]
            
            return event
        
        elif first_byte == 0xF0:
            event = {'type': 'sysEx'}
            length = 0
            pos = 1
            if pos < len(event_bytes):
                byte = event_bytes[pos]
                pos += 1
                while byte & 0x80 and pos < len(event_bytes):
                    length = (length << 7) + (byte & 0x7F)
                    byte = event_bytes[pos]
                    pos += 1
                length = (length << 7) + (byte & 0x7F)
            
            if pos + length <= len(event_bytes):
                event['data'] = event_bytes[pos:pos+length]
            
            return event
        
        elif first_byte == 0xF7:
            event = {'type': 'dividedSysEx'}
            length = 0
            pos = 1
            if pos < len(event_bytes):
                byte = event_bytes[pos]
                pos += 1
                while byte & 0x80 and pos < len(event_bytes):
                    length = (length << 7) + (byte & 0x7F)
                    byte = event_bytes[pos]
                    pos += 1
                length = (length << 7) + (byte & 0x7F)
            
            if pos + length <= len(event_bytes):
                event['data'] = event_bytes[pos:pos+length]
            
            return event
        
        return None

    @staticmethod
    def write_midi(data, output):
        ticks_per_beat = 480
        tempos = data.get('tempos', [])
        tracks = data.get('tracks', [])
        events = data.get('events', [])
        
        if not tracks and not events:
            raise ValueError("No track or event data")
        
        track_count = len(tracks) if tracks else 1
        
        midi = MIDIFile(track_count)
        
        initial_tempo = 500000
        if tempos and tempos[0].get('tempo'): #其实我觉得不太可能取不到
            initial_tempo = tempos[0]['tempo']
        
        for idx in range(track_count):
            if tracks and idx < len(tracks):
                track_name = tracks[idx].get('name', f'Track{idx}')
                midi.addTrackName(idx, 0, track_name)
            
            bpm = round(60000000 / initial_tempo)
            midi.addTempo(idx, 0, bpm)
            
            if tracks and idx < len(tracks):
                program = tracks[idx].get('program', 0)
                midi.addProgramChange(idx, 0, 0, program)
        
        track_events = {}
        all_parsed_events = []
        
        event_stats = {
            'noteOn': 0, 'noteOff': 0, 'controller': 0,
            'programChange': 0, 'meta': 0, 'unknown': 0
        }
        
        for event in events:
            track_id = event.get('track', 0)
            if track_id >= track_count:
                track_id = 0
            
            event_bytes = event.get('event', [])
            parsed_event = LibCCMZ.parse_midi_event(event_bytes)
            
            if parsed_event:
                parsed_event['tick'] = event['tick']
                parsed_event['duration'] = event.get('duration', 0)
                parsed_event['staff'] = event.get('staff', 0)
                parsed_event['track'] = track_id
                
                if track_id not in track_events:
                    track_events[track_id] = []
                track_events[track_id].append(parsed_event)
                all_parsed_events.append(parsed_event)
                
                if parsed_event['type'] == 'channel':
                    event_stats[parsed_event.get('subtype', 'unknown')] += 1
                else:
                    event_stats[parsed_event['type']] += 1
        
        note_on_map = {}
        
        for parsed_event in all_parsed_events:
            if parsed_event['type'] == 'channel':
                if parsed_event['subtype'] == 'noteOn':
                    key = (parsed_event['track'], parsed_event.get('channel', 0), parsed_event.get('noteNumber', 0))
                    note_on_map[key] = parsed_event
                
                elif parsed_event['subtype'] == 'noteOff':
                    key = (parsed_event['track'], parsed_event.get('channel', 0), parsed_event.get('noteNumber', 0))
                    
                    if key in note_on_map:
                        note_on = note_on_map[key]
                        
                        start_tick = note_on['tick']
                        end_tick = parsed_event['tick']
                        duration_ticks = max(10, end_tick - start_tick)
                        
                        start_time = start_tick / ticks_per_beat
                        duration_sec = duration_ticks / ticks_per_beat
                        velocity = note_on.get('velocity', 90)
                        
                        track_idx = parsed_event['track']
                        if track_idx >= track_count:
                            track_idx = track_count - 1
                        
                        midi.addNote(track_idx, 0, note_on['noteNumber'], 
                                   start_time, duration_sec, velocity)
                        
                        del note_on_map[key]
                    
                    else:
                        track_idx = parsed_event['track']
                        if track_idx >= track_count:
                            track_idx = track_count - 1
                        
                        note_number = parsed_event.get('noteNumber', 60)
                        velocity = parsed_event.get('velocity', 0)
                        
                        if velocity > 0:
                            start_time = parsed_event['tick'] / ticks_per_beat
                            duration_sec = parsed_event.get('duration', 10) / ticks_per_beat
                            midi.addNote(track_idx, 0, note_number, 
                                       start_time, duration_sec, velocity)
                
                elif parsed_event['subtype'] == 'controller':
                    track_idx = parsed_event['track']
                    if track_idx >= track_count:
                        track_idx = track_count - 1
                    
                    controller_type = parsed_event.get('controllerType', 0)
                    value = parsed_event.get('value', 0)
                    time = parsed_event['tick'] / ticks_per_beat
                    
                    if controller_type in [1, 7, 11, 64, 65, 66, 67, 68]:
                        midi.addControllerEvent(track_idx, 0, time, 
                                              controller_type, value)
                
                elif parsed_event['subtype'] == 'pitchBend':
                    track_idx = parsed_event['track']
                    if track_idx >= track_count:
                        track_idx = track_count - 1
                    
                    pitch_value = parsed_event.get('value', 8192)
                    normalized_value = ((pitch_value + 8192) * 16383) // 16383
                    time = parsed_event['tick'] / ticks_per_beat
                    
                    midi.addPitchWheelEvent(track_idx, 0, time, normalized_value)
        
        with open(output, 'wb') as f:
            midi.writeFile(f)
        return output
