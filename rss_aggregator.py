#!/usr/bin/env python3
# Auth: hitem
import subprocess
import asyncio
import aiohttp
import feedparser
from lxml import etree
import datetime
import calendar
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Ensure our local copy is exactly in sync with origin/main.
try:
    subprocess.run(["git", "fetch", "origin"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
except Exception as e:
    print(f"Error during git reset: {e}")

# Set to True for appending, False for overwriting
append_mode = False
# Set the maximum age for entries in days when in append mode
max_age_days = 365

# Define the list of RSS feed URLs
rss_feed_urls = [
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftSecurityandCompliance",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=CoreInfrastructureandSecurityBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=AzureNetworkSecurityBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftThreatProtectionBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftDefenderCloudBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftDefenderATPBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftDefenderIoTBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=DefenderExternalAttackSurfaceMgmtBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=Vulnerability-Management",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=DefenderThreatIntelligence",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftSecurityExperts",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=Microsoft-Security-Baselines",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftSentinelBlog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftDefenderforOffice365Blog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=microsoft-security-blog",
    "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=microsoft-entra-blog",
]

# Set the output file name and state file
output_file = "aggregated_feed.xml"
processed_links_file = "processed_links.txt"

# Define the time threshold: only process entries from the last 2 hours.
recent_time_threshold = datetime.datetime.now(
    datetime.timezone.utc) - datetime.timedelta(hours=2)

# Helper to normalize URLs (remove fragments, queries, and trailing slashes)
from urllib.parse import urlparse

def normalize_url(url):
    parsed = urlparse(url.strip())
    return parsed._replace(fragment="", query="").geturl().rstrip("/")

# Read previously processed links
try:
    with open(processed_links_file, "r") as f:
        processed_links = set(normalize_url(line.split()[1]) for line in f if line.strip())
except FileNotFoundError:
    processed_links = set()

# Asynchronous function to fetch RSS feed content
async def fetch_rss_feed(url, session):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                return feedparser.parse(content)
            else:
                print(f"Error fetching {url}: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# Convert struct_time to datetime with UTC timezone
def struct_time_to_datetime(t):
    timestamp = calendar.timegm(t)
    return datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=datetime.timezone.utc)

# Main asynchronous function to process RSS feeds
async def process_feeds():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rss_feed(url, session) for url in rss_feed_urls]
        feeds = await asyncio.gather(*tasks)

        # Gather all entries from all feeds
        all_entries = []
        for feed in feeds:
            if feed and feed.entries:
                all_entries.extend(feed.entries)

        # Remove duplicates from the current run and ignore already processed links
        deduped_entries = {}
        for entry in all_entries:
            if hasattr(entry, "link"):
                norm_link = normalize_url(entry.link)
                if norm_link not in processed_links:
                    deduped_entries.setdefault(norm_link, entry)
        unique_entries = list(deduped_entries.values())

        # Filter for recent entries using the published time
        recent_entries = []
        for entry in unique_entries:
            if hasattr(entry, 'published_parsed'):
                entry_datetime = struct_time_to_datetime(entry.published_parsed)
                if entry_datetime >= recent_time_threshold:
                    recent_entries.append(entry)

        # Sort entries by published time, most recent first
        sorted_entries = sorted(
            recent_entries, key=lambda x: x.published_parsed, reverse=True)

        # Append new links to processed_links.txt immediately
        with open(processed_links_file, "a") as f:
            for entry in sorted_entries:
                try:
                    timestamp = datetime.datetime.strptime(
                        entry.published, "%a, %d %b %Y %H:%M:%S %Z"
                    ).strftime("%Y-%m-%dT%H:%M:%S")
                    f.write(f"{timestamp} {normalize_url(entry.link)}\n")
                except Exception:
                    continue  # Skip malformed or missing dates

        # Update the aggregated XML feed with the new entries
        update_feed(sorted_entries)
        return sorted_entries

# Function to update or create the XML feed
def update_feed(sorted_entries):
    now = datetime.datetime.now(datetime.timezone.utc)

    if append_mode and os.path.exists(output_file):
        # Load existing feed if appending
        tree = etree.parse(output_file)
        root = tree.getroot()
        channel = root.find("channel")
    else:
        # Otherwise, create a new feed structure
        root = etree.Element("rss", version="2.0")
        channel = etree.SubElement(root, "channel")
        etree.SubElement(channel, "title").text = "RSS Aggregator Feed"
        etree.SubElement(
            channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
        etree.SubElement(
            channel, "description").text = "An aggregated feed of Microsoft blogs"

    # Update lastBuildDate element
    last_build_date = channel.find("lastBuildDate")
    if last_build_date is None:
        last_build_date = etree.SubElement(channel, "lastBuildDate")
    last_build_date.text = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Add new entries to the feed
    for entry in sorted_entries:
        if not hasattr(entry, "title") or not hasattr(entry, "link"):
            continue
        item = etree.SubElement(channel, "item")
        etree.SubElement(item, "title").text = entry.title
        etree.SubElement(item, "link").text = entry.link
        etree.SubElement(item, "pubDate").text = entry.published
        etree.SubElement(item, "guid", isPermaLink="false").text = entry.id if hasattr(
            entry, "id") else entry.link
        soup = BeautifulSoup(entry.summary, "lxml") if hasattr(
            entry, "summary") else None
        summary_text = soup.get_text() if soup else "No summary available."
        limited_summary = summary_text[:600] + \
            "..." if len(summary_text) > 350 else summary_text
        etree.SubElement(item, "description").text = limited_summary

    # Write the updated feed to file
    with open(output_file, "wb") as f:
        f.write(etree.tostring(root, pretty_print=True))

# Run the feed processing
sorted_entries = asyncio.run(process_feeds())

# Output the RSS feed entry count
if "GITHUB_ENV" in os.environ:
    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")
else:
    print(f"RSS_FEED_ENTRIES={len(sorted_entries)}")