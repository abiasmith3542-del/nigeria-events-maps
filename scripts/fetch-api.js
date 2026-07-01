const fs = require("fs");
const fetch = require("node-fetch");

const API_KEY = "pub_92a3062b63da4ee3b31c528e88c0e618";
const FILE = "./data/events.json";

async function fetchNews() {
  try {
    const res = await fetch(`https://newsdata.io/api/1/news?apikey=${API_KEY}&q=Nigeria&country=ng`);
    const json = await res.json();

    if (!json.results) {
      console.log("API异常:", json);
      return;
    }

    let oldData = [];
    if (fs.existsSync(FILE)) {
      oldData = JSON.parse(fs.readFileSync(FILE));
    }

    let newEvents = json.results.map(item => ({
      title: item.title,
      time: new Date(item.pubDate).toISOString(),
      lat: 9.0820,
      lng: 8.6753,
      level: 3
    }));

    let all = [...oldData, ...newEvents];

    // 去重
    const seen = new Set();
    all = all.filter(e => {
      if (seen.has(e.title)) return false;
      seen.add(e.title);
      return true;
    });

    fs.writeFileSync(FILE, JSON.stringify(all, null, 2));

    console.log("成功更新:", all.length);

  } catch (err) {
    console.log("运行失败:", err);
    process.exit(1); // 关键：显示错误
  }
}

fetchNews();
