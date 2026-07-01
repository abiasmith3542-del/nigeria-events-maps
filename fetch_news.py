python
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests

# 1. 关键词和安全等级配置
KEYWORDS = {
    "high": ["terrorist", "terrorism", "boko haram", "explosion", "bomb", "killed", "blast", "attacked", "insurgent", "massacre"],
    "medium": ["bandit", "kidnap", "abduct", "ransom", "hostage", "gunmen", "robbery", "clash"],
    "low": ["protest", "riot", "accident", "crash", "collapse", "flooding", "strike"]
}

ZH_MAPPING = {
    "terrorist": "恐怖分子", "terrorism": "恐怖主义", "boko haram": "博科圣地", "explosion": "爆炸", "bomb": "炸弹事件", 
    "killed": "严重袭击", "blast": "爆炸袭击", "attacked": "武装袭击", "insurgent": "叛军活动", "massacre": "屠杀事件",
    "bandit": "土匪劫掠", "kidnap": "绑架事件", "abduct": "强行诱拐", "ransom": "索要赎金", "hostage": "人质事件", 
    "gunmen": "枪手袭击", "robbery": "抢劫案", "clash": "武装冲突", "protest": "抗议示威", "riot": "暴乱骚乱", 
    "accident": "交通事故", "crash": "车祸", "collapse": "建筑倒塌", "flooding": "洪涝灾害", "strike": "罢工游行"
}

# 2. 尼日利亚主要省会及地区的常用经纬度字典（用于粗略定位）
NIGERIA_LOCATIONS = {
    "abuja": [9.0578, 7.4951], "lagos": [6.5244, 3.3792], "kano": [12.0022, 8.5920], "kaduna": [10.5105, 7.4165],
    "port harcourt": [4.8156, 7.0498], "uyo": [5.0377, 7.9128], "ibadan": [7.3775, 3.9470], "maiduguri": [11.8311, 13.1509],
    "jos": [9.8965, 8.8583], "enugu": [6.4584, 7.5083], "benin": [6.3350, 5.6037], "calabar": [4.9757, 8.3417],
    "ilorin": [8.4799, 4.5418], "minna": [9.5836, 6.5463], "yola": [9.2035, 12.4954], "sokoto": [13.0627, 5.2435],
    "owerri": [5.4856, 7.0351], "warri": [5.5544, 5.7932], "makurdi": [7.7337, 8.5214], "bauchi": [10.3158, 9.8442],
    "ibeno": [4.5612, 7.9892], "bayelsa": [4.7500, 6.2500], "delta": [5.7000, 6.0000], "anambra": [6.2000, 7.0000]
}

def analyze_text(text):
    """分析文本，提取安全分类、中文标签和安全等级"""
    text_lower = text.lower()
    for level, words in KEYWORDS.items():
        for word in words:
            if word in text_lower:
                return level, ZH_MAPPING[word]
    return None, None

def extract_location(text):
    """匹配文本中的尼日利亚地名"""
    text_lower = text.lower()
    for loc, coords in NIGERIA_LOCATIONS.items():
        if loc in text_lower:
            return loc.capitalize(), coords
    # 如果找不到具体地名，默认放在首都阿布贾附近随机偏移，避免重叠
    import random
    return "Nigeria (General)", [9.05 + random.uniform(-0.5, 0.5), 7.49 + random.uniform(-0.5, 0.5)]

def fetch_rss_news():
    # 监控 Google 新闻关于尼日利亚安全关键词的 RSS 源
    url = "https://news.google.com/rss/search?q=Nigeria+(attack+OR+kidnap+OR+protest+OR+killed+OR+accident)&hl=en-NG&gl=NG&ceid=NG:en"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.content)
        incidents = []
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            pub_date_str = item.find('pubDate').text
            
            # 转换时间格式 (例如: Wed, 01 Jul 2026 12:00:00 GMT)
            try:
                pub_date = datetime.strptime(pub_date_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            except:
                continue

            if pub_date < seven_days_ago:
                continue  # 忽略超过7天的数据

            level, event_zh = analyze_text(title)
            if not level:
                continue  # 过滤不相关新闻

            loc_name, coords = extract_location(title)
            
            incidents.append({
                "title": title.split(" - ")[0], # 去除媒体后缀
                "type": event_zh,
                "level": level,
                "date": pub_date.strftime("%Y-%m-%d"),
                "lat": coords[0],
                "lng": coords[1],
                "location": loc_name,
                "summary": f"据尼日利亚当地媒体报道，发生一起【{event_zh}】相关事件。详情请查看原始新闻。"
            })
            
        return incidents
    except Exception as e:
        print(f"数据抓取失败: {e}")
        return []

if __name__ == "__main__":
    print("开始抓取尼日利亚安全动态...")
    new_data = fetch_rss_news()
    
    # 写入 data.json 供前端调用
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
        
    print(f"抓取完成，共存入 {len(new_data)} 条近一周的有效动态。")
