[Gitee](https://gitee.com/haujet/audio-video-synchronization)　|　[Github](https://github.com/HaujetZhao/audio-video-synchronization) 

### 用途

功能： 通过波形比较，得到两个音频的时间戳偏移值，合成新视频。 

大白话：将视频中的声音替换成录音笔中的声音，并自动对齐。

用途示例： 录制 vlog时，使用录音笔实现更好的收声，再将相机的视频与录音笔的录音同步。

### 背景

最近了解了录音笔，知道了在 vlog 中的一个技巧：

> * 使用相机录视频，得到高质量的视频
>
> * 将录音笔 / 手机带在身上，录音，得到高质量的收声
>
> 后期将 **相机的视频** 和 **录音笔的录音** 对齐，转换音轨，得到画面和音质都完美的视频。

但是这个替换过程是比较繁琐的，即便 Pr、Davinci 这些专业软件中有音频对齐功能，但光打开这些软件就够卡的了，导出时还要重新压制，实在是不好用。

如果只是为了将视频中的声音替换成录音笔的声音，我还需要一个轻量的工具。

经过搜索，在 github 上，我找到了 [BBC 的 audio-offset-finder](https://github.com/bbc/audio-offset-finder)，可以分析两段声音之间的偏移时间，但它是用 python2.7 写的，然后我找到了 [abramhindle 教授的](https://github.com/abramhindle) 的 [audio-offset-finder fork](https://github.com/abramhindle/audio-offset-finder) ，他用 python3 进行了重新实现和优化，[benkno 的 audio-offset-finder fork]( https://github.com/benkno/audio-offset-finder) 又做了 bash 处理的优化。

经上述两个 fork 的优化，audio-offset-finder 的大概原理就成了：

> 取音频 1 的大约前 30 秒片段，得到特征值，在音频 2 的前 15 分钟片段中，寻找特征最接近的地方，得到偏移值，再替换音频，生成新视频。

上述的缺点是：如果时间位移超过 15 分钟，就分析不好了。

所以我做了些改进：

> 依次取音频 1 、音频 2、……音频 n 的大约前 20 - 50 秒片段，得到特征值，在音频 2 ，以 15 分钟为一小段，对每一段依次寻找特征最接近的地方，直到找到合格的相似点，得到偏移值，再替换音频，生成新视频。

所以你可以用录音笔一次录上好几小时的音频，中途用相机录上几段视频，用一条命令，将这些视频的音频，全部替换成录音笔音频中的片段：

```
python __init__.py 录音笔音频.mp3 相机视频1.mp4 相机视频2.mp4 相机视频3.mp4
```

### 安装

需要提前安装上 FFmpeg

再用 pip 安装依赖：

```
pip install -r requirements.txt
```

### 使用

为了保证音频对齐的效果，请尽量确保所用的视频和音频时长大于20秒。

例子：

```
python __init__.py
```

```shell
python __init__.py 录音笔音频.mp3 相机视频1.mp4 相机视频2.mp4 相机视频3.mp4
```

第一种方式是直接运行，会有文字提示引导你：

```
> python __init__.py
正在初始化，请稍等

你没有输入任何音频和视频文件，因此进入文字引导。
程序的用处主要是将视频中的音频替换为其它录音设备中的音频，例如：
  * 使用相机录像
  * 使用录音笔、手机随身录音
  * 将相机机内麦克风录制的声音，替换成录音笔中的高质量收音
录音笔录制的时间一般要长于视频片段的长度
因此，这个过程可以理解为：
    在音频（查找范围）中查找视频声音（查找目标）的偏移，再将视频中的声音替换
所以要先指定范围（音频文件），再指定目标（视频文件）


首先输入音频文件（查找范围）
请输入文件路径 或 直接拖入：音频.mp3

再输入视频文件（查找目标）
请输入文件路径 或 直接拖入：视频.mp4

总共有 1 个视频需要对齐，正在对齐第 1 个：视频.mp4
```

第二种方式是命令行传递参数运行，可以一次传递 **一个音频** 和 **多个视频** ：

```
> python __init__.py -h
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

