#!/usr/bin/env python

# audio-video-resync
#
# Copyright (c) 2014 British Broadcasting Corporation
# Copyright (c) 2019 Abram Hindle
# Copyright (c) 2021 Haujet Zhao
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

from setuptools import setup

# python setup.py build sdist clean install & audio-video-resync
# twine upload -u USERNAME -p PASSWORD "dist/audio-video-resync-1.0.0.tar.gz"

setup(
    name='audio-video-resync',
    version='1.0.0',
    description='通过波形比较，得到两个音频的时间戳偏移值，合成新视频。 ',
    author='Yves Raimond and Abram Hindle and Haujet Zhao',
    author_email='yves.raimond@bbc.co.uk and hindle1@ualberta.ca and haujetzhao@qq.com',
    url='https://github.com/HaujetZhao/audio-video-resync',
    license='Apache License 2.0',
    packages=['audio_video_resync'],
    install_requires=[
        'scipy>=0.12.0',
        'numpy',
        'matplotlib',
        'librosa', 
        'icecream'
    ],
    entry_points={  # Option: console_scripts gui_scripts
            'console_scripts': [
                'audio-video-resync=audio_video_resync.__main__:main',
                'audio_video_resync=audio_video_resync.__main__:main'
                'AudioVideoResync=audio_video_resync.__main__:main',
            ]
    },

)

