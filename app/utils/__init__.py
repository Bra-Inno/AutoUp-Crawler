"""
工具函数模块
"""

# 由于app.utils既是文件也是目录，这里需要特殊处理
# 直接从外层的utils.py文件导入函数

import os

# 获取app目录
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
utils_file = os.path.join(app_dir, 'utils.py')

# 动态加载utils.py
if os.path.exists(utils_file):
    with open(utils_file, 'r', encoding='utf-8') as f:
        exec(f.read(), globals())

__all__ = ['clean_filename', 'ensure_directory', 'get_file_extension']


