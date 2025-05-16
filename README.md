# chongchong-free-python

> [虫虫钢琴](https://www.gangqinpu.com/)midi下载工具。

## 项目简介

chongchong-free-python 是一个 python 工具，支持根据钢琴谱 id 或链接自动下载钢琴谱的 midi 文件，并支持指定保存目录。
本工具基于 [chongchong-free](https://github.com/hexadecimal233/chongchong-free) 项目，感谢原作者的创意与开源贡献！

## 特性

- 支持通过钢琴谱 id 或 url 下载
- 自动识别付费/免费曲目
- 自动保存为标准 midi 文件
- 支持自定义保存目录

## 安装

1. 克隆本仓库：

   ```bash
   git clone https://github.com/yfishyon/chongchong-free-python.git
   cd chongchong-free
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

```bash
python main.py -i <琴谱id或url> [-o <保存目录>]
```

- `-i` / `--id`：必填，钢琴谱id或者钢琴谱网址（如 942280 或 https://www.gangqinpu.com/cchtml/942280.htm ）
- `-o` / `--output`：选填，midi保存目录，默认 `output`

#### 示例

```bash
# 下载ID为942280的钢琴谱
python main.py -i 942280

# 下载指定URL的钢琴谱并保存到 mymidis 目录
python main.py -i https://www.gangqinpu.com/cchtml/942280.htm -o midi
```

## 注意事项

- 仅供学习交流，请勿用于商业用途。
- 如遇接口变动或下载失败，请联系作者或提交 issue。

## 参与贡献

欢迎提交 issue 或 pull request！

## 许可证

GPL-3.0 License
