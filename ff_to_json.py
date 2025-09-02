import requests, json
from datetime import datetime
import pytz

URL = "https://www.dailyfx.com/calendar/filters/high.json"
OUTPUT = "docs/news.json"

def fetch_news():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = []
    tz = pytz.timezone("US/Eastern")

    for event in data.get("events", []):
        title = event.get("title", "")
        date_str = event.get("date")
        if not date_str:
            continue

        # DailyFX gives UTC time
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dt = dt.astimezone(tz)

        results.append({
            "datetime": dt.isoformat(),
            "impact": "High",
            "title": title
        })

    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} high impact events to {OUTPUT}")

if __name__ == "__main__":
    fetch_news()
