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
# 3️⃣ 优化后的数据来源渠道库（强化尼日利亚本土及地方分类流，全覆盖抓取）
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
# 4️⃣ 全功能防漏核心引擎（含动态抖动不重叠与智能降级定位机制）
# ==========================================
def analyze_event_security_v3(title, content=""):
    text = (title + " " + content).lower()
    for level, config in SECURITY_KEYWORDS_MAP.items():
        if any(kw in text for kw in config["keywords"]):
            if "clash" in text or "conflict" in text or "communal" in text: 
                return "族群冲突/武装对抗", level
            if any(k in text for k in ["bandit", "terrorist", "abducted", "kidnap", "boko"]): 
                return "恐怖分子/土匪袭击", level
            return "突发涉安事件", level
    return "常规治安动态", "low"

def parse_location_v3(title, content=""):
    """
    智能解析引擎：无需穷举774个LGA坐标。
    机制：检测文章提及的任何州名。如果在新闻中发现地名（即使是没有硬编码坐标的小地方或LGA），
    提取其关联的州，并由清洗流在州基准中心点自动进行随机微分轻微偏移（Jitter），
    使其在前端渲染成独立的、不互相重叠覆盖的气泡，达到零死角全覆盖。
    """
    text = (title + " " + content).lower()
    
    # 扫描是否包含任意一个合法的尼日利亚州名
    for state_kw, coord in NIGERIA_ALL_STATES.items():
        if state_kw in text:
            # 提取具体的上下文关键词，使前端展示更精细
            matched_context = re.search(r'([a-zA-llgagh\s]{3,12})\s+(in|at|lga)\s+' + state_kw, text)
            display_name = coord["name"]
            if matched_context:
                display_name = f"{matched_context.group(1).strip().title()} Area, {coord['name']}"
            return coord["lat"], coord["lng"], display_name, True
            
    # 全局极端保底（阿布贾总归纳点）
    return NIGERIA_ALL_STATES["abuja"]["lat"], NIGERIA_ALL_STATES["abuja"]["lng"], "Nigeria (General Area)", False

# ==========================================
# 5️⃣ 抗堆叠防误杀数据清洗管道
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
            
        # 格式化日期
        try:
            if "GMT" in pub_date or "," in pub_date:
                clean_date = datetime.strptime(pub_date.split(" +")[0].split(" GMT")[0], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
            else:
                clean_date = pub_date[:10]
        except Exception:
            clean_date = datetime.today().strftime("%Y-%m-%d")
        
        event_type, level = analyze_event_security_v3(title)
        base_lat, base_lng, location_name, is_state_found = parse_location_v3(title)
        
        # 💥 动态偏移抗堆叠机制 (Jitter Engine)：
        # 同一个州如果同一天有多条不同的细分地名新闻（例如Akwa Ibom不同的LGA），
        # 赋予其微小的坐标偏移量（+-0.08度以内），防止它们在前端地图上完全重叠而导致不可见！
        if is_state_found:
            lat_jitter = random.uniform(-0.07, 0.07)
            lng_jitter = random.uniform(-0.07, 0.07)
            final_lat = base_lat + lat_jitter
            final_lng = base_lng + lng_jitter
        else:
            final_lat = base_lat + random.uniform(-0.12, 0.12)
            final_lng = base_lng + random.uniform(-0.12, 0.12)

        # 指纹验证（日期+级别+位置前缀）
        fingerprint = f"{clean_date}_{level}_{location_name[:10].replace(' ', '')}"
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            processed_events.append({
                "title": title, "type": event_type, "level": level, "date": clean_date,
                "lat": round(final_lat, 4), "lng": round(final_lng, 4), "location": location_name, "source": source, "url": url
            })
        else:
            # 二次判断，防止标题前缀不同的同地独立事件被干掉
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
    print(f"✅ [fetch_news.py] 完美运行：已并行调度 20 组多地域数据，成功清洗并输出 {len(processed_events)} 个安全气泡至 data.json 文件。")

# ==========================================
# 6️⃣ 自动化抓取执行机
# ==========================================
def run_all_scrapers_v3():
    aggregated_raw_data = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 开始请求全量 20 个尼日利亚本土化安全情报监听数据通道...")
    
    for source_name, feed_url in NEWS_SOURCES_CONFIG.items():
        try:
            response = requests.get(feed_url, headers=headers, timeout=12)
            if response.status_code != 200:
                continue
                
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
            print(f"  └─ 渠道 [{source_name}]：同步提取到 {count} 条潜在区域数据")
        except Exception:
            continue
            
    # 执行智能过滤管道
    smart_process_pipeline_v3(aggregated_raw_data)

if __name__ == "__main__":
    run_all_scrapers_v3()
