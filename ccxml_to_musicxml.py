# -*- coding: utf-8 -*-
"""
CCXML to MusicXML converter
Based on bszapp/ccmz-to-midi ccxml-to-musicxml branch
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


class CCXMLToMusicXML:
    """Convert CCXML format to MusicXML"""
    
    def __init__(self, ccxml_data, config=None):
        self.ccxml = ccxml_data
        self.config = config or {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'enableShift': True,
            'fontScale': 0.9
        }
        self.type_map = {
            1: 'whole',
            2: 'half',
            4: 'quarter',
            8: 'eighth',
            16: '16th',
            32: '32nd'
        }
        self.step_map = ["C", "D", "E", "F", "G", "A", "B"]
        
    def convert(self):
        """Main conversion method"""
        root = self._create_root()
        self._add_work(root)
        self._add_identification(root)
        self._add_defaults(root)
        self._add_credits(root)
        self._add_part_list(root)
        self._add_parts(root)
        
        return self._prettify(root)
    
    def _create_root(self):
        """Create root score-partwise element"""
        root = ET.Element('score-partwise', {'version': '4.0'})
        return root
    
    def _add_work(self, root):
        """Add work section"""
        work = ET.SubElement(root, 'work')
        work_title = ET.SubElement(work, 'work-title')
        work_title.text = self.ccxml.get('title', {}).get('title', '')
    
    def _add_identification(self, root):
        """Add identification section"""
        ident = ET.SubElement(root, 'identification')
        
        creator = ET.SubElement(ident, 'creator', {'type': 'composer'})
        composer = self.ccxml.get('title', {}).get('composer', '').replace('\r\n', ' ').replace('\n', ' ')
        creator.text = composer
        
        encoding = ET.SubElement(ident, 'encoding')
        software = ET.SubElement(encoding, 'software')
        software.text = 'chongchong-free-python (ccxml-to-musicxml)'
        
        enc_date = ET.SubElement(encoding, 'encoding-date')
        enc_date.text = datetime.now().strftime('%Y-%m-%d')
        
        # Add support tags
        supports_list = [
            {'element': 'accidental', 'type': 'yes'},
            {'element': 'beam', 'type': 'yes'},
            {'element': 'print', 'attribute': 'new-page', 'type': 'yes', 'value': 'yes'},
            {'element': 'print', 'attribute': 'new-system', 'type': 'yes', 'value': 'yes'},
            {'element': 'stem', 'type': 'yes'}
        ]
        for sup in supports_list:
            ET.SubElement(encoding, 'supports', sup)
        
        # Miscellaneous info
        misc = ET.SubElement(ident, 'miscellaneous')
        misc_date = ET.SubElement(misc, 'miscellaneous-field', {'name': 'creationDate'})
        misc_date.text = self.config['date']
        
        subtitle_elem = ET.SubElement(misc, 'miscellaneous-field', {'name': 'subtitle'})
        subtitle_elem.text = self.ccxml.get('title', {}).get('subtitle', '')
        
        copyright_elem = ET.SubElement(misc, 'miscellaneous-field', {'name': 'copyright'})
        qrcode = self.ccxml.get('qrcode', {})
        link = qrcode.get('link', '')
        copyright_elem.text = f'本文件来自虫虫钢琴ccmz格式转换，版权归原作者所有\n来源：{link}'
    
    def _add_defaults(self, root):
        """Add defaults section"""
        defs = ET.SubElement(root, 'defaults')
        
        scaling = ET.SubElement(defs, 'scaling')
        ET.SubElement(scaling, 'millimeters').text = '6.99911'
        ET.SubElement(scaling, 'tenths').text = '40'
        
        page = self.ccxml.get('page', {})
        pg_layout = ET.SubElement(defs, 'page-layout')
        ET.SubElement(pg_layout, 'page-height').text = str(page.get('h', 1700))
        ET.SubElement(pg_layout, 'page-width').text = str(page.get('w', 1200))
        
        for margin_type in ['even', 'odd']:
            margins = ET.SubElement(pg_layout, 'page-margins', {'type': margin_type})
            for side in ['left-margin', 'right-margin', 'top-margin', 'bottom-margin']:
                ET.SubElement(margins, side).text = '85.7252'
        
        # Appearance
        apper = ET.SubElement(defs, 'appearance')
        line_widths = [
            ('light barline', '1.8'), ('heavy barline', '5.5'), ('beam', '5'),
            ('bracket', '4.5'), ('dashes', '1'), ('enclosure', '1'),
            ('ending', '1.1'), ('extend', '1'), ('leger', '1.6'),
            ('pedal', '1.1'), ('octave shift', '1.1'), ('slur middle', '2.1'),
            ('slur tip', '0.5'), ('staff', '1.1'), ('stem', '1'),
            ('tie middle', '2.1'), ('tie tip', '0.5'), ('tuplet bracket', '1'),
            ('wedge', '1.2')
        ]
        for line_type, width in line_widths:
            ET.SubElement(apper, 'line-width', {'type': line_type}).text = width
        
        ET.SubElement(apper, 'note-size', {'type': 'cue'}).text = '70'
        ET.SubElement(apper, 'note-size', {'type': 'grace'}).text = '70'
        ET.SubElement(apper, 'note-size', {'type': 'grace-cue'}).text = '49'
        
        ET.SubElement(defs, 'music-font', {'font-family': 'Leland'})
        ET.SubElement(defs, 'word-font', {'font-family': 'Edwin', 'font-size': '10'})
        ET.SubElement(defs, 'lyric-font', {'font-family': 'Edwin', 'font-size': '10'})
    
    def _add_credits(self, root):
        """Add credit sections"""
        title_text = self.ccxml.get('title', {}).get('title', '')
        composer_text = self.ccxml.get('title', {}).get('composer', '')
        subtitle_text = self.ccxml.get('title', {}).get('subtitle', '')
        
        # Title credit
        c1 = ET.SubElement(root, 'credit', {'page': '1'})
        ET.SubElement(c1, 'credit-type').text = 'title'
        ET.SubElement(c1, 'credit-words', {
            'default-x': '600.241935',
            'default-y': '1611.210312',
            'justify': 'center',
            'valign': 'top',
            'font-size': '22'
        }).text = title_text
        
        # Composer credit
        c2 = ET.SubElement(root, 'credit', {'page': '1'})
        ET.SubElement(c2, 'credit-type').text = 'composer'
        ET.SubElement(c2, 'credit-words', {
            'default-x': '1114.7587',
            'default-y': '1511.210312',
            'justify': 'right',
            'valign': 'bottom'
        }).text = composer_text
        
        # Subtitle credit (if exists)
        if subtitle_text:
            c3 = ET.SubElement(root, 'credit', {'page': '1'})
            ET.SubElement(c3, 'credit-type').text = 'subtitle'
            ET.SubElement(c3, 'credit-words', {
                'default-x': '600.241935',
                'default-y': '1554.374677',
                'justify': 'center',
                'valign': 'top',
                'font-size': '14'
            }).text = subtitle_text
    
    def _add_part_list(self, root):
        """Add part-list section"""
        part_list = ET.SubElement(root, 'part-list')
        parts = self.ccxml.get('parts', [])
        lines = self.ccxml.get('lines', [])
        
        for i, part in enumerate(parts):
            pid = f'P{i + 1}'
            score_part = ET.SubElement(part_list, 'score-part', {'id': pid})
            
            # Get part name from lines
            name = ''
            shortname = ''
            if lines:
                for line in lines[:2]:
                    line_staves = line.get('lineStaves', [])
                    for ls in line_staves:
                        if ls.get('parti') == i:
                            if not name and line == lines[0]:
                                name = ls.get('name', '')
                            if not shortname and len(lines) > 1 and line == lines[1]:
                                shortname = ls.get('name', '')
            
            if not name:
                name = 'Piano'
            if not shortname:
                shortname = name
            
            ET.SubElement(score_part, 'part-name').text = name
            ET.SubElement(score_part, 'part-abbreviation').text = shortname
            
            score_inst = ET.SubElement(score_part, 'score-instrument', {'id': f'{pid}-I1'})
            ET.SubElement(score_inst, 'instrument-name').text = 'Piano'
            ET.SubElement(score_inst, 'instrument-sound').text = 'keyboard.piano'
            
            ET.SubElement(score_part, 'midi-device', {'id': f'{pid}-I1', 'port': '1'})
            
            midi_inst = ET.SubElement(score_part, 'midi-instrument', {'id': f'{pid}-I1'})
            ET.SubElement(midi_inst, 'midi-channel').text = '1'
            ET.SubElement(midi_inst, 'midi-program').text = '1'
            ET.SubElement(midi_inst, 'volume').text = '78.7402'
            ET.SubElement(midi_inst, 'pan').text = '0'
    
    def _add_parts(self, root):
        """Add all parts and measures"""
        parts = self.ccxml.get('parts', [])
        
        for p_idx, part_data in enumerate(parts):
            part = ET.SubElement(root, 'part', {'id': f'P{p_idx + 1}'})
            measures = part_data.get('measures', [])
            
            for m_idx, measure_data in enumerate(measures):
                self._add_measure(part, m_idx, measure_data)
    
    def _add_measure(self, part, m_idx, measure_data):
        """Add a single measure"""
        meas = ET.SubElement(part, 'measure', {
            'number': str(measure_data.get('num', m_idx + 1)),
            'width': str(measure_data.get('w', 100))
        })
        
        # Handle page/system breaks
        lines = self.ccxml.get('lines', [])
        for line in lines:
            if line.get('m1') == m_idx:
                print_attrs = {}
                if line.get('newpage'):
                    print_attrs = {'new-page': 'yes', 'new-system': 'yes'}
                elif m_idx == 0:
                    print_attrs = {}
                else:
                    print_attrs = {'new-system': 'yes'}
                
                print_elem = ET.SubElement(meas, 'print', print_attrs)
                sys_layout = ET.SubElement(print_elem, 'system-layout')
                
                if m_idx == 0:
                    sys_margins = ET.SubElement(sys_layout, 'system-margins')
                    ET.SubElement(sys_margins, 'left-margin').text = '50'
                    ET.SubElement(sys_margins, 'right-margin').text = '0'
                    ET.SubElement(sys_layout, 'top-system-distance').text = '170'
                else:
                    sys_margins = ET.SubElement(sys_layout, 'system-margins')
                    ET.SubElement(sys_margins, 'left-margin').text = '0'
                    ET.SubElement(sys_margins, 'right-margin').text = '0'
                    if line.get('newpage'):
                        ET.SubElement(sys_layout, 'top-system-distance').text = '120'
                    else:
                        ET.SubElement(sys_layout, 'system-distance').text = '237.5'
                
                if measure_data.get('staves', 1) > 1:
                    staff_layout = ET.SubElement(print_elem, 'staff-layout', {'number': '2'})
                    ET.SubElement(staff_layout, 'staff-distance').text = '65'
                break
        
        # Attributes
        attr = ET.SubElement(meas, 'attributes')
        ET.SubElement(attr, 'divisions').text = '24'
        
        fifths_data = measure_data.get('fifths')
        if fifths_data:
            key = ET.SubElement(attr, 'key')
            ET.SubElement(key, 'fifths').text = str(fifths_data.get('fifths', 0))
        
        time_data = measure_data.get('time')
        if time_data:
            time_elem = ET.SubElement(attr, 'time')
            ET.SubElement(time_elem, 'beats').text = str(time_data.get('beats', 4))
            ET.SubElement(time_elem, 'beat-type').text = str(time_data.get('beatu', 4))
        
        staves = measure_data.get('staves', 1)
        if staves:
            ET.SubElement(attr, 'staves').text = str(staves)
        
        # Tempo (only first measure)
        if m_idx == 0:
            dirs = measure_data.get('dirs', [])
            for d in dirs:
                if d.get('type') == 'metronome':
                    direction = ET.SubElement(meas, 'direction', {'placement': 'above'})
                    dir_type = ET.SubElement(direction, 'direction-type')
                    metro = ET.SubElement(dir_type, 'metronome', {'parentheses': 'no'})
                    
                    param = d.get('param', {})
                    metro.set('default-x', str(param.get('x', 0)))
                    metro.set('relative-y', '20')
                    
                    ET.SubElement(metro, 'beat-unit').text = 'quarter'
                    ET.SubElement(metro, 'per-minute').text = str(d.get('value', '60'))
                    
                    ET.SubElement(direction, 'staff').text = str(d.get('staff', 1))
                    ET.SubElement(direction, 'sound', {'tempo': str(d.get('value', '60'))})
        
        # Barlines and repeats
        lbar = measure_data.get('lbar')
        if lbar and lbar.get('repeat'):
            barline = ET.SubElement(meas, 'barline', {'location': 'left'})
            ET.SubElement(barline, 'bar-style').text = 'heavy-light'
            ET.SubElement(barline, 'repeat', {'direction': lbar['repeat']})
        
        ends = measure_data.get('ends')
        if ends:
            barline = ET.SubElement(meas, 'barline', {'location': 'left'})
            ET.SubElement(barline, 'ending', {
                'number': str(ends.get('num', '1')),
                'type': 'start'
            })
            
            if ends.get('stop'):
                rbarline = ET.SubElement(meas, 'barline', {'location': 'right'})
                ET.SubElement(rbarline, 'ending', {
                    'number': str(ends.get('num', '1')),
                    'type': 'stop'
                })
                
                rbar = measure_data.get('rbar')
                if rbar and rbar.get('repeat'):
                    ET.SubElement(rbarline, 'bar-style').text = 'light-heavy'
                    ET.SubElement(rbarline, 'repeat', {'direction': rbar['repeat']})
        else:
            rbar = measure_data.get('rbar')
            if rbar and rbar.get('repeat'):
                barline = ET.SubElement(meas, 'barline', {'location': 'right'})
                ET.SubElement(barline, 'bar-style').text = 'light-heavy'
                ET.SubElement(barline, 'repeat', {'direction': rbar['repeat']})
        
        # Notes (simplified version - basic structure)
        notes = measure_data.get('notes', [])
        self._add_notes(meas, notes)
    
    def _add_notes(self, meas, notes):
        """Add notes to measure (simplified version)"""
        for note_data in notes:
            self._add_single_note(meas, note_data)
    
    def _add_single_note(self, meas, note_data):
        """Add a single note element"""
        note_elem = ET.SubElement(meas, 'note')
        
        # Check if rest
        rest_data = note_data.get('rest')
        if rest_data:
            ET.SubElement(note_elem, 'rest')
        else:
            # Regular note - add pitch
            elems = note_data.get('elems', [])
            if elems:
                elem = elems[0]
                pitch = ET.SubElement(note_elem, 'pitch')
                step = elem.get('step', 1)
                ET.SubElement(pitch, 'step').text = self.step_map[step - 1] if 1 <= step <= 7 else 'C'
                
                alter = elem.get('alter')
                if alter:
                    ET.SubElement(pitch, 'alter').text = str(alter)
                
                ET.SubElement(pitch, 'octave').text = str(elem.get('octave', 4))
        
        # Duration (simplified - using type value)
        note_type = note_data.get('type', 4)
        duration = 24 * (4 / note_type)
        ET.SubElement(note_elem, 'duration').text = str(int(duration))
        
        # Voice and staff
        staff_num = note_data.get('staff', 1)
        voice_num = note_data.get('v', 0)
        track_id = (staff_num - 1) * 4 + voice_num
        
        ET.SubElement(note_elem, 'voice').text = str(track_id + 1)
        ET.SubElement(note_elem, 'type').text = self.type_map.get(note_type, 'quarter')
        
        # Dots
        dots = note_data.get('dots', 0)
        for _ in range(dots):
            ET.SubElement(note_elem, 'dot')
        
        ET.SubElement(note_elem, 'staff').text = str(staff_num)
        
        # Stem direction
        stem = note_data.get('stem')
        if stem:
            stem_type = stem.get('type')
            if stem_type:
                stem_elem = ET.SubElement(note_elem, 'stem')
                stem_elem.text = stem_type
        
        # Lyrics
        lyrics = note_data.get('lyrics')
        if lyrics:
            lyric_font = self.ccxml.get('defaults', {}).get('lyricfont', 'SimHei')
            for lyric_data in lyrics:
                lyric_num = lyric_data.get('num', 0) + 1
                lyric_elem = ET.SubElement(note_elem, 'lyric', {'number': str(lyric_num)})
                ET.SubElement(lyric_elem, 'syllabic').text = 'single'
                text_elem = ET.SubElement(lyric_elem, 'text', {'font-family': lyric_font})
                text_elem.text = lyric_data.get('text', '')
    
    def _prettify(self, elem):
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        
        # Add DOCTYPE
        impl = minidom.getDOMImplementation()
        doctype = impl.createDocumentType(
            'score-partwise',
            '-//Recordare//DTD MusicXML 4.0 Partwise//EN',
            'http://www.musicxml.org/dtds/partwise.dtd'
        )
        
        doc = impl.createDocument(None, 'score-partwise', doctype)
        doc.replaceChild(reparsed.documentElement, doc.documentElement)
        
        return doc.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')


def convert_ccxml_to_musicxml(ccxml_data, config=None):
    """Main conversion function"""
    converter = CCXMLToMusicXML(ccxml_data, config)
    return converter.convert()
