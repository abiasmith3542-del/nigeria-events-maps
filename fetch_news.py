import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
import requests
import time
import re
from difflib import SequenceMatcher

# 1. 用户提供的完善版关键词字典（全面涵盖9大类）
KEYWORDS_MAPPING = {
    "terrorist": "恐怖分子", "terrorism": "恐怖主义", "boko haram": "博科圣地", "iswap": "西非伊斯兰国", "insurgent": "叛军活动", "jihadist": "圣战分子", "suicide bombing": "自杀式炸弹袭击", "ied": "简易爆炸装置", "extremist": "极端分子",
    "explosion": "爆炸袭击", "bomb": "炸弹事件", "blast": "爆炸", "attacked": "武装袭击", "massacre": "屠杀事件", "fatal": "致命事件", "gunned": "枪击身亡", "gunfire": "枪战", "ambush": "伏击", "raid": "突袭",
    "bandit": "土匪劫掠", "kidnap": "绑架事件", "abduct": "强行诱拐", "abduction": "绑架案", "ransom": "索要赎金", "hostage": "人质事件", "gunmen": "枪手袭击", "robbery": "抢劫案", "rustlers": "盗牛匪帮", "herdsmen": "牧民冲突", "banditry": "匪徒活动", "kidnapping": "绑架", "kidnappers": "绑匪", "highway robbery": "公路抢劫",
    "clash": "武装冲突", "communal clash": "族群冲突", "farmer-herder": "农牧民冲突", "ethno-religious": "族群宗教冲突", "militia": "民兵武装",
    "protest": "抗议示威", "riot": "暴乱骚乱", "strike": "罢工游行", "demonstration": "示威游行", "unrest": "社会动荡", "violence": "暴力事件",
    "accident": "交通事故", "crash": "车祸事故", "somersaulted": "车辆翻车", "collapse": "建筑倒塌", "gridlock": "交通瘫痪", "road accident": "道路交通事故", "vehicular manslaughter": "交通肇事",
    "flooding": "洪涝灾害", "rainstorm": "暴雨灾害", "downpour": "暴雨天气", "deluge": "暴雨洪涝", "flood": "洪水", "landslide": "山体滑坡", "drought": "干旱",
    "killed": "严重袭击", "injured": "人员受伤", "casualties": "伤亡", "deadly": "致命的", "wounded": "受伤",
    "piracy": "海盗袭击", "oil theft": "石油盗窃", "pipeline vandalism": "管道破坏", "separatist": "分离主义", "ipob": "本土人民之声", "criminality": "犯罪活动", "insecurity": "安全形势恶化", "attack": "袭击", "shooting": "枪击事件", "beheading": "斩首事件", "lynching": "私刑"
}

# 按严重程度将 49 个关键词分级，决定气泡颜色
SEVERITY_LEVELS = {
    "high": ["terrorist", "terrorism", "boko haram", "iswap", "insurgent", "jihadist", "suicide bombing", "ied", "extremist", "explosion", "bomb", "blast", "massacre", "gunned", "gunfire", "ambush", "raid", "killed", "deadly", "beheading"],
    "medium": ["bandit", "kidnap", "abduct", "abduction", "ransom", "hostage", "gunmen", "robbery", "rustlers", "herdsmen", "banditry", "kidnapping", "kidnappers", "highway robbery", "clash", "communal clash", "farmer-herder", "ethno-religious", "militia", "attacked", "separatist", "ipob", "attack", "shooting", "lynching"],
    "low": ["protest", "riot", "strike", "demonstration", "unrest", "violence", "accident", "crash", "somersaulted", "collapse", "gridlock", "road accident", "vehicular manslaughter", "flooding", "rainstorm", "downpour", "deluge", "flood", "landslide", "drought", "injured", "casualties", "wounded", "piracy", "oil theft", "pipeline vandalism", "criminality", "insecurity"]
}

# 🔒 体育与噪音词汇黑名单（彻底阻断足球、英超等无关新闻）
SPORTS_BLACKLIST = ["football", "match", "goal", "league", "chelsea", "arsenal", "liverpool", "manchester", "barcelona", "madrid", "tournament", "stadium", "trophy", "striker", "coach", "club", "transfer"]

# 🔒 其他国家黑名单（彻底阻断国际干扰）
FOREIGN_COUNTRIES = ["congo", "venezuela", "ukraine", "russia", "gaza", "israel", "sudan", "kenya", "america", "us", "uk", "ghana", "mali", "niger", "cameroon", "chad"]

# 📌 尼日利亚精确 36 个州及核心城市级坐标字典
NIGERIA_STATES = {
    "abuja": ["Abuja (FCT)", 9.0578, 7.4951], "fct": ["Abuja (FCT)", 9.0578, 7.4951],
    "plateau": ["Plateau State", 9.4167, 9.5833], "jos": ["Jos (Plateau)", 9.8965, 8.8583], "bokkos": ["Bokkos (Plateau)", 9.3000, 8.9500],
    "bauchi": ["Bauchi State", 10.5000, 10.0000], "rafin ciyawa": ["Rafin Ciyawa (Bauchi)", 9.9431, 9.7214],
    "sokoto": ["Sokoto State", 13.0627, 5.2435],
    "borno": ["Borno State", 11.8311, 13.1509], "maiduguri": ["Maiduguri (Borno)", 11.8311, 13.1509],
    "kaduna": ["Kaduna State", 10.5105, 7.4165], "zaria": ["Zaria (Kaduna)", 11.0855, 7.7178],
    "lagos": ["Lagos State", 6.5244, 3.3792], "kano": ["Kano State", 12.0022, 8.5920],
    "rivers": ["Rivers State", 4.8156, 7.0498], "port harcourt": ["Port Harcourt", 4.8156, 7.0498],
    "delta": ["Delta State", 5.7000, 6.0000], "warri": ["Warri (Delta)", 5.5544, 5.7932], "asaba": ["Asaba (Delta)", 6.1985, 6.7297],
    "adamawa": ["Adamawa State", 9.3333, 12.5000], "yola": ["Yola (Adamawa)", 9.2035, 12.4954],
    "anambra": ["Anambra State", 6.2000, 7.0000], "awka": ["Awka (Anambra)", 6.2107, 7.0731], "onitsha": ["Onitsha (Anambra)", 6.1473, 6.7845],
    "benue": ["Benue State", 7.3333, 8.7500], "makurdi": ["Makurdi (Benue)", 7.7337, 8.5214],
    "enugu": ["Enugu State", 6.4584, 7.5083], "oyo": ["Oyo State", 8.0000, 4.0000], "ibadan": ["Ibadan (Oyo)", 7.3775, 3.9470],
    "katsina": ["Katsina State", 12.9833, 7.6000], "zamfara": ["Zamfara State", 12.1667, 6.3333], "gusau": ["Gusau (Zamfara)", 12.1628, 6.6614],
    "yobe": ["Yobe State", 12.0000, 11.5000], "damaturu": ["Damaturu (Yobe)", 11.7470, 11.9608],
    "kogi": ["Kogi State", 7.7333, 6.6667], "lokoja": ["Lokoja (Kogi)", 7.7969, 6.7405],
    "nasarawa": ["Nasarawa State", 8.5000, 8.1667], "lafia": ["Lafia (Nasarawa)", 8.4912, 8.5150],
    "taraba": ["Taraba State", 8.0000, 10.5000], "jalingo": ["Jalingo (Taraba)", 8.8931, 11.3731],
    "gombe": ["Gombe State", 10.2833, 11.1667], "jigawa": ["Jigawa State", 12.2500, 9.5000],
    "kebbi": ["Kebbi State", 11.5000, 4.0000], "kwara": ["Kwara State", 8.5000, 4.7500], "ilorin": ["Ilorin (Kwara)", 8.4799, 4.5418],
    "niger": ["Niger State", 10.0000, 6.0000], "minna": ["Minna (Niger)", 9.5836, 6.5463],
    "ogun": ["Ogun State", 7.0000, 3.5000], "abeokuta": ["Abeokuta (Ogun)", 7.1475, 3.3619],
    "ondo": ["Ondo State", 7.1667, 5.0500], "osun": ["Osun State", 7.5000, 4.5000], "osogbo": ["Osogbo (Osun)", 7.7827, 4.5606],
    "ekiti": ["Ekiti State", 7.6667, 5.2500], "edo": ["Edo State", 6.5000, 6.0000], "benin": ["Benin City (Edo)", 6.3350, 5.6037],
    "cross river": ["Cross River State", 5.7500, 8.5000], "calabar": ["Calabar", 4.9757, 8.3417],
    "akwa ibom": ["Akwa Ibom State", 5.0000, 7.8333], "uyo": ["Uyo (Akwa Ibom)", 5.0377, 7.9128],
    "abia": ["Abia State", 5.4167, 7.5000], "umuahia": ["Umuahia (Abia)", 5.5267, 7.4895],
    "imo": ["Imo State", 5.5000, 7.1667], "owerri": ["Owerri (Imo)", 5.4856, 7.0351],
    "bayelsa": ["Bayelsa State", 4.7500, 6.2500], "yenagoa": ["Yenagoa (Bayelsa)", 4.9267, 6.2631],
    "ebonyi": ["Ebonyi State", 6.2500, 8.0000], "abakaliki": ["Abakaliki (Ebonyi)", 6.2649, 8.0527]
}

SOURCES = [
    "https://news.google.com/rss/search?q=Nigeria+(attack+OR+kidnap+OR+protest+OR+killed+OR+clash+OR+bandits+OR+flooding+OR+crash+OR+somersaulted+OR+fatal)&hl=en-NG&gl=NG&ceid=NG:en",
    "https://www.vanguardngr.com/category/national-news/feed/",
    "https://punchng.com/topics/news/feed/",
    "https://dailytrust.com/feed/",
    "https://www.premiumtimesng.com/category/news/top-news/feed",
    "https://guardian.ng/category/news/nigeria/feed/",
    "https://thenationonlineng.net/news/feed/",
    "https://leadership.ng/category/news/feed/",
    "https://saharareporters.com/feeds/news/feed",
    "https://dailypost.ng/feed/",
    "https://blueprint.ng/category/news/feed/"
]

def is_similar(title1, title2):
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()

def is_clean_security_news(title, summary=""):
    """
    【高精度清洗引擎一】：严格过滤体育新闻和国际干扰
    """
    full_text = (title + " " + summary).lower()
    
    # 1. 拦截体育相关的干扰词
    for sport_word in SPORTS_BLACKLIST:
        if re.search(r'\b' + sport_word + r'\b', full_text):
            return False
            
    # 2. 拦截明确提到其他国家的新闻
    for country in FOREIGN_COUNTRIES:
        if re.search(r'\b' + country + r'\b', full_text):
            return False
            
    return True

def analyze_security_text(text):
    """
    【高精度清洗引擎二】：使用全单词匹配，精准归类突发事件
    """
    text_lower = text.lower()
    for word, zh_name in KEYWORDS_MAPPING.items():
        # \b 确保匹配的是完整单词，避免 'striker' 错误匹配到 'strike'
        if re.search(r'\b' + word + r'\b', text_lower):
            # 找到对应单词后，寻找其匹配的安全等级
            for level, words_list in SEVERITY_LEVELS.items():
                if word in words_list:
                    return level, zh_name
    return None, None

def extract_precise_location(title, summary=""):
    """
    【地理对齐引擎三】：优先匹配对应的具体州，无具体地点的才分配到阿布贾保底
    """
    search_scope = (title + " " + summary).lower()
    
    # 遍历我们完备的 36 个州和核心城镇群词库
    for loc_key, info in NIGERIA_STATES.items():
        if re.search(r'\b' + loc_key + r'\b', search_scope):
            # 匹配成功，赋予对应州的坐标，并加上微小的随机扰动，防止多个气泡在州中心完全重叠
            lat_offset = random.uniform(-0.025, 0.025)
            lng_offset = random.uniform(-0.025, 0.025)
            return info[0], [info[1] + lat_offset, info[2] + lng_offset]
            
    # 🔍 【完全匹配不到具体州时】投放到首都阿布贾进行宏观保底，并大范围散开
    return "Nigeria (General Area)", [9.0578 + random.uniform(-0.5, 0.5), 7.4951 + random.uniform(-0.5, 0.5)]

def fetch_all_sources_with_dedup():
    all_stories = []
    seen_urls = set()
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    for url in SOURCES:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if res.status_code != 200: continue
            root = ET.fromstring(res.content)
            
            for item in root.findall('.//item'):
                title = item.find('title').text.split(" - ")[0].strip()
                link = item.find('link').text
                pub_date_str = item.find('pubDate').text
                desc = item.find('description').text if item.find('description') is not None else ""
                
                if link in seen_urls: continue

                try:
                    pub_date = datetime.strptime(pub_date_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                except: continue

                if pub_date < seven_days_ago: continue

                # 🚀 拦截点1：清洗无关的体育、非尼日利亚新闻
                if not is_clean_security_news(title, desc): continue

                # 🚀 拦截点2：精准识别由用户订制的 49 个安全领域关键词（防止 striker 误伤）
                level, event_zh = analyze_security_text(title)
                if not level and desc: 
                    level, event_zh = analyze_security_text(desc)
                if not level: continue

                # 🚀 拦截点3：智能去重
                duplicate_found = False
                for existing_story in all_stories:
                    if existing_story["date"] == pub_date.strftime("%Y-%m-%d"):
                        if is_similar(title, existing_story["title"]) > 0.65:
                            duplicate_found = True
                            break
                if duplicate_found: continue

                # 🚀 拦截点4：精准匹配发生州/县，或保底阿布贾
                loc_name, coords = extract_precise_location(title, desc)

                all_stories.append({
                    "title": title,
                    "type": event_zh,
                    "level": level,
                    "date": pub_date.strftime("%Y-%m-%d"),
                    "lat": coords[0],
                    "lng": coords[1],
                    "location": loc_name,
                    "summary": f'<div style="font-weight:bold;margin-bottom:5px;">事发地点: {loc_name}</div><a href="{link}" target="_blank" style="color: #007bff; text-decoration: underline; font-weight: bold;">点击打开原始媒体报道 (Source Link)</a>'
                })
                seen_urls.add(link)
        except Exception as e:
            continue
            
    return all_stories

if __name__ == "__main__":
    print("【天网高精度版】正在执行清洗、过滤与州级对齐...")
    data = fetch_all_sources_with_dedup()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"清洗完毕！成功导出 {len(data)} 条高纯净无噪音数据。")
