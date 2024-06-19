# RSS Aggregator

Simple aggregator for RSS feeds for my own pleasure \
In my example we use Microsoft tech blogs \
https://techcommunity.microsoft.com/t5/security-compliance-and-identity/ct-p/MicrosoftSecurityandCompliance
<br>
```hitem```

### Howto
1. Create a new GitHub repository and upload files: \
    Create a new public GitHub repository (e.g., "rss-aggregator"). You'll store the Python script, aggregated RSS feed and the workflow file in this repository. \
    Personally, i ran the python script localy to generate the ```aggregated_feed.xml``` file - but the workflow should be able to do that for you, but maybe you dont want to wait. If you do so you have to install:
    > pip install feedparser lxml beautifulsoup4

    then run 
    > python3 rss_aggregator.py

2. Set up GitHub Pages:\
    Go to the repository settings, scroll down to the GitHub Pages section, and choose the "main" branch as the source. Save the changes, and you'll get a URL for your GitHub Pages site (e.g., https://```<username>```.github.io/rss-aggregator/).
3. Update the 'link' field in the script:
    Replace the 'link' field in the ```rss_aggregator.py``` script with your GitHub Pages URL:
    ```python
    etree.SubElement(channel, "link").text = "https://<username>.github.io/<repo name>/aggregated_feed.xml"
    ```
4. Update the workflow:\
   Change the timer accordingly in ```rss_aggregator.yml```\
   The Cron job is the main one (how often it runs). But one more such setting is that links are only stored for 365 days under ```name: Update processed links file``` to prevent ```processed_links.txt``` to grow to big.
5. Then you take the link to `aggregated_feed.xml` and paste it in to your RSS hook (and ingest frequenzy to match your cron configuration in `rss_aggregator.yml`) \
Example from teams: \
![image](https://github.com/hitem/rss-aggregator/assets/8977898/cb0fbc33-57a7-4012-8cf7-4f9d36a3c1e0)

### Current Behavior
- **Script Execution:** Cronjob triggers the script every hour, the script then fetches and processes RSS feed entries from the last 2 hours.
- **Link Processing:** It writes new links to `processed_links.txt` and skips links that are already in `processed_links.txt`.

It is possible to change this behavior, but keep in mind: `time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=2)` should never exceed your cron: `'0 */1 * * *'`.
Example: If you collect all the links for the last 30 days, the cron job should never exceed that time - if you do, you will start to get duplicate links.

