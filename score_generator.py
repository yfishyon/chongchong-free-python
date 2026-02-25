# -*- coding: utf-8 -*-
"""
Score generation module using Lilypond
Handles: MusicXML -> LY -> PNG/PDF conversion
"""

import os
import subprocess
import platform
import tempfile
import shutil


class ScoreGenerator:
    """Generate sheet music images from MusicXML"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_android = self._detect_android()
        self.lilypond_cmd = None
        self.musicxml2ly_script = None
        self.python_exe = None
        
    def _detect_android(self):
        """Detect if running on Android (Termux)"""
        try:
            return 'com.termux' in os.environ.get('PREFIX', '') or \
                   os.path.exists('/data/data/com.termux')
        except:
            return False
    
    def _find_lilypond_windows(self):
        """Find Lilypond installation on Windows"""
        # Check common installation paths
        possible_paths = [
            os.path.expandvars(r'%LOCALAPPDATA%\lilyponddist\lilyponddist'),
            r'C:\Program Files\LilyPond',
            r'C:\Program Files (x86)\LilyPond',
        ]
        
        for base_path in possible_paths:
            if os.path.exists(base_path):
                # Find version directories
                try:
                    for item in os.listdir(base_path):
                        item_path = os.path.join(base_path, item)
                        if os.path.isdir(item_path):
                            bin_path = os.path.join(item_path, 'bin')
                            lilypond_exe = os.path.join(bin_path, 'lilypond.exe')
                            musicxml2ly = os.path.join(bin_path, 'musicxml2ly.py')
                            python_exe = os.path.join(bin_path, 'python.exe')
                            
                            if os.path.exists(lilypond_exe):
                                self.lilypond_cmd = lilypond_exe
                                if os.path.exists(musicxml2ly):
                                    self.musicxml2ly_script = musicxml2ly
                                if os.path.exists(python_exe):
                                    self.python_exe = python_exe
                                return True
                except:
                    continue
        
        return False
    
    def _find_lilypond_unix(self):
        """Find Lilypond on Unix-like systems"""
        try:
            # Check if lilypond is in PATH
            result = subprocess.run(
                ['which', 'lilypond'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.lilypond_cmd = result.stdout.strip()
                
                # Try to find musicxml2ly
                ly_dir = os.path.dirname(self.lilypond_cmd)
                musicxml2ly = os.path.join(ly_dir, 'musicxml2ly')
                if os.path.exists(musicxml2ly):
                    self.musicxml2ly_script = musicxml2ly
                
                return True
        except:
            pass
        
        return False
    
    def setup_lilypond(self):
        """Setup Lilypond based on the environment"""
        print(f"检测操作系统: {self.system}")
        print(f"是否为 Android: {self.is_android}")
        
        if self.is_android:
            return self._install_lilypond_android()
        elif self.system == 'Windows':
            return self._find_lilypond_windows()
        else:
            return self._find_lilypond_unix()
    
    def _install_lilypond_android(self):
        """Install Lilypond on Android (Termux)"""
        print("检测到 Android 环境 (Termux)")
        print("正在安装 Lilypond...")
        
        try:
            # Update package list
            subprocess.run(['pkg', 'update', '-y'], check=True)
            
            # Install lilypond
            subprocess.run(['pkg', 'install', 'lilypond', '-y'], check=True)
            
            # Verify installation
            result = subprocess.run(
                ['which', 'lilypond'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.lilypond_cmd = result.stdout.strip()
                print(f"Lilypond 安装成功: {self.lilypond_cmd}")
                
                # Try to find musicxml2ly
                ly_dir = os.path.dirname(self.lilypond_cmd)
                musicxml2ly = os.path.join(ly_dir, 'musicxml2ly')
                if os.path.exists(musicxml2ly):
                    self.musicxml2ly_script = musicxml2ly
                
                return True
            else:
                print("Lilypond 安装失败")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"安装 Lilypond 时出错: {e}")
            return False
        except Exception as e:
            print(f"意外错误: {e}")
            return False
    
    def musicxml_to_ly(self, musicxml_path, ly_output_path):
        if not self.lilypond_cmd:
            print("错误: 未找到 Lilypond")
            return False

        bin_dir = os.path.dirname(self.lilypond_cmd)
        musicxml2ly = os.path.join(bin_dir, 'musicxml2ly.py')
        python_exe = os.path.join(bin_dir, 'python.exe') if self.system == 'Windows' else 'python3'

        if not os.path.exists(musicxml2ly):
            print(f"错误: 找不到 musicxml2ly.py: {musicxml2ly}")
            return False

        # musicxml2ly has a bug with repeat barlines - strip them first
        cleaned_path = musicxml_path + '.clean.xml'
        import re as _re
        with open(musicxml_path, 'r', encoding='utf-8') as f:
            xml = f.read()
        xml = _re.sub(r'<barline[^>]*>[\s\S]*?<repeat[^/]*/?>[\s\S]*?</barline>', '', xml)
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            f.write(xml)

        print("使用 Lilypond 内置 musicxml2ly...")
        print("正在转换 MusicXML → LY（可能需要约30秒）...")
        try:
            ly_base = os.path.splitext(ly_output_path)[0]
            cmd = [python_exe, musicxml2ly, '-o', ly_base, cleaned_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=120)
            if os.path.exists(ly_output_path):
                return True
            print(f"转换失败: {ly_output_path} 未生成")
            return False
        except subprocess.TimeoutExpired:
            print("转换超时（超过120秒）")
            return False
        except Exception as e:
            print(f"转换失败: {e}")
            return False
        finally:
            try:
                os.remove(cleaned_path)
            except Exception:
                pass
    
    def ly_to_png(self, ly_path, output_basename):
        """Convert LY to PNG images. output_basename is the base path (without extension)"""
        if not self.lilypond_cmd:
            print("错误: 未找到 Lilypond")
            return False
        
        print(f"使用 Lilypond: {self.lilypond_cmd}")
        print(f"转换 LY 文件: {ly_path}")
        
        try:
            cmd = [
                self.lilypond_cmd,
                '--png',
                '-dresolution=300',
                f'-doutput={output_basename}',
                ly_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(ly_path) or '.'
            )
            
            if result.returncode != 0:
                err = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
                print(f"Lilypond 错误:\n{err}")
                return False
            
            print("转换成功!")
            return True
            
        except Exception as e:
            print(f"转换时出错: {e}")
            return False
    
    def generate_score_from_musicxml(self, musicxml_content, output_dir, base_name):
        with tempfile.TemporaryDirectory() as temp_dir:
            musicxml_path = os.path.join(temp_dir, f'{base_name}.musicxml')
            with open(musicxml_path, 'w', encoding='utf-8') as f:
                f.write(musicxml_content)
            
            ly_path = os.path.join(temp_dir, f'{base_name}.ly')
            if not self.musicxml_to_ly(musicxml_path, ly_path):
                print("MusicXML 转 LY 失败")
                return None

            # output_basename: all PNGs will be temp_dir/score, temp_dir/score-1.png, etc.
            output_basename = os.path.join(temp_dir, 'score')
            if not self.ly_to_png(ly_path, output_basename):
                print("LY 转 PNG 失败")
                return None

            png_files = []
            raw_pngs = sorted(f for f in os.listdir(temp_dir) if f.endswith('.png'))
            for i, file in enumerate(raw_pngs, 1):
                src = os.path.join(temp_dir, file)
                dst = os.path.join(output_dir, f'{base_name}-page{i}.png')
                shutil.copy2(src, dst)
                png_files.append(dst)

            print(f"生成了 {len(png_files)} 个页面")
            return png_files


def check_environment():
    """Check and report the environment setup"""
    generator = ScoreGenerator()
    
    print("=" * 50)
    print("环境检测")
    print("=" * 50)
    
    if generator.setup_lilypond():
        print("✓ Lilypond 已找到")
        print(f"  路径: {generator.lilypond_cmd}")
        
        if generator.musicxml2ly_script:
            print(f"✓ musicxml2ly 已找到")
            print(f"  路径: {generator.musicxml2ly_script}")
        else:
            print(f"⚠ musicxml2ly 未找到")
        
        if generator.python_exe:
            print(f"✓ Lilypond Python 已找到")
            print(f"  路径: {generator.python_exe}")
        
        return True
    else:
        print("✗ Lilypond 未找到")
        print("\n请安装 Lilypond:")
        if generator.is_android:
            print("  pkg install lilypond")
        elif generator.system == 'Windows':
            print("  访问 https://lilypond.org/download.html")
        else:
            print("  使用包管理器安装，例如:")
            print("  sudo apt-get install lilypond  (Debian/Ubuntu)")
            print("  sudo yum install lilypond      (CentOS/RHEL)")
            print("  brew install lilypond          (macOS)")
        
        return False


if __name__ == '__main__':
    check_environment()
