import os
import sys
import pathlib
sys.path.append(str(pathlib.Path(os.path.abspath(__file__)).parent / 'site-packages')) # 将当前目录导入 python 寻找 package 和 moduel 的变量
import __init__

__init__.main()
