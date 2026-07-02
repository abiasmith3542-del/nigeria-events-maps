import json
import os
import re
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ==========================================
# 1️⃣ 核心涉安与公共卫生白名单矩阵
# ==========================================
SECURITY_KEYWORDS_MAP = {
    "high": {
        "tags": ["恐怖袭击", "武装冲突/严重袭击", "绑架劫持"],
        "keywords": ["killed", "dead", "fatal", "bandit", "terrorist", "massacre", "abducted", "kidnapped", "clash", "razed", "bomb", "attack", "manslaughter", "iswap", "boko haram", "herdsmen", "gunned down", "assassinated", "ambush", "beheaded", "hostage", "neutralized", "massacred", "herders", "shot"]
    },
    "medium": {
        "tags": ["安全冲突", "逮捕反制", "治安事件"],
        "keywords": ["clashed", "gunmen", "arrested", "stole", "raid", "robbery", "suspects", "military operation", "police", "troops", "curfew", "gunfire", "weapon", "ammunition", "hijack", "busted", "vigilante", "troops rescue"]
    },
    "low": {
        "tags": ["抗议示威", "突发灾害/疫情", "交通安全"],
        "keywords": ["protest", "demonstration", "gridlock", "accident", "vehicular", "vandalism", "strike", "blockade", "riot", "unrest", "explosion", "fire outbreak", "collapse", 
                     "cholera", "lassa fever", "mpox", "meningitis", "outbreak", "epidemic", "contagious", "infected cases", "yellow fever", "dengue", "pandemic"]
    }
}

# ==========================================
# 2️⃣ 全尼日利亚基准坐标库（含 Plateau/Jos 核心锚点）
# ==========================================
NIGERIA_ALL_STATES = {
    "abuja": {"lat": 9.0578, "lng": 7.4950, "name": "Abuja (FCT)"},
    "fct": {"lat": 9.0578, "lng": 7.4950, "name": "Abuja (FCT)"},
    "plateau": {"lat": 9.3000, "lng": 9.5000, "name": "Plateau State"},
    "jos": {"lat": 9.8965, "lng": 8.8583, "name": "Jos, Plateau State"}, # 🎯 强化乔斯本地精准定位
    "abia": {"lat": 5.4167, "lng": 7.5000, "name": "Abia State"},
    "adamawa": {"lat": 9.3333, "lng": 12.5000, "name": "Adamawa State"},
    "akwa ibom": {"lat": 5.0000, "lng": 7.8333, "name": "Akwa Ibom State"},
    "anambra": {"lat": 6.2000, "lng": 7.0000, "name": "Anambra State"},
    "bauchi": {"lat": 10.5000, "lng": 10.0000, "name": "Bauchi State"},
    "bayelsa": {"lat": 4.7500, "lng": 6.0000, "name": "Bayelsa State"},
    "benue": {"lat": 7.3333, "lng": 8.7500, "name": "Benue State"},
    "borno": {"lat": 11.8333, "lng": 13.1500, "name": "Borno State"},
    "cross river": {"lat": 5.7500, "lng": 8.5000, "name": "Cross River State"},
    "delta": {"lat": 5.5000, "lng": 6.0000, "name": "Delta State"},
    "ebonyi": {"lat": 6.2500, "lng": 8.0000, "name": "Ebonyi State"},
    "edo": {"lat": 6.5000, "lng": 6.0000, "name": "Edo State"},
    "ekiti": {"lat": 7.6667, "lng": 5.2500, "name": "Ekiti State"},
    "enugu": {"lat": 6.5000, "lng": 7.5000, "name": "Enugu State"},
    "gombe": {"lat": 10.2833, "lng": 11.1667, "name": "Gombe State"},
    "imo": {"lat": 5.4833, "lng": 7.0333, "name": "Imo State"},
    "jigawa": {"lat": 12.0000, "lng": 9.7500, "name": "Jigawa State"},
    "kaduna": {"lat": 10.5000, "lng": 7.5000, "name": "Kaduna State"},
    "kano": {"lat": 12.0022, "lng": 8.5920, "name": "Kano State"},
    "katsina": {"lat": 12.5139, "lng": 7.6114, "name": "Katsina State"},
    "kebbi": {"lat": 11.4500, "lng": 4.2000, "name": "Kebbi State"},
    "kogi": {"lat": 7.8000, "lng": 6.7333, "name": "Kogi State"},
    "kwara": {"lat": 8.5000, "lng": 4.5500, "name": "Kwara State"},
    "lagos": {"lat": 6.5244, "lng": 3.3792, "name": "Lagos State"},
    "nasarawa": {"lat": 8.5000, "lng": 8.1667, "name": "Nasarawa State"},
    "niger": {"lat": 10.0000, "lng": 6.0000, "name": "Niger State"},
    "ogun": {"lat": 7.0000, "lng": 3.5000, "name": "Ogun State"},
    "ondo": {"lat": 7.2500, "lng": 5.2000, "name": "Ondo State"},
    "osun": {"lat": 7.5000, "lng": 4.5000, "name": "Osun State"},
    "oyo": {"lat": 8.0000, "lng": 4.0000, "name": "Oyo State"},
    "plateau": {"lat": 9.5000, "lng": 9.5000, "name": "Plateau State"},
    "rivers": {"lat": 4.7500, "lng": 6.8333, "name": "Rivers State"},
    "sokoto": {"lat": 13.0622, "lng": 5.2333, "name": "Sokoto State"},
    "taraba": {"lat": 8.0000, "lng": 10.5000, "name": "Taraba State"},
    "yobe": {"lat": 12.0000, "lng": 11.5000, "name": "Yobe State"},
    "zamfara": {"lat": 12.1222, "lng": 6.2244, "name": "Zamfara State"}
}

# ==========================================
# 3️⃣ 22路核心情报源
# ==========================================
NEWS_SOURCES_CONFIG = {
    "Daily Post Nigeria": "https://dailypost.ng/category/news/feed/",
    "Vanguard National": "https://www.vanguardngr.com/category/national-news/feed/",
    "Punch Metro": "https://punchng.com/topics/news/feed/",
    "Premium Times": "https://www.premiumtimesng.com/category/news/top-news/feed",
    "The Guardian Nigeria": "https://guardian.ng/category/news/nigeria/feed/",
    "The Cable NG": "https://www.thecable.ng/feed",
    "Leadership News": "https://leadership.ng/feed/",
    "Daily Trust": "https://dailytrust.com/feed/",
    "Sahara Reporters": "http://saharareporters.com/feeds/news/feed",
    "Channels TV Local": "https://www.channelstv.com/category/local/feed/",
    "ThisDay Live": "https://www.thisdaylive.com/index.php/category/news/feed/",
    "The Nation Nigeria": "https://thenationonlineng.net/news/feed/",
    "Sun News Online": "https://sunnewsonline.com/category/national/feed/",
    "Tribune Online": "https://tribuneonlineng.com/category/news/feed/",
    "Legit.ng News": "https://www.legit.ng/rss/all.xml",
    "PRNigeria (Security)": "https://news.google.com/rss/search?q=site:prnigeria.com&hl=en-NG&gl=NG&ceid=NG:en",
    "Zagazola Defense": "https://news.google.com/rss/search?q=Zagazola&hl=en-NG&gl=NG&ceid=NG:en",
    "HumAngle Media": "https://news.google.com/rss/search?q=site:humanglemedia.com&hl=en-NG&gl=NG&ceid=NG:en",
    "WHO Africa Outbreaks": "https://news.google.com/rss/search?q=site:afro.who.int+outbreak+nigeria&hl=en-NG&gl=NG&ceid=NG:en",
    "Africa CDC Alert": "https://news.google.com/rss/search?q=site:africacdc.org+nigeria&hl=en-NG&gl=NG&ceid=NG:en",
    "Google News - Nigeria Security": "https://news.google.com/rss/search?q=Nigeria+security+clash+attack+killed+cholera+outbreak&hl=en-NG&gl=NG&ceid=NG:en",
    "Google News - Nigeria Local": "https://news.google.com/rss/search?q=Nigeria+local+government+area+violence+epidemic&hl=en-NG&gl=NG&ceid=NG:en"
}

# ==========================================
# 4️⃣ 强涉安审查引擎
# ==========================================
def analyze_event_security_v6(title, content=""):
    text = (title + " " + content).lower()
    
    is_security_related = False
    matched_level = "low"
    
    for level, config in SECURITY_KEYWORDS_MAP.items():
        if any(kw in text for kw in config["keywords"]):
            is_security_related = True
            matched_level = level
            break

    if not is_security_related:
        irrelevant_blacklist = [
            "football", "match", "fc", "super eagles", "sport", "entertainment", "movie", "music", "award",
            "appoints", "appointment", "inaugurates", "passed bill", "economic", "growth", "revenue", "tax", 
            "fiscal", "inflation", "exchange rate", "roads", "infrastructure", "electricity", "wages", "salary", 
            "pension", "school", "university", "jamb", "waec", "subsidy", "hailed", "praised"
        ]
        if any(irr_kw in text for irr_kw in irrelevant_blacklist):
            return "DROP", "low"
        return "DROP", "low"

    if any(k in text for k in ["cholera", "lassa fever", "mpox", "meningitis", "outbreak", "epidemic", "yellow fever", "dengue", "pandemic"]):
        return "突发公共卫生疫情", "low"
    if any(k in text for k in ["clash", "conflict", "communal", "cultist", "cult", "fighting"]): 
        return "族群冲突/武装对抗", matched_level
    if any(k in text for k in ["bandit", "terrorist", "abducted", "kidnap", "boko", "gunmen", "insurgents", "herders", "shot"]): 
        return "恐怖分子/土匪袭击", matched_level
        
    return "突发涉安事件", matched_level

# ==========================================
# 5️⃣ 地名精准解析
# ==========================================
def parse_location_strict(title, content=""):
    text = (title + " " + content).lower()
    
    for state_kw, coord in NIGERIA_ALL_STATES.items():
        if state_kw in text:
            matched_context = re.search(r'\b([a-z]{4,12})\b\s+(in|at|lga)\s+' + state_kw, text)
            display_name = coord["name"]
            
            if matched_context:
                specific_loc = matched_context.group(1).strip().title()
                invalid_nouns = ["People", "Electricity", "Violence", "Community", "Again", "Involved", "Police", "Soldier", "Kill", "Attack", "Cases", "Report"]
                if specific_loc not in invalid_nouns:
                    display_name = f"{specific_loc} Area, {coord['name']}"
                    
            return coord["lat"], coord["lng"], display_name, True
            
    return NIGERIA_ALL_STATES["abuja"]["lat"], NIGERIA_ALL_STATES["abuja"]["lng"], "Nigeria (General Area)", False

# ==========================================
# 6️⃣ 核心升级：7天数据增量合并与滚动清洗管道
# ==========================================
def smart_process_pipeline_v6(raw_scraped_list):
    # ⏰ 计算允许入库的7天时间窗口（完美匹配前端地图滑块）
    today = datetime.today()
    allowed_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(8)]
    print(f"\n📅 7天滚动侦听窗口已激活：保存 {allowed_dates[-1]} 至 {allowed_dates[0]} 期间的安全事件。")

    # 💾 读取现有历史数据，防止直接覆盖被清除
    existing_events = []
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                existing_events = json.load(f)
        except Exception:
            existing_events = []

    # 建立现有的去重指纹库
    seen_fingerprints = {f"{ev['date']}_{ev['level']}_{ev['location'][:15].replace(' ', '')}" for ev in existing_events if 'date' in ev}
    
    new_archive_list = [ev for ev in existing_events if ev.get("date") in allowed_dates] # 过滤掉超过7天的真正老旧数据
    
    added_count = 0

    for news in raw_scraped_list:
        title = news.get("title", "")
        pub_date = news.get("date", "")
        url = news.get("url", "#")
        source = news.get("source", "未知媒体")
        
        if not title: continue
        
        # 解析日期
        try:
            if "GMT" in pub_date or "," in pub_date:
                clean_date = datetime.strptime(pub_date.split(" +")[0].split(" GMT")[0], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
            else:
                clean_date = pub_date[:10]
        except Exception:
            clean_date = "UNKNOWN"

        # 🛑 阻断：如果新闻不在过去7天滑块范围内，才予以剔除
        if clean_date not in allowed_dates:
            continue
        
        # 白名单审查
        event_type, level = analyze_event_security_v6(title)
        if event_type == "DROP": 
            continue  
            
        base_lat, base_lng, location_name, is_state_found = parse_location_strict(title)
        
        # 散点引擎
        lat_jitter = random.uniform(-0.06, 0.06) if is_state_found else random.uniform(-0.1, 0.1)
        lng_jitter = random.uniform(-0.06, 0.06) if is_state_found else random.uniform(-0.1, 0.1)
        final_lat = base_lat + lat_jitter
        final_lng = base_lng + lng_jitter

        # 指纹去重
        fingerprint = f"{clean_date}_{level}_{location_name[:15].replace(' ', '')}"
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            new_archive_list.append({
                "title": title, "type": event_type, "level": level, "date": clean_date,
                "lat": round(final_lat, 4), "lng": round(final_lng, 4), "location": location_name, "source": source, "url": url
            })
            added_count += 1

    # 持久化输出（保留了历史+最新合并的完整包）
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(new_archive_list, f, ensure_ascii=False, indent=4)
        
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🧹 [7天滑动滚动数据库更新完成]")
    print(f"   ✨ 本次新增实时硬核安全事件: {added_count} 条")
    print(f"   📊 数据库当前共留存（过去一周内）总气泡数: {len(new_archive_list)} 条")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def run_all_scrapers_v6():
    aggregated_raw_data = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 正在从22路渠道拉取并合并安全大盘...")
    for source_name, feed_url in NEWS_SOURCES_CONFIG.items():
        try:
            response = requests.get(feed_url, headers=headers, timeout=10)
            if response.status_code != 200: continue
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else "#"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                if title:
                    aggregated_raw_data.append({"title": title, "date": pub_date, "url": link, "source": source_name})
        except Exception:
            continue
            
    smart_process_pipeline_v6(aggregated_raw_data)

if __name__ == "__main__":
    run_all_scrapers_v6()
