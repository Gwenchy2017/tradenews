import requests, json
from datetime import datetime
import pytz
import xml.etree.ElementTree as ET

# Forex Factory weekly calendar (XML)
URL = "https://cdn-nfs.forexfactory.net/ffcal_week_this.xml"
OUTPUT = "docs/news.json"

def fetch_news():
    # Fetch XML feed
    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    # Parse XML
    root = ET.fromstring(r.content)
    results = []

    for event in root.findall("event"):
        impact = event.findtext("impact", "").lower()
        if "high" not in impact:
            continue  # only keep High Impact events

        date_str = event.findtext("date")
        time_str = event.findtext("time")
        title = event.findtext("title", "")

        if not date_str or not time_str:
            continue

        try:
            # Parse into datetime
            dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M")
            # Localize to New York time (US/Eastern)
            dt = pytz.timezone("US/Eastern").localize(dt)
        except Exception as e:
            print("Error parsing date/time:", e)
            continue

        results.append({
            "datetime": dt.isoformat(),
            "impact": event.findtext("impact", ""),
            "title": title
        })

    # Save JSON
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} high impact events to {OUTPUT}")

if __name__ == "__main__":
    fetch_news()
