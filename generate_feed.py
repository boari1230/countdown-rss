"""Generate a countdown RSS feed XML file with multiple events."""

import datetime
import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---- 設定 ----
# JSON形式で複数イベントを定義
# 例: [{"date": "2026-06-30", "name": "リリース"}, {"date": "2026-12-31", "name": "年末"}]
EVENTS_JSON = os.environ.get("EVENTS", "[]")
FEED_TITLE = os.environ.get("FEED_TITLE", "Countdown RSS")
SITE_URL = os.environ.get("SITE_URL", "https://example.github.io/countdown-rss")
TZ_OFFSET_HOURS = int(os.environ.get("TZ_OFFSET_HOURS", "9"))
# ---- 設定ここまで ----


def _rfc822(dt: datetime.datetime) -> str:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    offset = dt.strftime("%z")
    return (
        f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month - 1]} "
        f"{dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} {offset}"
    )


def build_item(event: dict, now: datetime.datetime) -> dict:
    target_date = event["date"]
    name = event["name"]
    target = datetime.datetime.strptime(target_date, "%Y-%m-%d").replace(
        tzinfo=now.tzinfo
    )
    delta = (target.date() - now.date()).days

    if delta > 0:
        title = f"🔥 {name}まであと {delta} 日！"
        desc = f"{name} ({target_date}) まで残り {delta} 日です。"
    elif delta == 0:
        title = f"🎉 今日は {name} 当日です！"
        desc = f"ついに {name} の日がやってきました！"
    else:
        title = f"✅ {name}から {abs(delta)} 日経過"
        desc = f"{name} ({target_date}) から {abs(delta)} 日が経ちました。"

    return {"title": title, "description": desc, "date": target_date}


def generate_feed() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET_HOURS))
    now = datetime.datetime.now(tz)
    events = json.loads(EVENTS_JSON)

    if not events:
        print("WARNING: EVENTS is empty. Add events to countdown.yml")
        return ""

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = "カウントダウン RSS フィード"
    ET.SubElement(channel, "language").text = "ja"
    ET.SubElement(channel, "lastBuildDate").text = _rfc822(now)

    for event in events:
        data = build_item(event, now)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = data["title"]
        ET.SubElement(item, "description").text = data["description"]
        ET.SubElement(item, "pubDate").text = _rfc822(now)
        ET.SubElement(item, "guid", isPermaLink="false").text = (
            f"countdown-{data['date']}-{now.strftime('%Y%m%d')}"
        )

    rough = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding=None)
    return pretty


if __name__ == "__main__":
    os.makedirs("public", exist_ok=True)
    xml_str = generate_feed()
    if xml_str:
        with open("public/feed.xml", "w", encoding="utf-8") as f:
            f.write(xml_str)
        print("Generated public/feed.xml")
        events = json.loads(EVENTS_JSON)
        for e in events:
            print(f"  - {e['name']} ({e['date']})")
