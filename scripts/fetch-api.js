const fs = require("fs");
const fetch = require("node-fetch");

const API_KEY = "你的API_KEY";
const FILE = "./data/events.json";

// 👉 7天时间（毫秒）
const MAX_AGE = 7 * 24 * 60 * 60 * 1000;

async function fetchNews() {
  let oldData = [];

  // ✅ 1. 读取旧数据
  if (fs.existsSync(FILE)) {
    oldData = JSON.parse(fs.readFileSync(FILE));
  }

  const res = await fetch(`https://newsdata.io/api/1/news?apikey=${API_KEY}&q=Nigeria&country=ng`);
  const json = await res.json();

  let newEvents = [];

  json.results.forEach(item => {
    const { type, level } = detectType(item.title);
    const loc = detectLocation(item.title);

    newEvents.push({
      title: item.title,
      type,
      level,
      lat: loc.lat,
      lng: loc.lng,
      source: item.link,
      time: new Date(item.pubDate).toISOString()
    });
  });

  // ✅ 2. 合并数据
  let all = [...oldData, ...newEvents];

  // ✅ 3. 去重（按标题）
  const seen = new Set();
  all = all.filter(e => {
    if (seen.has(e.title)) return false;
    seen.add(e.title);
    return true;
  });

  // ✅ 4. 删除7天前数据
  const now = Date.now();

  all = all.filter(e => {
    return now - new Date(e.time).getTime() <= MAX_AGE;
  });

  // ✅ 5. 按时间排序（最新在前）
  all.sort((a, b) => new Date(b.time) - new Date(a.time));

  // ✅ 6. 保存
  fs.writeFileSync(FILE, JSON.stringify(all, null, 2));

  console.log("更新完成，当前数据量:", all.length);
}

// 类型识别
function detectType(title) {
  title = title.toLowerCase();

  if (title.includes("kidnap")) return { type: "kidnap", level: 5 };
  if (title.includes("attack") || title.includes("kill")) return { type: "attack", level: 5 };
  if (title.includes("robbery")) return { type: "robbery", level: 4 };
  if (title.includes("protest")) return { type: "protest", level: 3 };
  if (title.includes("accident")) return { type: "accident", level: 2 };

  return { type: "news", level: 1 };
}

// 地点识别
function detectLocation(title) {
  title = title.toLowerCase();

  if (title.includes("lagos")) return { lat: 6.5244, lng: 3.3792 };
  if (title.includes("abuja")) return { lat: 9.0765, lng: 7.3986 };

  return { lat: 9.0820, lng: 8.6753 };
}

fetchNews();
