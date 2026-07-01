import json
import re
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ==========================================
# 1️⃣ 前后端关键词完美同频矩阵
# ==========================================
SECURITY_KEYWORDS_MAP = {
    "high": {
        "tags": ["恐怖袭击", "武装冲突/严重袭击", "绑架劫持"],
        "keywords": ["killed", "dead", "bandit", "terrorist", "massacre", "abducted", "kidnapped", "clash", "razed", "bomb", "attack", "manslaughter", "iswap", "boko haram", "herdsmen", "gunned down", "assassinated"]
    },
    "medium": {
        "tags": ["安全冲突", "逮捕反制", "治安事件"],
        "keywords": ["clashed", "gunmen", "arrested", "stole", "raid", "robbery", "suspects", "military operation", "clash", "police", "troops", "neutralized", "curfew"]
    },
    "low": {
        "tags": ["抗议示威", "交通安全", "社会安全"],
        "keywords": ["protest", "demonstration", "gridlock", "accident", "vehicular", "vandalism", "strike", "blockade"]
    }
}

# ==========================================
# 2️⃣ 彻底补齐：尼日利亚全部 36 个州及联邦首都特区 (FCT) 官方全量基准坐标库
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
# 3️⃣ 优化后的数据来源渠道库（20个本土与宏观安全通道）
# ==========================================
NEWS_SOURCES_CONFIG = {
    "Daily Post Nigeria": "https://dailypost.ng/category/news/feed/",
    "Vanguard National": "https://www.vanguardngr.com/category/national-news/feed/",
    "Punch Metro": "https://punchng.com/topics/news/feed/",
    "Premium Times": "https://www.premiumtimesng.com/category/news/top-news/feed",
    "The Guardian Nigeria": "https://guardian.ng/category/news/nigeria/feed/",
    "The Cable NG": "https://www.thecable.ng/feed",
    "ThisDay Live": "https://www.thisdaylive.com/index.php/feed/",
    "Leadership News": "https://leadership.ng/feed/",
    "The Nation": "https://thenationonlineng.net/feed/",
    "BusinessDay": "https://businessday.ng/feed/",
    "Daily Trust": "https://dailytrust.com/feed/",
    "Sahara Reporters": "http://saharareporters.com/feeds/news/feed",
    "Channels TV Local": "https://www.channelstv.com/category/local/feed/",
    "Independent NG": "https://independent.ng/category/news/feed/",
    "Sun News Online": "https://sunnewsonline.com/feed/",
    "Nigerian Tribune": "https://tribuneonlineng.com/category/news/feed/",
    "Blueprint NG": "https://www.blueprint.ng/category/news/feed/",
    "PRNigeria (Security)": "https://news.google.com/rss/search?q=site:prnigeria.com&hl=en-NG&gl=NG&ceid=NG:en",
    "Google News - Nigeria Security": "https://news.google.com/rss/search?q=Nigeria+security+clash+attack+killed&hl=en-NG&gl=NG&ceid=NG:en",
    "Google News - Nigeria Local": "https://news.google.com/rss/search?q=Nigeria+local+government+area+violence&hl=en-NG&gl=NG&ceid=NG:en"
}

# ==========================================
# 4️⃣ 核心安全判定过滤引擎（带负向财经策略拦截）
# ==========================================
def analyze_event_security_v3(title, content=""):
    text = (title + " " + content).lower()
    
    # 🚫 财经/税收/改革政策类黑名单拦截机制（彻底丢弃宏观经济新闻）
    economic_blacklist = [
        "economic decline", "economic stability", "tax reform", "fiscal policy", 
        "inflation rate", "naira stabilization", "gdp growth", "revenue generation",
        "customs revenue", "budget passing", "foreign exchange market", "cbn policy",
        "moved from economic", "economic growth", "economic reforms"
    ]
    if any(eco_kw in text for eco_kw in economic_blacklist):
        return "DROP", "low"  # 标记为丢弃状态

    # 运行涉安事件分类判定
    for level, config in SECURITY_KEYWORDS_MAP.items():
        if any(kw in text for kw in config["keywords"]):
            if "clash" in text or "conflict" in text or "communal" in text: 
                return "族群冲突/武装对抗", level
            if any(k in text for k in ["bandit", "terrorist", "abducted", "kidnap", "boko"]): 
                return "恐怖分子/土匪袭击", level
            return "突发涉安事件", level
    return "常规治安动态", "low"

def parse_location_v3(title, content=""):
    text = (title + " " + content).lower()
    
    # 扫描全尼日利亚 36 个州域关键字
    for state_kw, coord in NIGERIA_ALL_STATES.items():
        if state_kw in text:
            matched_context = re.search(r'([a-zA-llgagh\s]{3,12})\s+(in|at|lga)\s+' + state_kw, text)
            display_name = coord["name"]
            if matched_context:
                display_name = f"{matched_context.group(1).strip().title()} Area, {coord['name']}"
            return coord["lat"], coord["lng"], display_name, True
            
    return NIGERIA_ALL_STATES["abuja"]["lat"], NIGERIA_ALL_STATES["abuja"]["lng"], "Nigeria (General Area)", False

# ==========================================
# 5️⃣ 数据清洗去重与动态抖动散点管道
# ==========================================
def smart_process_pipeline_v3(raw_scraped_list):
    processed_events = []
    seen_fingerprints = set()

    for news in raw_scraped_list:
        title = news.get("title", "")
        pub_date = news.get("date", "")
        url = news.get("url", "#")
        source = news.get("source", "未知媒体")
        
        if not title: continue
        
        # 1. 前置熔断判定
        event_type, level = analyze_event_security_v3(title)
        if event_type == "DROP": 
            continue  # 拦截纯财经政治新闻，直接跳过不生成气泡
            
        # 2. 格式化日期为 YYYY-MM-DD
        try:
            if "GMT" in pub_date or "," in pub_date:
                clean_date = datetime.strptime(pub_date.split(" +")[0].split(" GMT")[0], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
            else:
                clean_date = pub_date[:10]
        except Exception:
            clean_date = datetime.today().strftime("%Y-%m-%d")
        
        base_lat, base_lng, location_name, is_state_found = parse_location_v3(title)
        
        # 3. 动态偏移抗重叠引擎 (Jitter Engine)
        if is_state_found:
            lat_jitter = random.uniform(-0.07, 0.07)
            lng_jitter = random.uniform(-0.07, 0.07)
            final_lat = base_lat + lat_jitter
            final_lng = base_lng + lng_jitter
        else:
            final_lat = base_lat + random.uniform(-0.12, 0.12)
            final_lng = base_lng + random.uniform(-0.12, 0.12)

        # 4. 指纹机制去重
        fingerprint = f"{clean_date}_{level}_{location_name[:10].replace(' ', '')}"
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            processed_events.append({
                "title": title, "type": event_type, "level": level, "date": clean_date,
                "lat": round(final_lat, 4), "lng": round(final_lng, 4), "location": location_name, "source": source, "url": url
            })
        else:
            is_dup = False
            for existing in processed_events:
                if existing["date"] == clean_date and existing["location"] == location_name:
                    if title[:15].lower() == existing["title"][:15].lower():
                        is_dup = True
                        break
            if not is_dup:
                processed_events.append({
                    "title": title, "type": event_type, "level": level, "date": clean_date,
                    "lat": round(final_lat, 4), "lng": round(final_lng, 4), "location": location_name, "source": source, "url": url
                })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(processed_events, f, ensure_ascii=False, indent=4)
    print(f"✅ [fetch_news.py] 运行完毕：已清洗纯财经噪音，并生成 {len(processed_events)} 条精准突发气泡至 data.json。")

# ==========================================
# 6️⃣ 多线程循环抓取器
# ==========================================
def run_all_scrapers_v3():
    aggregated_raw_data = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 启动全网 20 个本土监听源的数据流吞吐...")
    
    for source_name, feed_url in NEWS_SOURCES_CONFIG.items():
        try:
            response = requests.get(feed_url, headers=headers, timeout=12)
            if response.status_code != 200: continue
                
            root = ET.fromstring(response.content)
            count = 0
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else "#"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                
                if title:
                    aggregated_raw_data.append({
                        "title": title, "date": pub_date, "url": link, "source": source_name
                    })
                    count += 1
            print(f"  └─ 渠道 [{source_name}]：抓取到 {count} 条事件快照")
        except Exception:
            continue
            
    smart_process_pipeline_v3(aggregated_raw_data)

if __name__ == "__main__":
    run_all_scrapers_v3()
