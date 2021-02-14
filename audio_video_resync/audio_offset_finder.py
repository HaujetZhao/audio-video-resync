# audio-offset-finder
#
# Copyright (c) 2014 British Broadcasting Corporation
# Copyright (c) 2018 Abram Hindle
# Copyright (c) 2021 Haujet Zhao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# 内存分析：
# @profile
# python -m memory_profiler example.py

import math
import os
import shlex
import tempfile
import warnings
from subprocess import Popen, PIPE

# `from scikits.talkbox.features.mfcc import mfcc` is used for python2.7
# we use librosa in python3 to reimplement
import librosa
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic
from scipy.io import wavfile


def mfcc(音频文件, nwin=256, n_fft=512, 音频采样率=16000, n_mfcc=20):
    return [np.transpose(librosa.feature.mfcc(y=音频文件, sr=音频采样率, n_fft=n_fft, win_length=nwin, n_mfcc=n_mfcc))]

def add_feature(mfcc1, 音频平方均根):
    tmfcc1 = np.zeros((mfcc1.shape[0], mfcc1.shape[1] + 音频平方均根.shape[0]))
    n = mfcc1.shape[0]
    m = mfcc1.shape[1]
    w = 音频平方均根.shape[0]
    tmfcc1[0:n,0:m] = mfcc1[0:n,0:m]
    tmfcc1[0:n,m:m+w]   = np.transpose(音频平方均根[0:w, 0:n])
    return tmfcc1

def get_audio(file1, 音频采样率=16000):
    '''
    Haujet Zhao：这里涉及到了音频处理领域的专业名词，具体是怎么分析音频片段相似度的我也看不懂，只能将部分难懂的名词尽可能翻译成中文。

    :param file1:
    :param 音频采样率:
    :param trim:
    :return: 重采样后的临时音频文件、mfcc1、无零的音频数据、平方均根列表
    '''
    临时音频文件 = file1
    # Removing warnings because of 18 bits block size
    # outputted by ffmpeg
    # https://trac.ffmpeg.org/ticket/1843
    # warnings.simplefilter("ignore", wavfile.WavFileWarning)
    warnings.simplefilter("ignore")
    a1 = wavfile.read(临时音频文件, mmap=True)[1] / (2.0 ** 15)
    # We truncate zeroes off the beginning of each signals
    # (only seems to happen in ffmpeg, not in sox)
    a1 = ensure_non_zero(a1)
    # print(f"{file1} 采样数: {a1.shape[0]}")

    # Mel频率倒谱系数 Mel-frequency cepstral coefficients (MFCCs)
    Mel频率倒谱系数 = mfcc(a1, nwin=256, n_fft=512, 音频采样率=音频采样率, n_mfcc=26)[0]
    Mel频率倒谱系数 = std_mfcc(Mel频率倒谱系数)

    # 得到每一帧的平方均根 root-mean-square (RMS)
    平方均根列表 = librosa.feature.rms(a1)

    # 光谱矩心 spectral centroid
    光谱矩心 = librosa.feature.spectral_centroid(y=a1, sr=音频采样率)

    # 偏移频率 roll-off frequency
    偏移频率 = librosa.feature.spectral_rolloff(y=a1, sr=音频采样率, roll_percent=0.1)

    # Constant-Q chromagram
    chroma_cq1 = librosa.feature.chroma_cqt(y=a1, sr=音频采样率, n_chroma=12)

    # 光谱通量起始强度包络线 spectral flux onset strength envelope
    起始包络线 = librosa.onset.onset_strength(y=a1, sr=音频采样率, n_mels=int(音频采样率 / 800))

    # 主要局部脉冲（PLP）估计 Predominant local pulse (PLP) estimation
    脉冲 = librosa.beat.plp(onset_envelope=起始包络线, sr=音频采样率)
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, 平方均根列表)
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, 偏移频率 / 音频采样率)
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, 光谱矩心 / 音频采样率)
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, chroma_cq1)
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, 起始包络线.reshape(1,起始包络线.shape[0]))
    Mel频率倒谱系数 = add_feature(Mel频率倒谱系数, 脉冲.reshape(1,起始包络线.shape[0]))

    return 临时音频文件, Mel频率倒谱系数, a1, 平方均根列表

def find_offset(要在其中查找的音频, 视频, 母音频偏移秒数, 单位片段秒数, 音频采样率=16000, correl_nframes=1000, plotit=False):

    # 子音频在母音频中找偏移值
    母音频 = convert_and_trim(要在其中查找的音频, 音频采样率, trim=None, offset=母音频偏移秒数)
    母音频数据 = wavfile.read(母音频, mmap=True)[1]
    母音频数据长度 = len(母音频数据)
    print(f'母音频数据长度：{母音频数据长度}')
    # ic(母音频数据长度)

    子音频 = convert_and_trim(视频, 音频采样率, 单位片段秒数, offset=0)
    子音频数据 = wavfile.read(子音频, mmap=True)[1]
    子音频数据长度 = len(子音频数据)
    子音频时长 = 子音频数据长度 / 音频采样率
    del 子音频数据
    # 不能从子音频的第一帧开始取片段进行分析
    # 因为录制者有可能先按下了录像开关，然后过了几秒钟才按下录音笔开关
    # 所以要对采样的起始点添加一个偏移
    子音频前移时长 = min(子音频时长 * 1 / 5, 180)
    print(f'子音频取样开始点：{"{:.2f}".format(子音频前移时长)}s')
    # ic(子音频前移时长)
    子音频 = convert_and_trim(视频, 音频采样率, 单位片段秒数, offset=子音频前移时长)



    单位片段数据长度 = 单位片段秒数 * 音频采样率
    总音频段数 = math.ceil(母音频数据长度 / 单位片段数据长度)
    print(f'单位片段数据长度：{单位片段数据长度}')
    print(f'母音频分段数：{总音频段数}')

    clip_tmp = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_clip_', suffix='.wav')
    clip_tmp_name = clip_tmp.name
    clip_tmp.close()

    及格分 = 8
    最高分 = 0
    总移值 = 母音频偏移秒数
    新片段向前偏移秒数 = 0

    for i in range(总音频段数):
        print(f'匹配及格分：{及格分}')
        print(f'与母音频第 {i+1} 段比较中……')
        start = i * 单位片段数据长度
        if i > 0:
            新片段向前偏移秒数 = 60
            start -= 新片段向前偏移秒数 * 音频采样率
        end = min(i * 单位片段数据长度 + 单位片段数据长度, 母音频数据长度 - 1)
        wavfile.write(clip_tmp_name, 音频采样率, 母音频数据[start:end])

        audio1 = get_audio(clip_tmp_name, 音频采样率)
        audio2 = get_audio(子音频, 音频采样率)

        offset, score, c = find_clip_offset(audio1, audio2, 音频采样率)
        print(f'母音频第 {i+1} 段匹配得分：{"{:.2f}".format(score)} ')
        # ic(score)
        if score > 最高分:
            最高分 = score
            总移值 = i * 单位片段秒数 + 母音频偏移秒数 + offset - 子音频前移时长 - 新片段向前偏移秒数
        if score > 及格分:
            print(f'母音频第 {i + 1} 段匹配得分品优，不再继续分析')
            break
    print(f'最终匹配得分：{"{:.2f}".format(score)}')

    # 显示具体分数的图表
    if plotit:
        plt.figure(figsize=(8, 4))
        plt.plot(c)
        plt.show()

    return 总移值, 最高分

def find_clip_offset(audio1, audio2, 音频采样率=16000, correl_nframes=1000):
    临时音频文件1, mfcc1, 音频数据1, 平方均根1 = audio1
    临时音频文件2, mfcc2, 音频数据2, 平方均根2 = audio2

    # 得到列表，表示每一帧偏移后，匹配的程度，取最高值为位移帧
    c = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    max_k_index = np.argmax(c)

    偏移 = max_k_index * (音频数据1.shape[0]/平方均根1.shape[1]) / float(音频采样率) # * over / sample rate
    得分 = (c[max_k_index] - np.mean(c)) / max(np.std(c), 1) # standard score of peak
    # print(f'平均：{c.mean()}，最高：{c.max()}，标准偏差：{c.std()}，得分：{得分}')


    return 偏移, 得分, c

def ensure_non_zero(signal):
    # We add a little bit of static to avoid
    # 'divide by zero encountered in log'
    # during MFCC computation
    # 添加一点静态值，以避免在 MFCC 计算中的除以非0值错误
    signal += np.random.random(len(signal)) * 10**-10
    return signal

def make_similar_shape(mfcc1,mfcc2):
    n1, mdim1 = mfcc1.shape #
    n2, mdim2 = mfcc2.shape
    # print((nframes,(n1,mdim1),(n2,mdim2)))
    if (n2 < n1):
        t = np.zeros((n1,mdim2))
        t[0:n2,0:mdim2] = mfcc2[0:n2,0:mdim2]
        mfcc2 = t
    elif (n2 > n1):
        return make_similar_shape(mfcc2,mfcc1)
    return (mfcc1,mfcc2)

def cross_correlation(mfcc1, mfcc2, nframes):
    n1, mdim1 = mfcc1.shape # 母
    n2, mdim2 = mfcc2.shape # 子

    if n2 <= nframes:
        nframes = int(n2 * 3 / 4)

    if n1 <= nframes:
        nframes = n1

    ic(nframes)

    # 如果视频长度不够，就把它补起来
    if (n2 < nframes):
        t = np.zeros((nframes,mdim2))
        t[0:n2,0:mdim2] = mfcc2[0:n2,0:mdim2]
        mfcc2 = t

    # 向后位移一位，查找的次数
    n = n1 - nframes + 1

    # 计算结果的列表
    c = np.zeros(n)
    for k in range(n):
        # 将两个片段特征值依次相乘，再加和，纯性对数标准化，对齐的那一点，它的值会特别的高
        cc = np.sum(np.multiply(mfcc1[k:k+nframes], mfcc2[:nframes]), axis=0)
        c[k] = np.linalg.norm(cc,1)
    return c

def std_mfcc(mfcc):
    return (mfcc - np.mean(mfcc, axis=0)) / np.std(mfcc, axis=0)

def convert_and_trim(afile, sr, trim, offset):
    tmp = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_', suffix='.wav')
    tmp_name = tmp.name
    tmp.close()

    if not trim:
        command = f'ffmpeg -loglevel panic -i "{afile}" -ac 1 -ar {sr} -ss {offset} -vn -c:a pcm_s16le "{tmp_name}"'
    else:
        command = f'ffmpeg -loglevel panic -i "{afile}" -ac 1 -ar {sr} -ss {offset} -t {trim} -vn -c:a pcm_s16le "{tmp_name}"'
    command = shlex.split(command)

    psox = Popen(command, stderr=PIPE)
    psox.communicate()

    if not psox.returncode == 0:
        raise Exception("FFMpeg failed")

    # print(f'tmp_name: {tmp_name}')
    return tmp_name

class BatchOffsetFinder:
    def __init__(self, haystack_filenames, fs=8000, trim=60*15, correl_nframes=1000):
        self.fs = fs
        self.trim = trim
        self.correl_nframes = correl_nframes
        self.haystacks = []

        for filename in haystack_filenames:
            self.haystacks.append((filename, get_audio(filename, fs, trim)))

    def find_offset(self, needle):
        best_score = 0
        best_filename = ""
        best_offset = 0
        needle_audio = get_audio(needle, self.fs, self.trim)
        for (haystack_filename, haystack_audio) in self.haystacks:
            offset, score = find_clip_offset(haystack_audio, needle_audio, self.fs, self.correl_nframes)
            if (score > best_score):
                best_score = score
                best_filename = haystack_filename
                best_offset = offset

        print("Cleaning up %s" % str(needle_audio[0]))
        os.remove(needle_audio[0])

        return best_filename, best_offset, best_score

    def __del__(self):
        for haystack in self.haystacks:
            print("Cleaning up %s" % str(haystack[1][0]))
            os.remove(haystack[1][0])
