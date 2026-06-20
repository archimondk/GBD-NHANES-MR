"""
Find correct NHANES file names for cycles that failed.
"""

import urllib.request
import re
from html.parser import HTMLParser


class XPTLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.xpt_links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        d = dict(attrs)
        href = d.get("href", "")
        text = d.get("title", "")
        if ".xpt" in href.lower():
            self.xpt_links.append((href, text))


# Try data documentation pages for 2001-2002 and 2003-2004
# looking for PBCD and GLU alternatives
components = {
    "Laboratory": ["GLU", "PBCD", "L06", "LAB06", "LAB10"],
}

for year in ["2001", "2003"]:
    for comp, keywords in components.items():
        url = (
            f"https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx"
            f"?Component={comp}&CycleBeginYear={year}"
        )
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            resp = urllib.request.urlopen(req, timeout=15)
            html = resp.read().decode("utf-8", errors="replace")

            # Find all data file references
            for kw in keywords:
                if kw.lower() in html.lower():
                    # Show context around matches
                    idx = html.lower().find(kw.lower())
                    ctx = html[max(0, idx - 200) : idx + 200]
                    xpt_match = re.search(r'[\w_]+\.xpt', ctx, re.I)
                    if xpt_match:
                        print(f"Year {year} / {comp}: found '{kw}' -> {xpt_match.group()}")
        except Exception as e:
            print(f"Year {year} / {comp}: {e}")

# Also try direct data file listing
print("\n-- Trying DataFiles directory page for 2001 --")
url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2001/DataFiles/"
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8", errors="replace")
    parser = XPTLinkParser()
    parser.feed(html)
    for href, title in parser.xpt_links:
        print(f"  {href}")
except Exception as e:
    print(f"  Error: {e}")

print("\n-- Trying DataFiles directory page for 2003 --")
url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/"
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8", errors="replace")
    parser = XPTLinkParser()
    parser.feed(html)
    for href, title in parser.xpt_links:
        print(f"  {href}")
except Exception as e:
    print(f"  Error: {e}")
