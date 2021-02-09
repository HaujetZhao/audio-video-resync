#!/usr/bin/python

# audio-offset-finder
#
# Copyright (c) 2014 British Broadcasting Corporation
# Copyright (c) 2018 Abram Hindle
# Copyright (c) 2019 Benjamin Knowles
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from audio_offset_finder.audio_offset_finder import find_offset, get_audio
import argparse, sys, os
import subprocess, shlex
from icecream import ic

def main():
    parser = argparse.ArgumentParser(
        description='''功能：      通过波形比较，得到两个音频的时间戳偏移值，合成新视频。
                       用途示例：  录制 vlog 时，使用录音笔实现更好的收声，再将相机的视频与录音笔的录音同步。''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('Audio', type=str, help='外置音频，在这个文件中进行匹配')
    parser.add_argument('Video', nargs='+',  type=str, help='对此视频文件匹配偏移（可一次添加多个文件）')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    parser.add_argument('--offset', metavar='Minutes', type=int, default=0, help='忽略外置音频的前多少分钟')
    parser.add_argument('--trim', metavar='Minutes', type=int, default=15, help='只使用音频文件的前多少分钟进行分析')
    parser.add_argument('--sr', metavar='SampleRate', type=int, default=16000, help='重新采样进行分析时，使用什么采样率')
    parser.add_argument('--format', metavar='Format', type=str, default='mp4', help='输出文件的格式，例如：mp4、mkv')
    parser.add_argument('--not-generate',action='store_true', help='不要运行 FFMPEG 生成同步好的新视频')
    parser.add_argument('--plotit',action='store_true', help='展示相关性计算结果的图示')

    args = parser.parse_args()

    片段秒数 = args.trim * 60
    前移秒数 = args.offset * 60
    for index, video in enumerate(args.Video):
        print(f'总共有 {len(args.Video)} 个视频需要对齐，正在对齐第 {index + 1} 个：{video}')
        sync(args.Audio, video, 前移秒数, 片段秒数, args.sr, args.format, args.not_generate, args.plotit)


def sync(within, find_offset_of, offset, trim, sr, format, not_generate, plotit):

    offset, score = find_offset(within, find_offset_of, offset, trim, sr, plotit=plotit)

    print(f"偏移: {str(offset)} (秒)")

    # ffmpeg 命令
    if offset >= 0:
        ffmpeg_cmd = f'''ffmpeg -y -hide_banner -i "{find_offset_of}" -ss {offset} -i "{within}" -map 0:v:0 -map 1:a:0  -c:v copy -shortest "{find_offset_of}.sync.{"{:.2f}".format(offset)}.{format}"'''
    else:
        ffmpeg_cmd = f'''ffmpeg -y -hide_banner -ss {offset} -i "{find_offset_of}" -i "{within}" -map 0:v:0 -map 1:a:0  -c:v copy -shortest "{find_offset_of}.sync.{"{:.2f}".format(offset)}.{format}"'''
    print(f'FFmpeg 合并命令：\n    {ffmpeg_cmd}')

    # 合并生成新视频
    if not not_generate:
        command_arg = shlex.split(ffmpeg_cmd)
        subprocess.run(command_arg)

if __name__ == '__main__':
    # sys.argv = ['test.py', '--find-offset-of', 'example\\蜀道难电脑5秒.mkv', '--within', 'example\\蜀道难手机20秒.aac', '--ffmpeg']
    main()
    # import math
    # ic(math.ceil(0.1))

# python test.py --find-offset-of example\noisy.mp3 --within example\clean.mp3 --ffmpeg
