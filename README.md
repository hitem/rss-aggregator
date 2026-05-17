# RSS Aggregator

A simple GitHub Actions RSS/HTML feed aggregator.

It runs on a schedule, collects new items, writes them to `aggregated_feed.xml`, tracks already used links in `processed_links.txt`, and publishes the result with GitHub Pages.

`hitem`

---

## What this is for

Use this when you want to turn one or more RSS/HTML sources into a single feed that can be used by:

- RSS readers
- Microsoft Teams RSS connectors
- Power Automate flows
- Feedly or similar feed tools
- Any tool that can poll an RSS/XML feed
  

> **Recommended:** Use `rss_aggregator.py` as the default option.  
> `html_aggregator.py` is a fallback parser for sources that do not provide a usable RSS feed.

The generated feed URL will look like this:

```text
https://<username>.github.io/<repo-name>/aggregated_feed.xml
```

Example:

```text
https://hitem.github.io/rss-aggregator/aggregated_feed.xml
```

---

## Files used

| File | Purpose |
|---|---|
| `rss_aggregator.py` | Aggregates RSS feeds |
| `html_aggregator.py` | Aggregates HTML sources |
| `aggregated_feed.xml` | The generated RSS/XML feed |
| `processed_links.txt` | Tracks links that have already been processed |
| `.github/workflows/rss_aggregator.yml` | Runs the aggregator and deploys GitHub Pages |
| `requirements.txt` | Python dependencies |

---

## Setup guide

### 1. Create a GitHub repository

Create a new public GitHub repository, for example:

```text
rss-aggregator
```

Upload the project files to the repository.

---

### 2. Enable GitHub Pages

Go to:

```text
Repository -> Settings -> Pages
```

Set:

```text
Build and deployment -> Source -> GitHub Actions
```

This lets the workflow deploy the generated feed to GitHub Pages.

Your Pages site will be:

```text
https://<username>.github.io/<repo-name>/
```

Your feed URL will be:

```text
https://<username>.github.io/<repo-name>/aggregated_feed.xml
```

---

### 3. Update the feed link in the script

Open either `rss_aggregator.py` or `html_aggregator.py`.

Find the `link` field:

```python
etree.SubElement(channel, "link").text = "https://<username>.github.io/<repo name>/aggregated_feed.xml"
```

Replace it with your real feed URL.

Example:

```python
etree.SubElement(channel, "link").text = "https://hitem.github.io/rss-aggregator/aggregated_feed.xml"
```

---

### 4. Choose RSS or HTML aggregation

Open:

```text
.github/workflows/rss_aggregator.yml
```

For RSS feeds, use:

```yaml
- name: Run RSS aggregator script
  run: python rss_aggregator.py
```

For HTML sources, use:

```yaml
- name: Run HTML aggregator script
  run: python html_aggregator.py
```

---

### 5. Choose feed mode

Open `rss_aggregator.py` or `html_aggregator.py`.

#### Aggregate mode

Use this when your external tool reads the whole feed each time.

```python
append_mode = False
```

Good for tools where the ingestion is triggered elsewhere and reads the full `aggregated_feed.xml`.

#### Append mode

Use this when your external tool checks for newly added RSS items.

```python
append_mode = True
max_age_days = 365
```

Good for Feedly, Teams, Power Automate, or other tools that look for new RSS entries.

`max_age_days` controls how long items stay in `aggregated_feed.xml`.

---

### 6. Run the workflow

Go to:

```text
Repository -> Actions -> RSS & HTML Aggregator -> Run workflow
```

After the run completes, open:

```text
https://<username>.github.io/<repo-name>/aggregated_feed.xml
```

You should see the generated XML feed.

---

## Use the feed in other tools

Use this URL:

```text
https://<username>.github.io/<repo-name>/aggregated_feed.xml
```

### Microsoft Teams example

![image](https://github.com/hitem/rss-aggregator/assets/8977898/cb0fbc33-57a7-4012-8cf7-4f9d36a3c1e0)

### Power Automate example

![image](https://github.com/user-attachments/assets/6752ac0c-a4c9-4e63-8d83-6214b8710d47)

### Power Automate with `append_mode = True`

<img width="800" height="220" alt="append_mode_true" src="https://github.com/user-attachments/assets/dda7bc59-53a0-499b-9314-c1f99b986e67" />

---

## GitHub Actions permissions

The workflow needs permission to commit updated files and deploy GitHub Pages.

The workflow should include:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

If commits or deployment fail, check:

```text
Repository -> Settings -> Actions -> General -> Workflow permissions
```

Make sure GitHub Actions has write access.

More info:

```text
https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#setting-the-permissions-of-the-github_token-for-your-repository
```

Use as few permissions as possible for your project.

---

## Timing and frequency

Timing has three parts:

| Setting | Where | Purpose |
|---|---|---|
| `time_threshold` | `rss_aggregator.py` or `html_aggregator.py` | How far back the script looks for items |
| Cron schedule | `.github/workflows/rss_aggregator.yml` | How often GitHub Actions runs |
| Ingestion frequency | Your RSS reader / Teams / Power Automate flow | How often the external tool checks the feed |

### Default hourly setup

In the Python script:

```python
time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
```

In the workflow:

```yaml
schedule:
  - cron: "37 * * * *"
```

Recommended external ingestion frequency: (if `append_mode = false`)

```text
1 hour
```

The collection window should overlap the workflow and ingestion interval so you do not miss items.

### Monthly-style setup

Example:

```text
time_threshold: 60 days
Cron job interval: 30 days
Ingestion frequency: 30 days
```

Note: with `append_mode = False`, the first run can collect a large window of items.

With `append_mode = True`, the feed only appends items found inside the configured script window, so it will not dump a large historical backlog on the first run.

---

## Avoid noisy GitHub notifications

If you fork or watch this repository and run the workflow often, GitHub notifications can become noisy.

For your own sanity, adjust your notification settings:

<img src="https://github.com/user-attachments/assets/e453e278-d324-45b1-9d76-f21b6c110a57" width="300"/>

If you run the workflow every hour with `append_mode = false`, it can get very chatty.
