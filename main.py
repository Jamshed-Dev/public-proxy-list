import os
import concurrent.futures
import requests
from bs4 import BeautifulSoup

PROXIES_DIR = "proxies"
CHECK_URL = "http://httpbin.org/ip"
TIMEOUT = 5

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
    """Fetch raw proxy IP:Port and country info from ProxyDB."""
    proxies = []
    url = "https://proxydb.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
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
    except Exception as e:
        print(f"Error scraping proxies: {e}")
        
    return proxies

def check_proxy(proxy_info):
    """Check if a proxy is actively responding (live)."""
    proxy_str = proxy_info["proxy"]
    country = proxy_info["country"]
    
    proxies = {
        "http": f"http://{proxy_str}",
        "https": f"http://{proxy_str}",
    }
    
    try:
        resp = requests.get(CHECK_URL, proxies=proxies, timeout=TIMEOUT)
        if resp.status_code == 200:
            print(f"[+] LIVE: {proxy_str} ({country})")
            return {"proxy": proxy_str, "country": country, "is_live": True}
    except Exception:
        pass
    
    print(f"[-] DEAD: {proxy_str} ({country})")
    return {"proxy": proxy_str, "country": country, "is_live": False}

def save_live_proxies(live_proxies):
    """Save live proxies categorized by country as well as an ALL.txt master list."""
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
        
    # Save master file containing ALL live proxies from all countries
    all_file_path = os.path.join(PROXIES_DIR, "ALL.txt")
    sorted_all = sorted(list(all_live_proxies))
    with open(all_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_all) + ("\n" if sorted_all else ""))
    print(f"--> Saved {len(sorted_all)} total live proxies to ALL.txt")

    # Save per-country files
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

    print("2. Fetching new proxies from ProxyDB...")
    new_proxies = get_proxies_from_proxydb()
    print(f"Fetched {len(new_proxies)} new proxies.")

    # Combine and deduplicate candidates
    all_candidates_dict = {}
    for p in existing + new_proxies:
        all_candidates_dict[p["proxy"]] = p["country"]
    
    candidates = [{"proxy": k, "country": v} for k, v in all_candidates_dict.items()]
    print(f"Total unique candidates to check: {len(candidates)}")
    
    print("3. Checking proxy live status...")
    live_proxies = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(check_proxy, candidates)
        for res in results:
            if res["is_live"]:
                live_proxies.append(res)
                
    print(f"\nTotal verified live proxies: {len(live_proxies)}")
    save_live_proxies(live_proxies)

if __name__ == "__main__":
    main()
