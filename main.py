import re
import os
import sys
import json
import argparse
import requests
from ccmz import LibCCMZ

def httpget(url, headers=None):
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def boolean_string(val, detailed=False):
    return "是" if val else "否" if not detailed else ("✔️" if val else "❌")

def get_music_id(param):
    match = re.search(r'(\d+)', param)
    return match.group(1) if match else None

def get_opern_id(music_id):
    url = f"https://www.gangqinpu.com/cchtml/{music_id}.htm"
    text = httpget(url)
    match = re.search(r'data-oid="(\d+)"', text)
    if not match:
        print("OpernID找不到")
        return None
    return match.group(1)

def get_details(opern_id):
    api = 'https://gangqinpu.lzjoy.com?'
    params = f"urlparam=pad/detail/operninfov002&old_id={opern_id}"
    return httpget(api + params)

def safe_filename(name):
    return ''.join(c if c not in '/\\:*?"<>|' else ' ' for c in name)

def main():
    parser = argparse.ArgumentParser(description="虫虫钢琴钢琴谱midi下载")
    parser.add_argument('-i', '--id', required=True, help='琴谱id或url')
    parser.add_argument('-o', '--output', default='./output', help='保存目录（默认output）')
    args = parser.parse_args()

    input_param = args.id
    save_dir = args.output
    music_id = get_music_id(input_param)
    if not music_id:
        print("无法识别id")
        sys.exit(1)

    os.makedirs(save_dir, exist_ok=True)

    opern_id = get_opern_id(music_id)
    if not opern_id:
        print("无法获取OpernID，退出。")
        sys.exit(1)
    details = json.loads(get_details(opern_id))['list']
    #print(details)
    ccmz_link = details['play_json']
    music_name = details['name']
    paid = details['is_pay']
    typename = details['typename']
    authorc_name = details['author']

    file_name = f"{safe_filename(music_name)}-{typename}"

    print(f"付费歌曲: {boolean_string(paid == '1')}")
    print(f"音乐名: {music_name}")
    print(f"原作者: {typename}")
    print(f"上传人: {authorc_name}")

    if ccmz_link:
        ccmz_raw = LibCCMZ.download_ccmz(ccmz_link)
        def cb(info):
            midi_path = os.path.join(save_dir, f"{file_name}.mid")
            if info.ver == 2:
                midi_data = json.loads(info.midi)
                LibCCMZ.write_midi(midi_data, midi_path)
            else:
                with open(midi_path, "wb") as f:
                    f.write(info.midi.encode("latin1"))
            print(f"下载成功! 已保存MIDI文件：{midi_path}")
        LibCCMZ.read_ccmz(ccmz_raw, cb)
    else:
        print('无MIDI可下载')

if __name__ == "__main__":
    main()