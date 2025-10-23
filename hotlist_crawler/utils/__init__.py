"""
工具函数模块
"""

import os

# 获取app目录
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
utils_file = os.path.join(app_dir, "utils.py")

# 动态加载utils.py
if os.path.exists(utils_file):
    with open(utils_file, "r", encoding="utf-8") as f:
        exec(f.read(), globals())
