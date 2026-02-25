import re
import os
import sys
import json
import argparse
import requests
from ccmz import LibCCMZ
from ccxml_to_musicxml import convert_ccxml_to_musicxml
from score_generator import ScoreGenerator

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

def get_ccmz_from_html(music_id):
    """
    从 HTML 页面的 iframe 中提取 CCMZ URL（主要方法）
    返回 CCMZ URL 或 None
    """
    try:
        url = f"https://www.gangqinpu.com/cchtml/{music_id}.htm"
        print(f"正在从页面提取 CCMZ 链接...")
        html = httpget(url)
        
        # 匹配 <iframe id='ai-score' src="...">
        # src 可能是相对路径或完整路径
        pattern = r'<iframe[^>]+id=["\']ai-score["\'][^>]+src=["\']([^"\']+)["\']'
        match = re.search(pattern, html)
        
        if not match:
            print("未找到 ai-score iframe")
            return None
        
        iframe_src = match.group(1)
        print(f"找到 iframe src: {iframe_src[:100]}...")
        
        # 提取 url 参数
        url_match = re.search(r'[?&]url=([^&]+)', iframe_src)
        if not url_match:
            print("未找到 CCMZ URL 参数")
            return None
        
        ccmz_url = url_match.group(1)
        
        # URL 解码（如果需要）
        from urllib.parse import unquote
        ccmz_url = unquote(ccmz_url)
        
        print(f"✅ 成功提取 CCMZ URL")
        return ccmz_url
        
    except Exception as e:
        print(f"从 HTML 提取 CCMZ 失败: {e}")
        return None

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
    parser = argparse.ArgumentParser(description="虫虫钢琴钢琴谱midi/乐谱下载")
    parser.add_argument('-i', '--id', help='琴谱id或url')
    parser.add_argument('-o', '--output', default='./output', help='保存目录（默认output）')
    parser.add_argument('-pdf', action='store_true', help='下载曲谱为pdf格式（旧方式-图片）')
    parser.add_argument('-png', action='store_true', help='下载曲谱为png格式（旧方式-图片）')
    parser.add_argument('-score', action='store_true', help='生成乐谱（新方式-使用Lilypond渲染）')
    parser.add_argument('--check-env', action='store_true', help='检查环境配置')
    args = parser.parse_args()

    # Check environment if requested
    if args.check_env:
        from score_generator import check_environment
        check_environment()
        return

    # For other operations, -i is required
    if not args.id:
        parser.error('the following arguments are required: -i/--id')

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
    
    # 先尝试从 HTML 页面提取完整 CCMZ（主要方法）
    ccmz_link = get_ccmz_from_html(music_id)
    
    # 如果失败，使用 API（fallback）
    if not ccmz_link:
        print("⚠️  HTML 提取失败，尝试使用 API（可能为试用版）...")
        details = json.loads(get_details(opern_id))['list']
        ccmz_link = details['play_json']
    else:
        # HTML 提取成功，仍需从 API 获取其他信息
        print("📥 获取歌曲详细信息...")
        details = json.loads(get_details(opern_id))['list']
    
    #print(details)
    music_name = details['name']
    paid = details['is_pay']
    typename = details['typename']
    authorc_name = details['author']

    file_name = f"{safe_filename(music_name)}-{safe_filename(typename)}"

    print(f"付费歌曲: {boolean_string(paid == '1')}")
    print(f"音乐名: {music_name}")
    print(f"原作者: {typename}")
    print(f"上传人: {authorc_name}")

    # Old method: Download images as PNG
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
        return
    
    # Old method: Download images as PDF
    if args.pdf:
        pdf_info = get_pdf_info(music_id)
        if pdf_info and 'image_list' in pdf_info:
            image_list = pdf_info['image_list']
            print(f"曲谱页数: {len(image_list)}页")
            if download_pdf_images(image_list, save_dir, file_name):
                print("PDF下载完成")
        else:
            print('无曲谱图片可下载')
        return

    # New method: Generate score using Lilypond
    if args.score:
        if not ccmz_link:
            print('无乐谱数据可用')
            return
        
        print("正在下载 CCMZ 数据...")
        ccmz_raw = LibCCMZ.download_ccmz(ccmz_link)
        if not ccmz_raw:
            print("下载失败")
            return
        
        # Parse CCMZ
        def parse_ccmz(info):
            if info.ver == 2:
                score_data = json.loads(info.score)
                
                print("正在转换 CCXML -> MusicXML...")
                try:
                    musicxml_content = convert_ccxml_to_musicxml(score_data)
                    
                    # Save MusicXML for debugging
                    musicxml_path = os.path.join(save_dir, f"{file_name}.musicxml")
                    with open(musicxml_path, 'w', encoding='utf-8') as f:
                        f.write(musicxml_content)
                    print(f"MusicXML 已保存: {musicxml_path}")
                    
                    # Generate score using Lilypond
                    print("正在初始化乐谱生成器...")
                    generator = ScoreGenerator()
                    
                    if not generator.setup_lilypond():
                        print("\n错误: 未找到 Lilypond")
                        print("请先安装 Lilypond 或运行 --check-env 查看环境配置")
                        return
                    
                    print("正在生成乐谱图片...")
                    png_files = generator.generate_score_from_musicxml(
                        musicxml_content,
                        save_dir,
                        file_name
                    )
                    
                    if png_files:
                        print(f"\n成功生成 {len(png_files)} 页乐谱:")
                        for png_file in png_files:
                            print(f"  - {png_file}")
                    else:
                        print("乐谱生成失败")
                        
                except Exception as e:
                    print(f"转换出错: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("仅支持 CCMZ v2 格式")
        
        LibCCMZ.read_ccmz(ccmz_raw, parse_ccmz)
        return

    # Default: Download MIDI
    if not args.pdf and not args.png and not args.score:
        # ccmz_link 已经在前面从 HTML 或 API 获取
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
    