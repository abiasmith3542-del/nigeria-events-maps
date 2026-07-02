import json
import re
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ==========================================
# 1️⃣ 核心涉安与公共卫生白名单矩阵（强准入词库）
# ==========================================
SECURITY_KEYWORDS_MAP = {
    "high": {
        "tags": ["恐怖袭击", "武装冲突/严重袭击", "绑架劫持"],
        "keywords": ["killed", "dead", "fatal", "bandit", "terrorist", "massacre", "abducted", "kidnapped", "clash", "razed", "bomb", "attack", "manslaughter", "iswap", "boko haram", "herdsmen", "gunned down", "assassinated", "ambush", "beheaded", "hostage", "neutralized", "massacred"]
    },
    "medium": {
        "tags": ["安全冲突", "逮捕反制", "治安事件"],
        "keywords": ["clashed", "gunmen", "arrested", "stole", "raid", "robbery", "suspects", "military operation", "police", "troops", "curfew", "gunfire", "weapon", "ammunition", "hijack", "busted", "vigilante"]
    },
    "low": {
        "tags": ["抗议示威", "突发灾害/疫情", "交通安全"],
        "keywords": ["protest", "demonstration", "gridlock", "accident", "vehicular", "vandalism", "strike", "blockade", "riot", "unrest", "explosion", "fire outbreak", "collapse", 
                     "cholera", "lassa fever", "mpox", "meningitis", "outbreak", "epidemic", "contagious", "infected cases", "yellow fever", "dengue", "pandemic"]
    }
}

# ==========================================
# 2️⃣ 全尼日利亚全量基准坐标库
# ==========================================
NIGERIA_ALL_STATES = {
    "abuja": {"lat": 9.0578, "lng": 7.4950, "name": "Abuja (FCT)"},
    "fct": {"lat": 9.0578, "lng": 7.4950, "name": "Abuja (FCT)"},
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
# 3️⃣ 22路高并发核心频道矩阵
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
# 4️⃣ 强核心准入机制（涉安大案拥有黑名单豁免权）
# ==========================================
def analyze_event_security_v5(title, content=""):
    text = (title + " " + content).lower()
    
    # 🎯 优先检查涉安/疫情核心白名单：一旦命中硬核事件词汇，直接豁免黑名单拦截！
    is_security_related = False
    matched_level = "low"
    
    for level, config in SECURITY_KEYWORDS_MAP.items():
        if any(kw in text for kw in config["keywords"]):
            is_security_related = True
            matched_level = level
            break

    # 🛑 只有在不涉及硬核危险事件的前提下，黑名单拦截才生效
    if not is_security_related:
        irrelevant_blacklist = [
            "football", "match", "fc", "super eagles", "sport", "entertainment", "movie", "music", "award",
            "appoints", "appointment", "inaugurates", "passed bill", "economic", "growth", "revenue", "tax", 
            "fiscal", "inflation", "exchange rate", "roads", "infrastructure", "electricity", "wages", "salary", 
            "pension", "school", "university", "jamb", "waec", "subsidy", "hailed", "praised"
        ]
        if any(irr_kw in text for irr_kw in irrelevant_blacklist):
            return "DROP", "low"
        return "DROP", "low"  # 既没命中硬核白名单，也没命中常规黑名单的闲聊内容，直接默认剥离！

    # 精准标签划分
    if any(k in text for k in ["cholera", "lassa fever", "mpox", "meningitis", "outbreak", "epidemic", "yellow fever", "dengue", "pandemic"]):
        return "突发公共卫生疫情", "low"
    if any(k in text for k in ["clash", "conflict", "communal", "cultist", "cult", "fighting"]): 
        return "族群冲突/武装对抗", matched_level
    if any(k in text for k in ["bandit", "terrorist", "abducted", "kidnap", "boko", "gunmen", "insurgents"]): 
        return "恐怖分子/土匪袭击", matched_level
        
    return "突发涉安事件", matched_level

# ==========================================
# 5️⃣ 地名精确解析与杂质过滤
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
# 6️⃣ 数据清洗管道（48小时动态滑动窗口机制）
# ==========================================
def smart_process_pipeline_v5(raw_scraped_list):
    processed_events = []
    seen_fingerprints = set()
    
    # ⏰ 开启 48 小时滑动时间窗口（完美解决 RSS 发稿时差和日期字符卡死问题）
    today = datetime.today()
    allowed_dates = [
        today.strftime("%Y-%m-%d"),
        (today - timedelta(days=1)).strftime("%Y-%m-%d")
    ]
    print(f"\n⏰ 实时滑动侦听窗口：允许入库的日期为 {allowed_dates}（其余历史老旧新闻将予以拦截）")

    dropped_by_date = 0
    dropped_by_irrelevant = 0

    for news in raw_scraped_list:
        title = news.get("title", "")
        pub_date = news.get("date", "")
        url = news.get("url", "#")
        source = news.get("source", "未知媒体")
        
        if not title: continue
        
        # 1. 强力时间戳解析
        try:
            if "GMT" in pub_date or "," in pub_date:
                clean_date = datetime.strptime(pub_date.split(" +")[0].split(" GMT")[0], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
            else:
                clean_date = pub_date[:10]
        except Exception:
            clean_date = "UNKNOWN"

        # 🛑 【滑动窗口拦截】只允许入库48小时内（今明/昨今）爆发的最热动态
        if clean_date not in allowed_dates:
            dropped_by_date += 1
            continue
        
        # 2. 白名单核心安全局势审查
        event_type, level = analyze_event_security_v5(title)
        if event_type == "DROP": 
            dropped_by_irrelevant += 1
            continue  
            
        base_lat, base_lng, location_name, is_state_found = parse_location_strict(title)
        
        # 3. 散点抗重叠引擎
        lat_jitter = random.uniform(-0.06, 0.06) if is_state_found else random.uniform(-0.1, 0.1)
        lng_jitter = random.uniform(-0.06, 0.06) if is_state_found else random.uniform(-0.1, 0.1)
        final_lat = base_lat + lat_jitter
        final_lng = base_lng + lng_jitter

        # 4. 指纹去重验证
        fingerprint = f"{clean_date}_{level}_{location_name[:15].replace(' ', '')}"
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            processed_events.append({
                "title": title, "type": event_type, "level": level, "date": clean_date,
                "lat": round(final_lat, 4), "lng": round(final_lng, 4), "location": location_name, "source": source, "url": url
            })

    # 持久化输出
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(processed_events, f, ensure_ascii=False, indent=4)
        
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🧹 [48小时滑动侦听流运行完成]")
    print(f"   🛑 因非近期发布(历史老旧新闻)被拦截: {dropped_by_date} 条")
    print(f"   🚫 因纯碎民生/政治/非涉安噪音被拦截: {dropped_by_irrelevant} 条")
    print(f"   🎯 成功入库的高硬核实时安全气泡: {len(processed_events)} 条")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# ==========================================
# 7️⃣ 自动化调度
# ==========================================
def run_all_scrapers_v5():
    aggregated_raw_data = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 正在建立22个媒体监听管道，拉取最新突发态势...")
    
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
                    aggregated_raw_data.append({
                        "title": title, "date": pub_date, "url": link, "source": source_name
                    })
        except Exception:
            continue
            
    smart_process_pipeline_v5(aggregated_raw_data)

if __name__ == "__main__":
    run_all_scrapers_v5()
