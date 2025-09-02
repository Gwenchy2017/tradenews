#!/usr/bin/env python3
"""
ff_to_json.py
Fetch ForexFactory weekly XML and convert HIGH impact events into a news.json
Output: docs/news.json (NY local times, ISO format)
Requires: requests, python-dateutil, pytz
"""

import requests, xml.etree.ElementTree as ET, json, sys, os
from dateutil import parser as dparser
import pytz
from datetime import datetime, timedelta

# ----- CONFIG -----
FF_XML_URL = "https://cdn-nfs.forexfactory.net/ffcal_week_this.xml"
OUTPUT_PATH = "docs/news.json"   # when used with GitHub Pages set source to docs/
NY_TZ = pytz.timezone("America/New_York")
# ------------------

def parse_ff_xml(xml_text):
    events = []
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        print("XML parse error:", e)
        return events

    # Heuristics: look for element tags that likely contain events
    # (ForexFactory structure may vary; we attempt several strategies)
    for elem in root.iter():
        tag = elem.tag.lower()
        if ('event' in tag) or ('item' in tag) or ('row' in tag) or ('calendar' in tag):
            # Attempt to extract attributes first
            attrib = elem.attrib
            impact = None
            title = None
            dt = None

            # 1) impact (attr or child)
            for k in attrib:
                if 'impact' in k.lower() or 'importance' in k.lower():
                    impact = attrib[k]
            if impact is None:
                for child in elem:
                    if 'impact' in child.tag.lower() or 'importance' in child.tag.lower():
                        impact = (child.text or "").strip()

            # 2) title
            for k in attrib:
                if 'title' in k.lower() or 'event' in k.lower() or 'text' in k.lower():
                    title = attrib[k]
            if title is None:
                for child in elem:
                    if 'title' in child.tag.lower() or 'event' in child.tag.lower() or 'description' in child.tag.lower():
                        title = (child.text or "").strip()

            # 3) datetime: attributes often include date/time or iso
            if 'datetime' in attrib:
                dt = attrib['datetime']
            else:
                # date + time attributes
                date_attr = None
                time_attr = None
                for k in attrib:
                    if 'date' in k.lower() and len(attrib[k].strip())>=6:
                        date_attr = attrib[k].strip()
                    if 'time' in k.lower() and len(attrib[k].strip())>=3:
                        time_attr = attrib[k].strip()
                if date_attr and time_attr:
                    dt = date_attr + " " + time_attr

            # fallback: child tags for date/time
            if dt is None:
                date_text = None
                time_text = None
                for child in elem:
                    tagc = child.tag.lower()
                    if 'date' in tagc and child.text:
                        date_text = child.text.strip()
                    if 'time' in tagc and child.text:
                        time_text = child.text.strip()
                if date_text and time_text:
                    dt = date_text + " " + time_text

            # If we have impact that maps to High, keep it
            is_high = False
            if impact:
                s = str(impact).lower()
                if s.isdigit():
                    # often 3 = high, 2 = med, 1 = low
                    try:
                        if int(s) >= 3: is_high = True
                    except: pass
                else:
                    if 'high' in s: is_high = True
                    if 'h' == s: is_high = True

            # If no impact info, skip (we only want high)
            if not is_high:
                continue

            # parse dt (if none, skip)
            if not dt:
                # Some feeds provide a combined timestamp as text
                # try to find any child with an ISO-like text
                found = False
                for child in elem.iter():
                    txt = (child.text or "").strip()
                    if len(txt) >= 10 and (':' in txt or '-' in txt):
                        try:
                            dparser.parse(txt)
                            dt = txt
                            found = True
                            break
                        except:
                            continue
                if not found:
                    continue

            # Parse datetime; if no timezone given, treat it as NY local
            try:
                dt_parsed = dparser.parse(dt)
            except Exception as e:
                # skip if not parseable
                print("Could not parse dt:", dt, "err:", e)
                continue

            # If parsed datetime has no tzinfo, assume NY local
            if dt_parsed.tzinfo is None:
                dt_ny = NY_TZ.localize(dt_parsed)
            else:
                # convert to NY
                dt_ny = dt_parsed.astimezone(NY_TZ)

            # format to ISO without offset (EA expects NY local like "YYYY-MM-DDTHH:MM:SS")
            iso_ny = dt_ny.strftime("%Y-%m-%dT%H:%M:%S")

            # title fallback
            if not title:
                title = (elem.text or "").strip()[:120]

            events.append({
                "datetime": iso_ny,
                "impact": "high",
                "title": title or "event"
            })

    # deduplicate & sort
    unique = { (e['datetime'], e['title']): e for e in events }
    evs = sorted(unique.values(), key=lambda x: x['datetime'])
    return evs

def main():
    print("Fetching ForexFactory XML...")
    try:
        r = requests.get(FF_XML_URL, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        print("Failed to fetch FF XML:", e)
        sys.exit(1)

    events = parse_ff_xml(r.text)
    if not events:
        print("No high-impact events found (check feed or parsing).")
    else:
        print(f"Found {len(events)} high-impact events.")

    # ensure docs folder exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print("Wrote:", OUTPUT_PATH)

if __name__ == "__main__":
    main()
