"""Generate a countdown RSS feed XML file."""

import datetime
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ---- 設定 ----
TARGET_DATE = os.environ.get("TARGET_DATE", "2025-12-31")  # YYYY-MM-DD
EVENT_NAME = os.environ.get("EVENT_NAME", "イベント")
FEED_TITLE = os.environ.get("FEED_TITLE", "Countdown RSS")
SITE_URL = os.environ.get("SITE_URL", "https://example.github.io/countdown-rss")
TZ_OFFSET_HOURS = int(os.environ.get("TZ_OFFSET_HOURS", "9"))  # JST=9
# ---- 設定ここまで ----


def generate_feed() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET_HOURS))
    now = datetime.datetime.now(tz)
    target = datetime.datetime.strptime(TARGET_DATE, "%Y-%m-%d").replace(tzinfo=tz)
    delta = (target.date() - now.date()).days

    if delta > 0:
        title_text = f"🔥 {EVENT_NAME}まであと {delta} 日！"
        desc_text = (
            f"{EVENT_NAME} ({TARGET_DATE}) まで残り {delta} 日です。\n"
            f"今日は {now.strftime('%Y-%m-%d')} です。"
        )
    elif delta == 0:
        title_text = f"🎉 今日は {EVENT_NAME} 当日です！"
        desc_text = f"ついに {EVENT_NAME} の日がやってきました！"
    else:
        title_text = f"✅ {EVENT_NAME}から {abs(delta)} 日経過"
        desc_text = f"{EVENT_NAME} ({TARGET_DATE}) から {abs(delta)} 日が経ちました。"

    # Build RSS 2.0 XML
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = f"{EVENT_NAME} ({TARGET_DATE}) へのカウントダウン"
    ET.SubElement(channel, "language").text = "ja"
    ET.SubElement(channel, "lastBuildDate").text = _rfc822(now)

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title_text
    ET.SubElement(item, "description").text = desc_text
    ET.SubElement(item, "pubDate").text = _rfc822(now)
    ET.SubElement(item, "guid", isPermaLink="false").text = (
        f"countdown-{now.strftime('%Y%m%d')}"
    )

    rough = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding=None)
    # minidom adds an xml declaration; keep it
    return pretty


def _rfc822(dt: datetime.datetime) -> str:
    """Format datetime as RFC-822 for RSS <pubDate>."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    offset = dt.strftime("%z")  # e.g. "+0900"
    return (
        f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month - 1]} "
        f"{dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} {offset}"
    )


if __name__ == "__main__":
    os.makedirs("public", exist_ok=True)
    xml_str = generate_feed()
    with open("public/feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"Generated public/feed.xml")
    print(f"  TARGET_DATE : {TARGET_DATE}")
    print(f"  EVENT_NAME  : {EVENT_NAME}")
