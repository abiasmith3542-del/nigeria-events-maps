import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
import requests
import re

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

# 2. 尼日利亚完整地理经纬度库
NIGERIA_LOCATIONS = {
    "plateau": ["Plateau State", 9.4167, 9.5833],
    "jos": ["Jos", 9.8965, 8.8583],
    "bokkos": ["Bokkos (Plateau)", 9.3000, 8.9500],
    "abuja": ["Abuja (FCT)", 9.0578, 7.4951],
    "fct": ["Abuja (FCT)", 9.0578, 7.4951],
    "lagos": ["Lagos", 6.5244, 3.3792],
    "kano": ["Kano", 12.0022, 8.5920],
    "kaduna": ["Kaduna", 10.5105, 7.4165],
    "zaria": ["Zaria (Kaduna)", 11.0855, 7.7178],
    "borno": ["Borno State", 11.8311, 13.1509],
    "maiduguri": ["Maiduguri", 11.8311, 13.1509],
    "rivers": ["Rivers State", 4.8156, 7.0498],
    "port harcourt": ["Port Harcourt", 4.8156, 7.0498],
    "delta": ["Delta State", 5.7000, 6.0000],
    "warri": ["Warri", 5.5544, 5.7932],
    "asaba": ["Asaba", 6.1985, 6.7297],
    "adamawa": ["Adamawa State", 9.3333, 12.5000],
    "yola": ["Yola", 9.2035, 12.4954],
    "anambra": ["Anambra State", 6.2000, 7.0000],
    "awka": ["Awka", 6.2107, 7.0731],
    "onitsha": ["Onitsha", 6.1473, 6.7845],
    "benue": ["Benue State", 7.3333, 8.7500],
    "makurdi": ["Makurdi", 7.7337, 8.5214],
    "enugu": ["Enugu State", 6.4584, 7.5083],
    "oyo": ["Oyo State", 8.0000, 4.0000],
    "ibadan": ["Ibadan", 7.3775, 3.9470],
    "katsina": ["Katsina State", 12.9833, 7.6000],
    "zamfara": ["Zamfara State", 12.1667, 6.3333],
    "gusau": ["Gusau", 12.1628, 6.6614],
    "sokoto": ["Sokoto State", 13.0627, 5.2435],
    "yobe": ["Yobe State", 12.0000, 11.5000],
    "damaturu": ["Damaturu", 11.7470, 11.9608],
    "kogi": ["Kogi State", 7.7333, 6.6667],
    "lokoja": ["Lokoja", 7.7969, 6.7405],
    "nasarawa": ["Nasarawa State", 8.5000, 8.1667],
    "lafia": ["Lafia", 8.4912, 8.5150],
    "taraba": ["Taraba State", 8.0000, 10.5000],
    "jalingo": ["Jalingo", 8.8931, 11.3731],
    "bauchi": ["Bauchi State", 10.5000, 10.0000],
    "gombe": ["Gombe State", 10.2833, 11.1667],
    "jigawa": ["Jigawa State", 12.2500, 9.5000],
    "kebbi": ["Kebbi State", 11.5000, 4.0000],
    "kwara": ["Kwara State", 8.5000, 4.7500],
    "ilorin": ["Ilorin", 8.4799, 4.5418],
    "niger": ["Niger State", 10.0000, 6.0000],
    "minna": ["Minna", 9.5836, 6.5463],
    "ogun": ["Ogun State", 7.0000, 3.5000],
    "abeokuta": ["Abeokuta", 7.1475, 3.3619],
    "ondo": ["Ondo State", 7.1667, 5.0500],
    "osun": ["Osun State", 7.5000, 4.5000],
    "osogbo": ["Osogbo", 7.7827, 4.5606],
    "ekiti": ["Ekiti State", 7.6667, 5.2500],
    "edo": ["Edo State", 6.5000, 6.0000],
    "benin": ["Benin City", 6.3350, 5.6037],
    "cross river": ["Cross River State", 5.7500, 8.5000],
    "calabar": ["Calabar", 4.9757, 8.3417],
    "akwa ibom": ["Akwa Ibom State", 5.0000, 7.8333],
    "uyo": ["Uyo", 5.0377, 7.9128],
    "abia": ["Abia State", 5.4167, 7.5000],
    "umuahia": ["Umuahia", 5.5267, 7.4895],
    "imo": ["Imo State", 5.5000, 7.1667],
    "owerri": ["Owerri", 5.4856, 7.0351],
    "bayelsa": ["Bayelsa State", 4.7500, 6.2500],
    "yenagoa": ["Yenagoa", 4.9267, 6.2631],
    "ebonyi": ["Ebonyi State", 6.2500, 8.0000],
    "abakaliki": ["Abakaliki", 6.2649, 8.0527]
}

def clean_google_url(google_url):
    """
    通过向 Google 发起无痕轻量请求，获取其重定向后真正的媒体原始网址
    """
    try:
        # 使用不追踪、不带 cookie 的浏览器头部，快速碰一下重定向链接
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.head(google_url, headers=headers, allow_redirects=True, timeout=5)
        return res.url
    except:
        # 如果碰触超时或失败，采用正则尝试将某些明显的编码网址解出来，或者使用原网址保底
        return google_url

def analyze_text(text):
    text_lower = text.lower()
    for level, words in KEYWORDS.items():
        for word in words:
            if word in text_lower:
                return level, ZH_MAPPING[word]
    return None, None

def extract_location(title_text, summary_text=""):
    search_scope = (title_text + " " + summary_text).lower()
    for loc_key, info in NIGERIA_LOCATIONS.items():
        if loc_key in search_scope:
            lat_offset = random.uniform(-0.015, 0.015)
            lng_offset = random.uniform(-0.015, 0.015)
            return info[0], [info[1] + lat_offset, info[2] + lng_offset]
            
    return "Nigeria (General)", [9.05 + random.uniform(-0.6, 0.6), 7.49 + random.uniform(-0.6, 0.6)]

def fetch_rss_news():
    url = "https://news.google.com/rss/search?q=Nigeria+(attack+OR+kidnap+OR+protest+OR+killed+OR+accident+OR+clash+OR+bandits+OR+flooding+OR+rainstorm+OR+crash)&hl=en-NG&gl=NG&ceid=NG:en"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.content)
        incidents = []
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        for item in root.findall('.//item'):
            title = item.find('title').text
            raw_link = item.find('link').text
            pub_date_str = item.find('pubDate').text
            description = item.find('description').text if item.find('description') is not None else ""
            
            try:
                pub_date = datetime.strptime(pub_date_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            except:
                continue

            if pub_date < seven_days_ago:
                continue

            level, event_zh = analyze_text(title)
            if not level and description:
                level, event_zh = analyze_text(description)

            if not level:
                continue  

            loc_name, coords = extract_location(title, description)
            
            # 【升级核心】：将原有的 Google 间接链接，转化为纯净干净的原始媒体报社网页链接
            real_news_url = clean_google_url(raw_link)
            
            incidents.append({
                "title": title.split(" - ")[0], 
                "type": event_zh,
                "level": level,
                "date": pub_date.strftime("%Y-%m-%d"),
                "lat": coords[0],
                "lng": coords[1],
                "location": loc_name,
                "summary": f'<a href=" " target="_blank" style="color: #007bff; text-decoration: underline; font-weight: bold;">点击查看原始新闻链接 (Original News)</a >'
            })
            
        return incidents
    except Exception as e:
        print(f"数据抓取或解析失败: {e}")
        return []

if __name__ == "__main__":
    print("开始执行尼日利亚精准地名与原始链接解密爬虫...")
    new_data = fetch_rss_news()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
        
    print(f"抓取完成！成功存入 {len(new_data)} 条带干净原始链接的安全动态。")
