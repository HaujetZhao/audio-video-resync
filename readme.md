### 用途

功能： 通过波形比较，得到两个音频的时间戳偏移值，合成新视频。 

用途示例： 录制 vlog时，使用录音笔实现更好的收声，再将相机的视频与录音笔的录音同步。

### 安装

需要提前安装上 FFmpeg

再用 pip 安装依赖：

```
pip install -r requirements.txt
```

### 使用

例子：

```shell
python __init__.py 录音笔音频.mp3 相机视频1.mp4 相机视频2.mp4 相机视频3.mp4
```

用法：

```bash
python __init__.py -h
usage: __init__.py [-h] [--version] [--offset Minutes]
                   [--trim Minutes] [--sr SampleRate]
                   [--format Format] [--not-generate] [--plotit]
                   Audio Video [Video ...]

功能： 通过波形比较，得到两个音频的时间戳偏移值，合成新视频。 用途示例： 录制 vlog
时，使用录音笔实现更好的收声，再将相机的视频与录音笔的录音同步。

positional arguments:
  Audio             外置音频，在这个文件中进行匹配
  Video             对此视频文件匹配偏移（可一次添加多个文件）

optional arguments:
  -h, --help        show this help message and exit
  --version         show program's version number and exit
  --offset Minutes  忽略外置音频的前多少分钟 (default: 0)
  --trim Minutes    只使用音频文件的前多少分钟进行分析 (default: 15)
  --sr SampleRate   重新采样进行分析时，使用什么采样率 (default: 16000)
  --format Format   输出文件的格式，例如：mp4、mkv (default: mp4)
  --not-generate    不要运行 FFMPEG 生成同步好的新视频 (default: False)
  --plotit          展示相关性计算结果的图示 (default: False)
```

