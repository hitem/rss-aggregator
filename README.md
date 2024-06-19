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
5. Then you take the link to `aggregated_feed.xml` and paste it in to your RSS hook (and digest frequenzy to match your cron configuration in `rss_aggregator.yml`) \
Example from teams: \
![image](https://github.com/hitem/rss-aggregator/assets/8977898/cb0fbc33-57a7-4012-8cf7-4f9d36a3c1e0)

### Current Behavior
- **Script Execution:** The cron job triggers the script every hour. The script fetches and processes RSS feed entries from the last 2 hours.
- **Link Processing:** The script writes new links to `processed_links.txt` and skips links that are already present in `processed_links.txt`.

# Customizing Behavior
If you wish to change the time window for link collection, ensure that `time_threshold` does not exceed your cron job interval. For example:  
- **Time Threshold Setting:** `time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=2)`  
- **Cron Job Interval:** `'0 */1 * * *'`

**Important:** The `time_threshold` should never exceed the cron job interval. If you want to collect links for a longer period (e.g., the last 30 days), ensure your cron job interval accommodates this timeframe. The Digest timer should also match your cron job interval to avoid duplicate entries.

### Recommendations
To maintain comprehensive and timely updates, align the Digest interval with the cron job interval or a multiple of the processing window to ensure no links are missed. Here are specific recommendations:  
- **Align with the Cron Job:** Keep the Digest interval at 1 hour to match the cron job and processing window. This alignment ensures no links are missed and duplicates are avoided.  
- **Match Processing Window:** If a less frequent Digest is preferred, set it to 2 hours, matching the script's processing window. This setting ensures comprehensive coverage without duplication.  
- **Extended Time Window:** If you wish to collect and process links over a longer period, such as 30 days, set the script's time threshold to 30 days and adjust the Digest interval to 30 days. Ensure the cron job interval supports this setup to avoid excessive overlap or missed links.

By following these guidelines, you can ensure that your RSS feed aggregator operates efficiently and effectively without missing or duplicating links.

