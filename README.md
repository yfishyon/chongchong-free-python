# 虫虫钢琴谱下载工具 (改进版)

基于 [yfishyon/chongchong-free-python](https://github.com/yfishyon/chongchong-free-python) 改进

## 新增功能

### 乐谱生成功能 (使用 Lilypond 渲染)

现在支持从 CCMZ 文件生成高质量的乐谱图片，流程为：

```
CCXML (from CCMZ v2) → MusicXML → LY → PNG
```

这比原有的图片下载方式更好地还原了原始乐谱格式。

### 转换逻辑

CCXML 到 MusicXML 的转换逻辑参考自:
[bszapp/ccmz-to-midi (ccxml-to-musicxml 分支)](https://github.com/bszapp/ccmz-to-midi/tree/ccxml-to-musicxml)

## 安装

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Lilypond

#### Windows

访问 [Lilypond 官网](https://lilypond.org/download.html) 下载安装

或者使用 lilyponddist:

```bash
# 工具会自动检测 %LOCALAPPDATA%\lilyponddist 路径
```

#### Linux/macOS

```bash
# Debian/Ubuntu
sudo apt-get install lilypond

# CentOS/RHEL
sudo yum install lilypond

# macOS
brew install lilypond
```

#### Android (Termux)

程序会自动尝试安装：

```bash
pkg install lilypond
```

或手动安装：

```bash
pkg update
pkg install lilypond
```

### 3. 检查环境

```bash
python main.py --check-env
```

## 使用方法

### 下载 MIDI (默认)

```bash
python main.py -i <乐谱ID或URL> [-o 输出目录]
```

### 生成乐谱 (新方式 - 使用 Lilypond)

```bash
python main.py -i <乐谱ID或URL> -score [-o 输出目录]
```

生成的文件：

- `*.musicxml` - MusicXML 格式乐谱(中间文件)
- `*.png` - 渲染的乐谱图片(每页一个文件)

### 下载乐谱图片 (旧方式 - 直接下载)

```bash
# 下载为 PNG
python main.py -i <乐谱ID或URL> -png [-o 输出目录]

# 下载为 PDF
python main.py -i <乐谱ID或URL> -pdf [-o 输出目录]
```

## 示例

```bash
# 下载 MIDI
python main.py -i 2586441

# 使用 Lilypond 生成乐谱
python main.py -i 2586441 -score

# 使用 URL
python main.py -i "https://www.gangqinpu.com/html/26230.htm" -score

# 指定输出目录
python main.py -i 2586441 -score -o "./my_scores"

# 检查环境配置
python main.py --check-env
```

## 项目结构

```
chongchong-free-python/
├── main.py                    # 主程序
├── ccmz.py                    # CCMZ 解析和 MIDI 生成
├── ccxml_to_musicxml.py       # CCXML 到 MusicXML 转换器
├── score_generator.py         # 乐谱生成器 (使用 Lilypond)
├── requirements.txt
└── README.md
```

## 技术细节

### CCXML 到 MusicXML 转换

转换器处理以下元素：

- ✓ 音符、休止符、和弦
- ✓ 时值(全音符、二分音符、四分音符等)
- ✓ 附点
- ✓ 符干方向
- ✓ 音高、临时升降号
- ✓ 小节线、反复记号
- ✓ 调号、拍号
- ✓ 速度标记
- ✓ 换行、换页
- ✓ 多声部
- ○ 装饰音(部分支持)
- ○ 连音、圆滑线(部分支持)

### 环境检测

程序会自动检测：

1. 操作系统类型 (Windows/Linux/macOS/Android)
2. Lilypond 安装位置
3. musicxml2ly 工具可用性
4. 在 Android (Termux) 环境下自动尝试安装

### 独立转换器

`MusicXML → LY` 转换使用 Lilypond 自带的 `musicxml2ly.py`（随 lilyponddist 安装）。

## 代理设置

如果需要使用代理访问 GitHub:

### Windows (PowerShell)

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
$env:ALL_PROXY="socks5://127.0.0.1:7890"

git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

### Linux/macOS

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890

git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

## 故障排查

### Lilypond 未找到

运行环境检测：

```bash
python main.py --check-env
```

如果显示未找到，请手动安装 Lilypond 并确保在 PATH 中，或者在 Windows 上安装到标准路径。

### 转换失败

1. 检查 MusicXML 文件是否正确生成
2. 手动测试 musicxml2ly 命令
3. 查看错误信息中的具体提示

### 内存不足

对于超大乐谱，可能需要更多内存。可以尝试：

1. 减少渲染分辨率
2. 分段处理

## 许可证

继承原项目许可证。

CCXML 转换逻辑基于 [bszapp/ccmz-to-midi](https://github.com/bszapp/ccmz-to-midi) 项目。

## 致谢

- 原项目: [yfishyon/chongchong-free-python](https://github.com/yfishyon/chongchong-free-python)
- CCXML 转换逻辑: [bszapp/ccmz-to-midi](https://github.com/bszapp/ccmz-to-midi)
- Lilypond: [lilypond.org](https://lilypond.org)
