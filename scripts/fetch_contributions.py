#!/usr/bin/env python3
"""
Scrape public contribution counts from GitHub and write data/contributions.json.

No token. GitHub already serves the calendar at
https://github.com/users/<username>/contributions

    python scripts/fetch_contributions.py
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "vaiibhavkale")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_days():
    response = requests.get(
        URL,
        headers={"User-Agent": "profile-readme-bot/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found", file=sys.stderr)
        sys.exit(1)

    days = []
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        tooltip = None
        cell_id = cell.get("id")
        if cell_id:
            tooltip = soup.find("tool-tip", attrs={"for": cell_id})
        text = tooltip.get_text(strip=True) if tooltip else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            match = re.match(r"(\d+)", text)
            count = int(match.group(1)) if match else 0
        level = int(cell.get("data-level") or 0)
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda item: item["date"])
    # The table repeats nothing, but guard against duplicate dates.
    unique = {}
    for day in days:
        unique[day["date"]] = day
    return [unique[key] for key in sorted(unique)]


def current_streak(days):
    index = len(days) - 1
    if days[index]["count"] == 0:
        index -= 1
    length = 0
    end_index = index
    while index >= 0 and days[index]["count"] > 0:
        length += 1
        index -= 1
    if length == 0:
        return 0, None, None
    return length, days[index + 1]["date"], days[end_index]["date"]


def longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start = None
    for index, day in enumerate(days):
        if day["count"] > 0:
            if run == 0:
                run_start = index
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start]["date"]
                longest_end = day["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days):
    total = sum(day["count"] for day in days)
    active_days = sum(1 for day in days if day["count"] > 0)
    best = max(days, key=lambda day: day["count"])
    cur_len, cur_start, cur_end = current_streak(days)
    long_len, long_start, long_end = longest_streak(days)

    monthly = {}
    for day in days:
        key = day["date"][:7]
        monthly[key] = monthly.get(key, 0) + day["count"]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": key, "total": value} for key, value in sorted(monthly.items())],
        "days": days,
    }


def main():
    days = fetch_days()
    data = build_data(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print(
        f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
        f"current streak {data['current_streak']['length']}, "
        f"longest streak {data['longest_streak']['length']}"
    )


if __name__ == "__main__":
    main()
