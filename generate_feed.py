"""Generate a countdown RSS feed XML file from events.json."""

import datetime
import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---- 設定 ----
FEED_TITLE = os.environ.get("FEED_TITLE", "Countdown RSS")
SITE_URL = os.environ.get("SITE_URL", "https://example.github.io/countdown-rss")
TZ_OFFSET_HOURS = int(os.environ.get("TZ_OFFSET_HOURS", "9"))
EVENTS_FILE = os.environ.get("EVENTS_FILE", "events.json")
# ---- 設定ここまで ----


def load_events(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_item(name: str, target_date: str, now: datetime.datetime) -> dict:
    tz = now.tzinfo
    target = datetime.datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=tz)
    delta = (target.date() - now.date()).days

    if delta > 0:
        title = f"\U0001f525 {name}まであと {delta} 日！"
        desc = f"{name} ({target_date}) まで残り {delta} 日です。"
    elif delta == 0:
        title = f"\U0001f389 今日は {name} 当日です！"
        desc = f"ついに {name} の日がやってきました！"
    else:
        title = f"\u2705 {name}から {abs(delta)} 日経過"
        desc = f"{name} ({target_date}) から {abs(delta)} 日が経ちました。"

    return {"title": title, "description": desc, "date": target_date}


def generate_feed(events: list[dict]) -> str:
    tz = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET_HOURS))
    now = datetime.datetime.now(tz)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = "複数イベントへのカウントダウン"
    ET.SubElement(channel, "language").text = "ja"
    ET.SubElement(channel, "lastBuildDate").text = _rfc822(now)

    items = [build_item(e["name"], e["date"], now) for e in events]
    items.sort(key=lambda x: x["date"])

    for it in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = it["title"]
        ET.SubElement(item, "description").text = it["description"]
        ET.SubElement(item, "pubDate").text = _rfc822(now)
        guid_slug = it["date"].replace("-", "")
        ET.SubElement(item, "guid", isPermaLink="false").text = (
            f"countdown-{guid_slug}-{now.strftime('%Y%m%d')}"
        )

    rough = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding=None)
    return pretty


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


if __name__ == "__main__":
    events = load_events(EVENTS_FILE)
    print(f"Loaded {len(events)} event(s) from {EVENTS_FILE}:")
    for e in events:
        print(f"  - {e['name']} ({e['date']})")

    os.makedirs("public", exist_ok=True)
    xml_str = generate_feed(events)
    with open("public/feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print("Generated public/feed.xml")
