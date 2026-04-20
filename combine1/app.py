import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import base64
import jieba
import numpy as np
import random
from PIL import Image, ImageDraw
from wordcloud import WordCloud
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from stage1.get_danmu import get_bilibili_video_info, get_bilibili_video_danmu, save_danmu

app = FastAPI()
current_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(current_dir, "data")
TEMPLATE_PATH = os.path.join(current_dir, "templates", "index.html")


def pink_purple_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    colors = [
        (255, 182, 193), (255, 192, 203), (255, 105, 180), (255, 20, 147),
        (220, 20, 60), (255, 69, 0), (255, 0, 127),
        (218, 112, 214), (221, 160, 221), (186, 85, 211), (147, 112, 219), (138, 43, 226),
    ]
    color = random.choice(colors)
    return f'rgb({color[0]}, {color[1]}, {color[2]})'


def generate_wordcloud_base64(data_dir: str) -> str:
    df = pd.read_csv(os.path.join(data_dir, "danmu.csv"))
    text_data = ' '.join(df['content'].astype(str).tolist())

    # 分词并过滤
    seg_list = jieba.lcut(text_data)
    filtered_words = [w.strip() for w in seg_list if len(w.strip()) > 1]

    # 统计词频
    from collections import Counter
    word_freq = Counter(filtered_words)

    # 使用词频字典生成词云（避免重复）
    font_path = os.path.join(data_dir, 'STKAITI.TTF')
    wc = WordCloud(
        font_path=font_path,
        background_color='white',
        width=800, height=600,
        max_words=100,
        color_func=pink_purple_color_func,
        collocations=False,  # 禁用词组搭配，避免重复
        relative_scaling=0.5,  # 调整词频缩放
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.post("/analyze", response_class=JSONResponse)
async def analyze(bvid: str = Form(...)):
    bvid = bvid.strip()
    if not bvid:
        return JSONResponse({"error": "请输入 BVID"}, status_code=400)

    os.makedirs(DATA_DIR, exist_ok=True)

    video_info = get_bilibili_video_info(bvid)
    if not video_info:
        return JSONResponse({"error": "无法获取视频信息，请检查 BVID 是否正确"}, status_code=400)

    danmu_list = get_bilibili_video_danmu(bvid)
    if not danmu_list:
        return JSONResponse({"error": "未获取到弹幕，视频可能没有弹幕或请求失败"}, status_code=400)

    # 保存弹幕到 data/danmu.csv（词云固定读这个文件）
    csv_path = os.path.join(DATA_DIR, bvid + "danmu.csv")
    save_danmu(bvid ,danmu_list, DATA_DIR)

    wordcloud_b64 = generate_wordcloud_base64(DATA_DIR)

    import time as time_mod2
    pubdate = video_info.get('pubdate')
    pub_str = time_mod2.strftime("%Y-%m-%d %H:%M:%S", time_mod2.localtime(pubdate)) if pubdate else '未知'

    return JSONResponse({
        "title": video_info.get('title', ''),
        "author": video_info.get('owner', {}).get('name', ''),
        "view": video_info.get('stat', {}).get('view', 0),
        "danmaku": video_info.get('stat', {}).get('danmaku', 0),
        "like": video_info.get('stat', {}).get('like', 0),
        "coin": video_info.get('stat', {}).get('coin', 0),
        "favorite": video_info.get('stat', {}).get('favorite', 0),
        "pubdate": pub_str,
        "saved_count": len(danmu_list),
        "csv_path": csv_path,
        "wordcloud": wordcloud_b64,
    })