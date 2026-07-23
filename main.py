import os
import time
import concurrent.futures
import requests
from bs4 import BeautifulSoup

PROXIES_DIR = "proxies"
CHECK_URL = "http://httpbin.org/ip"
TIMEOUT = 6
MAX_PAGES = 75

def get_existing_proxies():
    """Load existing proxies from files in the proxies directory."""
    existing_proxies = []
    if not os.path.exists(PROXIES_DIR):
        return existing_proxies

    for filename in os.listdir(PROXIES_DIR):
        if filename.endswith(".txt") and filename.upper() != "ALL.TXT":
            country = filename.replace(".txt", "")
            file_path = os.path.join(PROXIES_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and ":" in proxy:
                        existing_proxies.append({"proxy": proxy, "country": country})
    return existing_proxies

def get_proxies_from_proxydb():
    """Fetch SOCKS5 & High Anonymous proxies across all pages from ProxyDB."""
    proxies = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Scraping SOCKS5 High Anonymous proxies from ProxyDB (up to {MAX_PAGES} pages)...")
    
    for page in range(MAX_PAGES):
        offset = page * 30
        url = f"https://proxydb.net/?protocol=socks5&anon_lvl=4&offset={offset}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:
                print(f"Rate limited at offset {offset}. Waiting 2 seconds before retrying...")
                time.sleep(2)
                response = requests.get(url, headers=headers, timeout=10)
                
            if response.status_code != 200:
                print(f"Failed to fetch offset {offset}, status: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            if len(rows) <= 1:
                print(f"No more proxies found at page {page + 1}.")
                break
                
            found_on_page = 0
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    ip_elem = cols[0].find('a')
                    port_elem = cols[1].find('a')
                    
                    if ip_elem and port_elem:
                        ip = ip_elem.text.strip()
                        port = port_elem.text.strip()
                        country = cols[3].text.strip() if len(cols) > 3 else "UNKNOWN"
                        
                        if ip and port and port.isdigit():
                            ip_port = f"{ip}:{port}"
                            proxies.append({"proxy": ip_port, "country": country})
                            found_on_page += 1
                            
            if found_on_page == 0:
                break
                
            # Slight sleep between requests to avoid rate limits
            time.sleep(0.3)
                
        except Exception as e:
            print(f"Error scraping offset {offset}: {e}")
            break
            
    print(f"Total raw SOCKS5 High Anonymous candidates scraped: {len(proxies)}")
    return proxies

def check_proxy(proxy_info):
    """Check if a SOCKS5 proxy is live and working."""
    proxy_str = proxy_info["proxy"]
    country = proxy_info["country"]
    
    proxies = {
        "http": f"socks5://{proxy_str}",
        "https": f"socks5://{proxy_str}",
    }
    
    try:
        resp = requests.get(CHECK_URL, proxies=proxies, timeout=TIMEOUT)
        if resp.status_code == 200:
            print(f"[+] LIVE SOCKS5: {proxy_str} ({country})")
            return {"proxy": proxy_str, "country": country, "is_live": True}
    except Exception:
        pass
        
    return {"proxy": proxy_str, "country": country, "is_live": False}

def save_live_proxies(live_proxies):
    """Save live SOCKS5 High Anonymous proxies categorized by country and in ALL.txt."""
    if not os.path.exists(PROXIES_DIR):
        os.makedirs(PROXIES_DIR)
        
    all_live_proxies = set()
    country_map = {}
    
    for item in live_proxies:
        proxy_str = item["proxy"]
        all_live_proxies.add(proxy_str)
        
        country = item["country"].replace(" ", "_").upper()
        if not country:
            country = "UNKNOWN"
        if country not in country_map:
            country_map[country] = set()
        country_map[country].add(proxy_str)
        
    # Save master list (ALL.txt)
    all_file_path = os.path.join(PROXIES_DIR, "ALL.txt")
    sorted_all = sorted(list(all_live_proxies))
    with open(all_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_all) + ("\n" if sorted_all else ""))
    print(f"\n--> Saved {len(sorted_all)} total live SOCKS5 High Anonymous proxies to ALL.txt")

    # Save country-specific files
    for country, proxy_set in country_map.items():
        file_path = os.path.join(PROXIES_DIR, f"{country}.txt")
        proxy_list = sorted(list(proxy_set))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(proxy_list) + "\n")
        print(f"--> Saved {len(proxy_list)} live proxies to {country}.txt")

def main():
    print("1. Loading previously saved proxies...")
    existing = get_existing_proxies()
    print(f"Found {len(existing)} existing proxies to re-verify.")

    print("2. Fetching SOCKS5 & High Anonymous proxies from ProxyDB...")
    new_proxies = get_proxies_from_proxydb()

    # Deduplicate candidate proxies
    all_candidates_dict = {}
    for p in existing + new_proxies:
        all_candidates_dict[p["proxy"]] = p["country"]
    
    candidates = [{"proxy": k, "country": v} for k, v in all_candidates_dict.items()]
    print(f"Total unique SOCKS5 candidates to check: {len(candidates)}")
    
    print("3. Testing SOCKS5 live proxy connectivity in parallel...")
    live_proxies = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_proxy, candidates)
        for res in results:
            if res["is_live"]:
                live_proxies.append(res)
                
    print(f"\nTotal verified live SOCKS5 High Anonymous proxies: {len(live_proxies)}")
    save_live_proxies(live_proxies)

if __name__ == "__main__":
    main()
