import requests
import json
import time
import xml.etree.ElementTree as ET
import csv
import os

# =============================================================================
# ------------------------------ 【 变量与函数 】 ------------------------------
# =============================================================================
BVID = "BV1nfSMBUEDr"
INFO_URL = f"https://api.bilibili.com/x/web-interface/view?bvid="
DANMU_URL = f"https://api.bilibili.com/x/v1/dm/list.so?oid="

current_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(current_dir, 'data')


def get_bilibili_video_info(bvid):
    """
    获取B站视频信息
    :param bvid: 视频BV号
    :return: 视频信息字典
    """
    # API接口
    url = INFO_URL + bvid
    
    # 请求头，模拟浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析JSON数据
        data = response.json()
        
        if data.get('code') == 0:
            # 提取视频信息
            video_info = data.get('data', {})
            return video_info
        else:
            print(f"获取视频信息失败: {data.get('message')}")
            return None
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

def print_video_info(video_info):
    """
    打印视频信息
    :param video_info: 视频信息字典
    """
    if video_info:
        # 输出视频信息
        print("视频信息:")
        print(f"标题: {video_info.get('title')}")
        print(f"UP主: {video_info.get('owner', {}).get('name')}")
        print(f"播放量: {video_info.get('stat', {}).get('view')}")
        print(f"弹幕数: {video_info.get('stat', {}).get('danmaku')}")
        print(f"点赞数: {video_info.get('stat', {}).get('like')}")
        print(f"投币数: {video_info.get('stat', {}).get('coin')}")
        print(f"收藏数: {video_info.get('stat', {}).get('favorite')}")
        print(f"分享数: {video_info.get('stat', {}).get('share')}")
        print(f"视频简介: {video_info.get('desc')}")
        pubdate = video_info.get('pubdate')
        if pubdate:
            # 转换时间戳为可读格式
            pubdate_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pubdate))
            print(f"发布时间: {pubdate_str}")
        print(f"视频长度: {video_info.get('duration')}秒")
        print(f"视频分区: {video_info.get('tname') if video_info.get('tname') else '无'}")
    else:
        print("未获取到视频信息")


def get_bilibili_video_danmu(bvid):
    """
    获取B站视频弹幕信息
    :param bvid: 视频BV号
    :return: 弹幕信息列表
    """
    # 先获取视频信息以获取cid
    video_info = get_bilibili_video_info(bvid)
    if not video_info:
        print("无法获取视频信息，无法获取弹幕")
        return []
    
    # 获取cid
    cid = video_info.get('cid')
    if not cid:
        print("无法获取视频cid，无法获取弹幕")
        return []
    
    # 弹幕API接口
    url = DANMU_URL + str(cid)

    # 请求头，模拟浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析XML数据
        root = ET.fromstring(response.content)
        
        # 提取弹幕信息
        danmu_list = []
        for d in root.findall('.//d'):
            # 获取弹幕属性
            p = d.attrib.get('p', '').split(',')
            if len(p) >= 5:
                danmu = {
                    'time': float(p[0]),  # 弹幕出现时间（秒）
                    'mode': int(p[1]),    # 弹幕模式
                    'fontsize': int(p[2]),  # 字体大小
                    'color': int(p[3]),    # 颜色
                    'timestamp': int(p[4]),  # 发送时间戳
                    'pool': int(p[5]) if len(p) > 5 else 0,  # 弹幕池
                    'uid_hash': p[6] if len(p) > 6 else '',  # 用户ID哈希
                    'uname': p[7] if len(p) > 7 else '',  # 用户名
                    'content': d.text  # 弹幕内容
                }
                danmu_list.append(danmu)
        
        # 按照时间升序排序
        danmu_list.sort(key=lambda x: x['time'])
        return danmu_list
    except Exception as e:
        print(f"获取弹幕失败: {str(e)}")
        return []

def get_danmu_mode(num: int) -> str:
    """
    根据数字获取弹幕模式
    :param num: 弹幕模式数字
    :return: 弹幕模式名称
    """
    mode_map = {
        1: "滚动弹幕",
        4: "顶部弹幕",
        5: "底部弹幕",
        7: "逆向弹幕",
        8: "高级弹幕",
        9: "代码弹幕",
        10: "特殊弹幕"
    }
    return mode_map.get(num, f"未知模式({num})")


def get_danmu_color(num: int) -> str:
    """
    根据数字获取弹幕颜色
    :param num: 十进制颜色值
    :return: 十六进制代码
    """
    # 将十进制颜色转换为十六进制
    hex_color = f"#{num:06x}".upper()
    return hex_color

def get_send_time(timestamp: int) -> str:
    """
    根据时间戳获取发送时间
    :param timestamp: 时间戳
    :return: 发送时间字符串
    """
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(timestamp))

def get_time(time: int) -> str:
    """
    根据时间戳获取时间字符串
    :param time: 时间戳
    :return: 时间字符串
    """
    return f"{int(time // 60):02d}:{int(time % 60):02d}"

def print_danmu_info(danmu_list):
    """
    打印弹幕信息
    :param danmu_list: 弹幕信息列表
    """
    if danmu_list:
        print(f"\n弹幕信息 (共{len(danmu_list)}条):")
        # 只打印前20条弹幕，避免输出过多
        for i, danmu in enumerate(danmu_list[:20]):
            # 转换时间格式
            time_str = get_time(danmu['time'])
            # 转换发送时间格式
            send_time_str = get_send_time(danmu['timestamp'])
            print(f"[{i+1}] {time_str} - {danmu['content']} (发送时间: {send_time_str})")
        
        if len(danmu_list) > 20:
            print(f"... 还有{len(danmu_list)-20}条弹幕未显示")
    else:
        print("未获取到弹幕信息")

def save_danmu(bvid, danmu_list, data_dir: str):
    """
    保存弹幕信息到CSV文件
    :param danmu_list: 弹幕信息列表
    """

    # 确保data文件夹存在
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # CSV文件路径
    csv_file = os.path.join(data_dir, bvid + 'danmu.csv')
    
    # 全部保存幕信息
    save_list = danmu_list[:]
    
    if save_list:
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                # 定义表头
                fieldnames = ['time', 'mode', 'fontsize', 'color', 'send_time', 'pool', 'uid_hash', 'uname', 'content']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入数据
                for i, danmu in enumerate(save_list):
                    # 转换字段格式
                    row = {
                        'time': get_time(danmu['time']),
                        'mode': get_danmu_mode(danmu['mode']),
                        'fontsize': danmu['fontsize'],
                        'color': get_danmu_color(danmu['color']),
                        'send_time': get_send_time(danmu['timestamp']),
                        'pool': danmu['pool'],
                        'uid_hash': danmu['uid_hash'],
                        'uname': danmu['uname'],
                        'content': danmu['content']
                    }
                    writer.writerow(row)
                    
                    # 每保存100条输出一次
                    if (i + 1) % 100 == 0:
                        print(f"已保存{i + 1}条弹幕")
            print(f"成功保存{len(save_list)}条弹幕到 {csv_file}")
        except Exception as e:
            print(f"保存弹幕失败: {str(e)}")
    else:
        print("没有弹幕信息可保存")


# =============================================================================
# ------------------------------ 【主函数】 ------------------------------
# =============================================================================

# 主函数

def run_danmu_analysis(bvid: str, data_dir: str):
    """
    运行弹幕分析
    """
    # 视频BV号
    
    # 获取视频信息
    video_info = get_bilibili_video_info(bvid)

    # 打印视频信息
    # print_video_info(video_info)
    
    # 获取弹幕信息
    danmu_list = get_bilibili_video_danmu(bvid)
    
    # 打印弹幕信息
    # print_danmu_info(danmu_list)

    # 保存弹幕信息
    save_danmu(BVID ,danmu_list, data_dir)

if __name__ == "__main__":
    run_danmu_analysis(BVID, DATA_DIR)
