#!/usr/bin/env python3
# Auth: hitem

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from lxml import etree
import datetime
import os

# Set to True for appending, False for overwriting
append_mode = False
# Set the maximum age for entries in days when in append mode
max_age_days = 365

# Define the list of blog page URLs
blog_urls = [
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftsecurityandcompliance",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/identity",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/coreinfrastructureandsecurityblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/azurenetworksecurityblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftthreatprotectionblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftdefendercloudblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/securitycopilotblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftdefenderatpblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftdefenderiotblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftdefenderforoffice365blog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/vulnerability-management",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoft-security-baselines",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftsentinelblog",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/defenderthreatintelligence",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/microsoftsecurityexperts",
    "https://techcommunity.microsoft.com/category/microsoftsecurityandcompliance/blog/defenderexternalattacksurfacemgmtblog",

]

# Set the output file name
output_file = "aggregated_feed.xml"
processed_links_file = "processed_links.txt"

# Read previously processed links
try:
    with open(processed_links_file, "r") as f:
        processed_links = set(line.split()[1] for line in f if line.strip())
except FileNotFoundError:
    processed_links = set()

# Set time threshold for recent posts (2 hours for checking new entries)
recent_time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)

# Set max age time threshold if append mode is enabled
if append_mode:
    max_age_time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=max_age_days)

# Asynchronous function to fetch and parse articles from a blog page
async def fetch_blog_articles(url, session):
    articles = []
    try:
        async with session.get(url, timeout=10) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")
            
            # Select articles based on the HTML structure
            found_articles = soup.find_all("article", {"data-testid": "MessageViewCard"})
            for article in found_articles:
                title_elem = article.find("a", {"data-testid": "MessageLink"})
                if title_elem and "aria-label" in title_elem.attrs:
                    title = title_elem["aria-label"]
                    link = "https://techcommunity.microsoft.com" + title_elem["href"]
                
                date_elem = article.find("span", {"title": True})
                if date_elem:
                    date_str = date_elem["title"].split(" at")[0]
                    try:
                        pub_date = datetime.datetime.strptime(date_str, "%B %d, %Y")
                    except ValueError:
                        try:
                            pub_date = datetime.datetime.strptime(date_str, "%b %d, %Y")
                        except ValueError:
                            continue
                    pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
                    
                    # Filter by recent time threshold and processed links
                    if pub_date >= recent_time_threshold and link not in processed_links:
                        summary_elem = article.find("div", {"data-testid": "MessageTeaser"})
                        summary = summary_elem.get_text(strip=True) if summary_elem else "No summary available."
                        articles.append({
                            "title": title,
                            "link": link,
                            "pubDate": pub_date.strftime("%Y-%m-%dT%H:%M:%S"),  # Changed format to ISO format
                            "description": summary[:600] + "..." if len(summary) > 600 else summary,
                        })
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    
    return articles

# Main asynchronous function to handle all URL requests concurrently
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_blog_articles(url, session) for url in blog_urls]
        results = await asyncio.gather(*tasks)
        all_entries = [item for sublist in results for item in sublist]
        
        # Sort entries by published date
        sorted_entries = sorted(all_entries, key=lambda x: x["pubDate"], reverse=True)

        # Load existing XML if appending
        if append_mode and os.path.exists(output_file):
            tree = etree.parse(output_file)
            root = tree.getroot()
            channel = root.find("channel")

            # Remove old entries beyond max_age_days in append mode
            for item in channel.findall("item"):
                pub_date = item.find("pubDate").text
                pub_datetime = datetime.datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S")
                if pub_datetime < max_age_time_threshold:
                    channel.remove(item)
        else:
            # Create new XML structure if overwriting or file doesn't exist
            root = etree.Element("rss", version="2.0")
            channel = etree.SubElement(root, "channel")
            etree.SubElement(channel, "title").text = "HTML Aggregator Feed"
            etree.SubElement(channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
            etree.SubElement(channel, "description").text = "An aggregated feed of Microsoft blogs"

        # Ensure lastBuildDate exists and is updated
        last_build_date = channel.find("lastBuildDate")
        if last_build_date is None:
            last_build_date = etree.SubElement(channel, "lastBuildDate")
        last_build_date.text = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Append new entries to the feed
        for entry in sorted_entries:
            item = etree.SubElement(channel, "item")
            etree.SubElement(item, "title").text = entry["title"]
            etree.SubElement(item, "link").text = entry["link"]
            etree.SubElement(item, "pubDate").text = entry["pubDate"]
            etree.SubElement(item, "description").text = entry["description"]

        # Write to the output file
        with open(output_file, "wb") as f:
            f.write(etree.tostring(root, pretty_print=True))

        # Update processed links file with new entries
        with open(processed_links_file, "a") as f:
            for entry in sorted_entries:
                f.write(f"{entry['pubDate']} {entry['link']}\n")

        # Output RSS feed entry count
        if "GITHUB_ENV" in os.environ:
            with open(os.environ["GITHUB_ENV"], "a") as f:
                f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")
        else:
            print(f"RSS_FEED_ENTRIES={len(sorted_entries)}")  # For local testing

# Run the main function
asyncio.run(main())
