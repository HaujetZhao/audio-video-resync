set 名字=AudioSyncVideo

set 启动器名=launcher

set 启动器路径=..\launcher\%启动器名%.py

set 排除列表=exclude.txt

:: 将依赖包从打包目录移动到备用地方
move .\dist\%启动器名%\site-packages .\dist\site-packages
move .\dist\%启动器名%\bin .\dist\bin

:: 如果出错就结束
::if "%errorlevel%"=="1" goto :end

:: 打包启动器
..\Scripts\pyinstaller --noconfirm ^
					--hidden-import distutils.version ^
					--hidden-import uuid ^
					--hidden-import distutils.version ^
					--hidden-import imp ^
					--hidden-import unittest.mock ^
					--hidden-import cProfile ^
					--hidden-import xml.etree ^
					--hidden-import http.cookies ^
					--hidden-import json ^
					--hidden-import timeit ^
					--hidden-import math ^
					"%启动器路径%"

:: 构建排除列表
echo \__pycache__\ > %排除列表%
echo \bin\ >> %排除列表%
echo \test\ >> %排除列表%

:: 将依赖包移动到打包目录
move .\dist\site-packages .\dist\%启动器名%\site-packages 
move .\dist\bin .\dist\%启动器名%\bin 

:: exe 重命名
del .\dist\%启动器名%\_%名字%.exe
ren .\dist\%启动器名%\%启动器名%.exe  "___%名字%.exe"

:: 7z 压缩依赖文件
::del /F /Q 依赖文件-%名字%.7z
::7z a -t7z 依赖文件-%名字%.7z .\dist\%启动器名%\* -mx=9 -ms=200m -mf -mhc -mhcf  -mmt -r

:: 复制 py 源文件到单独 src 文件夹
rmdir /s /q .\dist\src
echo d | xcopy /s /y /EXCLUDE:%排除列表% ..\src .\dist\src

:: 7z 压缩源代码
del /F /Q 源代码-%名字%.7z
7z a -t7z 源代码-%名字%.7z .\dist\src\* -mx=9 -ms=200m -mf -mhc -mhcf  -mmt -r

:: 将源代码移动到 launcher 文件夹
move .\dist\src\* .\dist\%启动器名%
move .\dist\src\audio_offset_finder .\dist\launcher

:: 运行测试
cd ".\dist\%启动器名%"
"___%名字%.exe"

:end
pause