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

def get_pdf_info(music_id):
    url = f"https://gangqinpu.lzjoy.com/?urlparam=home/user/getOpernDetail&id={music_id}"
    response = httpget(url)
    data = json.loads(response)
    
    if data.get('returnMsg') != 'ok':
        return None
    
    return data.get('list', {})

def download_pdf_images(image_list, save_dir, file_name_base):
    import tempfile
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from PIL import Image
    
    image_paths = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, img_url in enumerate(image_list, 1):
            try:
                resp = requests.get(img_url)
                resp.raise_for_status()
                
                img_path = os.path.join(temp_dir, f"temp_{i}.png")
                with open(img_path, 'wb') as f:
                    f.write(resp.content)
                image_paths.append(img_path)
                
            except:
                pass
        
        if image_paths:
            pdf_path = os.path.join(save_dir, f"{file_name_base}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=A4)
            
            for img_path in image_paths:
                try:
                    img = Image.open(img_path)
                    img_width, img_height = img.size
                    
                    page_width, page_height = A4
                    scale_x = page_width / img_width
                    scale_y = page_height / img_height
                    scale = min(scale_x, scale_y)
                    
                    new_width = img_width * scale
                    new_height = img_height * scale
                    x = (page_width - new_width) / 2
                    y = (page_height - new_height) / 2
                    
                    c.drawImage(img_path, x, y, new_width, new_height)
                    c.showPage()
                    
                except:
                    pass
            
            c.save()
            print(f"PDF已保存: {pdf_path}")
            return True
    
    return False

def download_png_images(image_list, save_dir, file_name_base):
    success_count = 0
    for i, img_url in enumerate(image_list, 1):
        try:
            resp = requests.get(img_url)
            resp.raise_for_status()
            
            img_path = os.path.join(save_dir, f"{file_name_base}-{i}.png")
            with open(img_path, 'wb') as f:
                f.write(resp.content)
            success_count += 1
            
        except:
            pass
    
    return success_count

def safe_filename(name):
    return ''.join(c if c not in '/\\:*?"<>|' else ' ' for c in name)

def main():
    parser = argparse.ArgumentParser(description="虫虫钢琴钢琴谱midi下载")
    parser.add_argument('-i', '--id', required=True, help='琴谱id或url')
    parser.add_argument('-o', '--output', default='./output', help='保存目录（默认output）')
    parser.add_argument('-pdf', action='store_true', help='下载曲谱为pdf格式')
    parser.add_argument('-png', action='store_true', help='下载曲谱为png格式')
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

    file_name = f"{safe_filename(music_name)}-{safe_filename(typename)}"

    print(f"付费歌曲: {boolean_string(paid == '1')}")
    print(f"音乐名: {music_name}")
    print(f"原作者: {typename}")
    print(f"上传人: {authorc_name}")

    if args.png:
        pdf_info = get_pdf_info(music_id)
        if pdf_info and 'image_list' in pdf_info:
            image_list = pdf_info['image_list']
            print(f"曲谱页数: {len(image_list)}页")
            success_count = download_png_images(image_list, save_dir, file_name)
            if success_count > 0:
                print(f"PNG已保存: {success_count}张图片")
        else:
            print('无曲谱图片可下载')

    if not args.pdf and not args.png:
        ccmz_link = details['play_json']
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
    