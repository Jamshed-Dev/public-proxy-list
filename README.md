# Auto Live Proxy Scraper & Verifier

A lightweight, automated python-based tool that scrapes proxies from **ProxyDB**, verifies their connectivity concurrently, and organizes active (live) proxies both into a master list (`ALL.txt`) and into individual country-specific files.

---

## Key Features

- **Automated Scraping**: Scrapes SOCKS5 & High Anonymous proxy lists dynamically from ProxyDB.
- **Concurrent Live Verification**: Uses multi-threading to quickly test each proxy candidate against live endpoints.
- **Master & Categorized Output**: Saves all active proxies in `proxies/ALL.txt` and groups them by country code (e.g., `CN.txt`, `US.txt`, `IN.txt`).
- **Automatic Cleanup**: Re-evaluates previously saved proxies and purges offline/dead nodes automatically.
- **CI/CD Integration**: Pre-configured GitHub Actions workflow runs every 30 minutes to maintain fresh proxy lists.

---

## Directory Structure

```text
├── .github/
│   └── workflows/
│       └── update_proxies.yml    # GitHub Actions Workflow (Runs every 30 minutes)
├── main.py                       # Core Python script for scraping & checking
├── requirements.txt              # Project dependencies
├── .gitignore                    # Prevents generated proxy outputs from tracked commits
└── README.md                     # Project documentation
```

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Local Usage

Run the script manually to scrape and verify live proxies locally:

```bash
python main.py
```

Generated proxies will be output to the `proxies/` directory (created automatically on run).

---

## Automated Workflow (GitHub Actions)

The repository includes a scheduled GitHub Workflow (`.github/workflows/update_proxies.yml`) that runs automatically **every 30 minutes**. You can also trigger it manually from the **Actions** tab on your GitHub repository page.

---

## License

This project is licensed under the [MIT License](LICENSE).
