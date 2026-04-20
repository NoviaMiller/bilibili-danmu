from stage1.get_danmu import run_danmu_analysis
from stage2.word_cloud import get_cloud_word

import os

BVID = 'BV1xx411c79H'

# 获取当前 combine01.py 所在的文件夹 (即 combine1 文件夹)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接出 combine1 下的 data 文件夹
target_data_dir = os.path.join(current_dir, 'data')

run_danmu_analysis(BVID, target_data_dir)
get_cloud_word(target_data_dir)