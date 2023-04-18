#!/usr/bin/env python3
# Auth: hitem

import feedparser
from lxml import etree
import datetime
import os

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
]

# Set the output file name
output_file = "aggregated_feed.xml"

# Parse and aggregate the RSS feeds
all_entries = []
for url in rss_feed_urls:
    feed = feedparser.parse(url)
    all_entries.extend(feed.entries)

# Remove duplicates based on the 'title', 'published', and 'link' fields
entry_key = lambda entry: (entry.title, entry.published, entry.link)
unique_entries = {entry_key(entry): entry for entry in all_entries}.values()

# Filter entries published within the last 2 hours
time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
recent_entries = [entry for entry in unique_entries if datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z") >= time_threshold]

# Filter out entries older than a year
max_age = datetime.datetime.utcnow() - datetime.timedelta(days=365)
filtered_entries = [entry for entry in recent_entries if datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z") >= max_age]

# Sort entries by published date in descending order
sorted_entries = sorted(filtered_entries, key=lambda x: x.published_parsed, reverse=True)

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
    # Change number depending on how many lines you want to include
    line_summary = '\n'.join(entry.summary.split('\n')[:5])
    etree.SubElement(item, "description").text = line_summary

# Write the output to a file
with open(output_file, "wb") as f:
    f.write(etree.tostring(root, pretty_print=True))

# Set the RSS_FEED_ENTRIES environment variable
with open(os.environ["GITHUB_ENV"], "a") as f:
    f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")