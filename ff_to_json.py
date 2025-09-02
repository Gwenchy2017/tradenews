import requests, xmltodict, json
from datetime import datetime
import pytz

URL = "https://cdn-nfs.forexfactory.net/ffcal_week_this.xml"
OUTPUT = "docs/news.json"

def fetch_news():
    r = requests.get(URL)
    r.raise_for_status()
    data = xmltodict.parse(r.content)
    events = data["weeklyevents"]["event"]
    results = []

    for e in events:
        impact = e.get("impact", "").lower()
        if "high" not in impact:
            continue  # only keep high impact news

        # convert time to New York timezone
        dt_str = e["date"] + " " + e["time"]
        dt = datetime.strptime(dt_str, "%m/%d/%Y %H:%M")
        dt = pytz.timezone("US/Eastern").localize(dt)

        results.append({
            "datetime": dt.isoformat(),
            "impact": e["impact"],
            "title": e["title"]
        })

    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    fetch_news()
