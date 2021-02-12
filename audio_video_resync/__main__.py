#coding=utf-8

# Copyright (c) 2021 Haujet Zhao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

import argparse
import os
import shlex
import subprocess
import sys

def main():
    不马上退出 = False
    if len(sys.argv) == 1:
        不马上退出 = True

        print(f'''
你没有输入任何音频和视频文件，因此进入文字引导。
程序的用处主要是将视频中的音频替换为其它录音设备中的音频，例如：
  * 使用相机录像
  * 使用录音笔、手机随身录音
  * 将相机机内麦克风录制的声音，替换成录音笔中的高质量收音
录音笔录制的时间一般要长于视频片段的长度
因此，这个过程可以理解为：
    在音频（查找范围）中查找视频声音（查找目标）的偏移，再将视频中的声音替换
所以要先指定范围（音频文件），再指定目标（视频文件）
''')
        print(f'\n首先输入音频文件（查找范围）')
        sys.argv.append(得到输入文件())

        print(f'\n再输入视频文件（查找目标）')
        sys.argv.append(得到输入文件())


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
        print(f'\n总共有 {len(args.Video)} 个视频需要对齐，正在对齐第 {index + 1} 个：{video}')
        sync(args.Audio, video, 前移秒数, 片段秒数, args.sr, args.format, args.not_generate, args.plotit)

    if 不马上退出:
        input('\n所有任务处理完毕，按下回车结束')

def 得到输入文件():
    while True:
        用户输入 = input(f'请输入文件路径 或 直接拖入：')
        if 用户输入 == '':
            continue
        if os.path.exists(用户输入.strip('\'"')):
            输入文件 = 用户输入.strip('\'"')
            break
        else:
            print('输入的文件不存在，请重新输入')
    return 输入文件

def sync(within, find_offset_of, offset, trim, sr, format, not_generate, plotit):
    from .audio_offset_finder import find_offset
    for file in [within, find_offset_of]:
        if not os.path.exists(file):
            print(f'文件不存在，故跳过：{file}')
            return False

    offset, score = find_offset(within, find_offset_of, offset, trim, sr, plotit=plotit)

    print(f'偏移时长: {"{:.2f}".format(offset)} (秒)')

    # ffmpeg 命令
    if offset >= 0:
        ffmpeg_cmd = f'''ffmpeg -y -hide_banner -i "{find_offset_of}" -ss {offset} -i "{within}" -map 0:v:0 -map 1:a:0  -c:v copy -shortest "{find_offset_of}.sync.{"{:.2f}".format(offset)}.{format}"'''
    else:
        delay = int(abs(offset) * 1000)
        ffmpeg_cmd = f'''ffmpeg -y -hide_banner -i "{find_offset_of}" -i "{within}" -map 0:v:0 -map 1:a:0 -c:v copy -af "adelay=delays={delay}:all=1" -shortest "{find_offset_of}.sync.{"{:.2f}".format(offset)}.{format}"'''
    print(f'FFmpeg 合并命令：\n    {ffmpeg_cmd}\n')

    # 合并生成新视频
    if not not_generate:
        command_arg = shlex.split(ffmpeg_cmd)
        subprocess.run(command_arg)

if __name__ == '__main__':
    # sys.argv = ['test.py', '--find-offset-of', 'example\\蜀道难电脑5秒.mkv', '--within', 'example\\蜀道难手机20秒.aac', '--ffmpeg']
    main()