#!/usr/bin/env python3
# Auth: hitem

import requests
from bs4 import BeautifulSoup
from lxml import etree
import datetime
import os

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

# Initialize requests session for reusing the connection
session = requests.Session()

# Read previously processed links
try:
    with open(processed_links_file, "r") as f:
        processed_links = set(line.split()[1] for line in f if line.strip())
except FileNotFoundError:
    processed_links = set()

# Set time threshold for recent posts
time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
all_entries = []

# Function to fetch and parse articles from a blog page with a timeout
def fetch_blog_articles(url):
    try:
        response = session.get(url, timeout=10)  # Timeout after 10 seconds
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []  # Return an empty list if there is an error

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # Adjust selectors based on your page structure
    for article in soup.find_all("div", class_="techcommunity-blog-post"):
        title_elem = article.find("h2", class_="blog-post-title")
        link_elem = title_elem.find("a") if title_elem else None
        date_elem = article.find("span", class_="blog-post-date")
        summary_elem = article.find("div", class_="blog-post-summary")

        # Extract details if elements are found
        if title_elem and link_elem and date_elem and summary_elem:
            title = title_elem.get_text(strip=True)
            link = "https://techcommunity.microsoft.com" + link_elem["href"]
            date_str = date_elem.get_text(strip=True)
            pub_date = datetime.datetime.strptime(date_str, "%b %d, %Y")
            
            # Only add articles that are recent and not already processed
            if pub_date >= time_threshold and link not in processed_links:
                summary = summary_elem.get_text(strip=True)[:600] + "..."
                articles.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "description": summary,
                })
    return articles

# Scrape each blog page and collect recent articles
for url in blog_urls:
    all_entries.extend(fetch_blog_articles(url))

# Sort entries by published date in descending order
sorted_entries = sorted(all_entries, key=lambda x: x["pubDate"], reverse=True)

# Create a new XML tree for the aggregated feed
root = etree.Element("rss", version="2.0")
channel = etree.SubElement(root, "channel")
etree.SubElement(channel, "title").text = "HTML Aggregator Feed"
etree.SubElement(channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
etree.SubElement(channel, "description").text = "An aggregated feed of Microsoft blogs"
etree.SubElement(channel, "lastBuildDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# Add entries to the feed
for entry in sorted_entries:
    item = etree.SubElement(channel, "item")
    etree.SubElement(item, "title").text = entry["title"]
    etree.SubElement(item, "link").text = entry["link"]
    etree.SubElement(item, "pubDate").text = entry["pubDate"]
    etree.SubElement(item, "description").text = entry["description"]

# Write the output to a file
with open(output_file, "wb") as f:
    f.write(etree.tostring(root, pretty_print=True))

# Update the processed links file with new links
with open(processed_links_file, "a") as f:
    for entry in sorted_entries:
        f.write(f"{entry['pubDate']} {entry['link']}\n")

# Conditionally set the RSS_FEED_ENTRIES environment variable
if "GITHUB_ENV" in os.environ:
    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")
else:
    print(f"RSS_FEED_ENTRIES={len(sorted_entries)}")  # For local testing
