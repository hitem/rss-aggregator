#!/usr/bin/env python3
# Auth: hitem

import asyncio
import aiohttp
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

# Read previously processed links
try:
    with open(processed_links_file, "r") as f:
        processed_links = set(line.split()[1] for line in f if line.strip())
except FileNotFoundError:
    processed_links = set()

# Set time threshold for recent posts
time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)

# Asynchronous function to fetch and parse articles from a blog page
async def fetch_blog_articles(url, session):
    articles = []
    print(f"Fetching articles from: {url}")
    try:
        async with session.get(url, timeout=10) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")
            
            # Select articles based on the new HTML structure
            found_articles = soup.find_all("article", {"data-testid": "MessageViewCard"})
            print(f"Found {len(found_articles)} articles on {url}")
            for article in found_articles[:5]:  # Limit to avoid excessive output
                
                # Extract title and link
                title_elem = article.find("a", {"class": "MessageViewCard_lia-subject-link__OhaPD"})
                if title_elem:
                    title = title_elem["aria-label"]
                    link = "https://techcommunity.microsoft.com" + title_elem["href"]
                
                # Extract publication date
                date_elem = article.find("a", {"class": "MessageViewCard_lia-timestamp__pG_bu"}).find("span", {"data-testid": "messageTime"})
                if date_elem and date_elem.span:
                    date_str = date_elem.span["title"].split(" at")[0]  # Remove the time portion if present

                    # Try parsing with both month formats
                    try:
                        pub_date = datetime.datetime.strptime(date_str, "%B %d, %Y")  # Full month name
                    except ValueError:
                        try:
                            pub_date = datetime.datetime.strptime(date_str, "%b %d, %Y")  # Abbreviated month name
                        except ValueError as e:
                            print(f"Date parsing error for {title}: {e}")
                            continue

                    pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)  # Ensure it's timezone-aware
                    
                    # Only add articles that are recent and not already processed
                    if link not in processed_links:
                        summary_elem = article.find("div", {"data-testid": "MessageTeaser"})
                        summary = summary_elem.get_text(strip=True) if summary_elem else "No summary available."
                        articles.append({
                            "title": title,
                            "link": link,
                            "pubDate": pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                            "description": summary[:600] + "..." if len(summary) > 600 else summary,
                        })
                        print(f"Added article: {title}")
                    else:
                        print(f"Article already processed: {title}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    
    return articles

# Main asynchronous function to handle all URL requests concurrently
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_blog_articles(url, session) for url in blog_urls]
        results = await asyncio.gather(*tasks)

        # Flatten the list of lists into a single list of articles
        all_entries = [item for sublist in results for item in sublist]

        # Sort entries by published date in descending order
        sorted_entries = sorted(all_entries, key=lambda x: x["pubDate"], reverse=True)

        # Create a new XML tree for the aggregated feed
        root = etree.Element("rss", version="2.0")
        channel = etree.SubElement(root, "channel")
        etree.SubElement(channel, "title").text = "HTML Aggregator Feed"
        etree.SubElement(channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
        etree.SubElement(channel, "description").text = "An aggregated feed of Microsoft blogs"
        etree.SubElement(channel, "lastBuildDate").text = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

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

        # Set the RSS_FEED_ENTRIES environment variable for GitHub Actions
        if "GITHUB_ENV" in os.environ:
            with open(os.environ["GITHUB_ENV"], "a") as f:
                f.write(f"RSS_FEED_ENTRIES={len(sorted_entries)}\n")
        else:
            print(f"RSS_FEED_ENTRIES={len(sorted_entries)}")  # For local testing

# Run the main function
asyncio.run(main())