#!/usr/bin/env python3
# Auth: hitem

import feedparser
from lxml import etree
import datetime
import os
from bs4 import BeautifulSoup

# Define the list of RSS feed URLs
rss_feed_urls = [
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftSecurityandCompliance",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=Identity",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=CoreInfrastructureandSecurityBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=AzureNetworkSecurityBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=IdentityStandards",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftThreatProtectionBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftDefenderCloudBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftDefenderATPBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftDefenderIoTBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=DefenderExternalAttackSurfaceMgmtBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=Vulnerability-Management",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=DefenderThreatIntelligence",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftSecurityExperts",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=Microsoft-Security-Baselines",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftSentinelBlog",
    "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=MicrosoftDefenderforOffice365Blog",
]

# Set the output file name
output_file = "aggregated_feed.xml"

# Read previously processed links
with open("processed_links.txt", "r") as f:
    processed_links = set(line.split(maxsplit=1)[1].strip() for line in f if line.strip())

# Parse and aggregate the RSS feeds
all_entries = []
for url in rss_feed_urls:
    feed = feedparser.parse(url)
    all_entries.extend(feed.entries)

# Remove duplicates based on the 'link' field and filter out already processed links
unique_entries = [entry for entry in all_entries if entry.link not in processed_links]

# Filter entries published within the last 60 days
time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
recent_entries = [entry for entry in unique_entries if datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z") >= time_threshold]

# Sort entries by published date in descending order
sorted_entries = sorted(recent_entries, key=lambda x: x.published_parsed, reverse=True)

# Create a new XML tree for the aggregated RSS feed
root = etree.Element("rss", version="2.0")
channel = etree.SubElement(root, "channel")
etree.SubElement(channel, "title").text = "RSS Aggregator Feed"
etree.SubElement(channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
etree.SubElement(channel, "description").text = "An aggregated feed of Microsoft blogs"
etree.SubElement(channel, "lastBuildDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# Add entries to the new feed
for entry in sorted_entries:
    item = etree.SubElement(channel, "item")
    etree.SubElement(item, "title").text = entry.title
    etree.SubElement(item, "link").text = entry.link
    etree.SubElement(item, "pubDate").text = entry.published
    etree.SubElement(item, "guid", isPermaLink="false").text = entry.id if hasattr(entry, "id") else entry.link
    soup = BeautifulSoup(entry.summary, "lxml")
    summary_text = soup.get_text()
    limited_summary = summary_text[:600] + "..." if len(summary_text) > 350 else summary_text
    etree.SubElement(item, "description").text = limited_summary

# Write the output to a file
with open(output_file, "wb") as f:
    f.write(etree.tostring(root, pretty_print=True))

# Implement logic to keep processed links from the last 600 days only
retention_period = datetime.timedelta(days=600)
current_time = datetime.datetime.utcnow()

# Read and filter the existing processed links
with open("processed_links.txt", "r") as f:
    existing_entries = [line for line in f if line.strip() and (current_time - datetime.datetime.strptime(line.split(maxsplit=1)[0], "%Y-%m-%dT%H:%M:%S") <= retention_period)]

# Append new entries
new_entries = [f"{datetime.datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%dT%H:%M:%S')} {entry.link}\n" for entry in recent_entries]

# Write the cleaned and updated list back to the file
with open("processed_links.txt", "w") as f:
    f.writelines(existing_entries + new_entries)

# Set the RSS_FEED_ENTRIES environment variable
with open(os.environ["GITHUB_ENV"], "a") as f:
    f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")