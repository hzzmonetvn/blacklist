#!/usr/bin/env python3
"""
HzzMonet Blacklist Builder
Aggregates, deduplicates, validates, and builds multiple DNS blocklist formats.
Author: hzzmonetvn
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(ROOT_DIR, "sources.txt")
CUSTOM_FILE = os.path.join(ROOT_DIR, "custom.txt")
WHITELIST_FILE = os.path.join(ROOT_DIR, "whitelist.txt")

OUTPUT_BLACKLIST = os.path.join(ROOT_DIR, "blacklist.txt")
OUTPUT_HOSTS = os.path.join(ROOT_DIR, "hosts.txt")
OUTPUT_DOMAINS = os.path.join(ROOT_DIR, "domains.txt")
REWRITES_FILE = os.path.join(ROOT_DIR, "rewrites.txt")
OUTPUT_YT_REWRITE = os.path.join(ROOT_DIR, "youtube-rewrite.txt")
OUTPUT_YT_HOSTS = os.path.join(ROOT_DIR, "youtube-hosts.txt")

# Regex to validate standard domain names
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9-]{2,63}$"
)

IGNORED_DOMAINS = {
    "localhost", "localhost.localdomain", "local", "broadcasthost",
    "ip6-localhost", "ip6-loopback", "ip6-localnet", "ip6-mcastprefix",
    "ip6-allnodes", "ip6-allrouters", "ip6-allhosts", "0.0.0.0", "127.0.0.1"
}

def extract_domain(line: str) -> str:
    """Extract and validate clean domain name from diverse blocklist syntax."""
    line = line.strip()
    if not line or line.startswith(("#", "!", "//", ";")):
        return ""

    # Strip inline comments
    if "#" in line:
        line = line.split("#")[0].strip()
    if "!" in line:
        line = line.split("!")[0].strip()

    # Adblock syntax: ||example.com^ or ||example.com^$third-party
    if line.startswith("||"):
        line = line[2:]
        if "^" in line:
            line = line.split("^")[0]
        elif "$" in line:
            line = line.split("$")[0]

    # Hosts format: 0.0.0.0 example.com or 127.0.0.1 example.com
    parts = line.split()
    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1", "::1", "::"):
        line = parts[1]
    elif len(parts) == 1:
        line = parts[0]
    else:
        return ""

    # Clean leading/trailing dots or hyphens
    domain = line.strip(" .-\r\n\t").lower()

    if not domain or domain in IGNORED_DOMAINS:
        return ""

    # Must contain at least one dot
    if "." not in domain:
        return ""

    if DOMAIN_REGEX.match(domain):
        return domain

    return ""

def load_sources():
    """Load list of upstream URLs from sources.txt."""
    if not os.path.exists(SOURCES_FILE):
        print(f"Warning: {SOURCES_FILE} not found.")
        return []

    sources = []
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sources.append(line)
    return sources

def fetch_url(url: str, timeout: int = 30) -> list:
    """Fetch lines from a single remote URL with retry."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HzzMonet-BlacklistBot/1.0; +https://github.com/hzzmonetvn/blacklist)"
    }
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                lines = raw.splitlines()
                print(f"[OK] Fetched {len(lines)} lines from {url}")
                return lines
        except Exception as e:
            time.sleep(1 + attempt * 2)
            if attempt == 2:
                print(f"[ERROR] Failed to fetch {url}: {e}")
                return []
    return []

def load_whitelist() -> set:
    """Load whitelist domains to protect from blocking."""
    if not os.path.exists(WHITELIST_FILE):
        return set()

    whitelist = set()
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            if line.startswith("@@"):
                line = line[2:]
            domain = extract_domain(line)
            if domain:
                whitelist.add(domain)
    print(f"Loaded {len(whitelist)} whitelist rules.")
    return whitelist

def is_whitelisted(domain: str, whitelist: set) -> bool:
    """Check if domain or its parent domain is whitelisted."""
    if domain in whitelist:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in whitelist:
            return True
    return False

def load_custom_rules() -> set:
    """Load user custom block rules."""
    if not os.path.exists(CUSTOM_FILE):
        return set()

    custom_domains = set()
    with open(CUSTOM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            domain = extract_domain(line)
            if domain:
                custom_domains.add(domain)
    print(f"Loaded {len(custom_domains)} custom block rules.")
    return custom_domains

def build_rewrites(now_utc: str):
    """Process rewrites.txt and generate AdGuard syntax and Hosts format rewrites."""
    if not os.path.exists(REWRITES_FILE):
        return

    rewrites = []
    with open(REWRITES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("#", "!", "//", ";")):
                continue
            if "#" in line:
                line = line.split("#")[0].strip()
            if "!" in line:
                line = line.split("!")[0].strip()

            ip = ""
            domain = ""
            # Adblock syntax: ||domain^$dnsrewrite=IP
            if "$dnsrewrite=" in line:
                m = re.match(r"^\|\|?([^^$]+)\^\$dnsrewrite=([0-9a-fA-F.:]+)$", line)
                if m:
                    domain = m.group(1).strip().lower()
                    ip = m.group(2).strip()
            else:
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0].strip()
                    domain = parts[1].strip().lower()

            if ip and domain:
                if (domain, ip) not in rewrites:
                    rewrites.append((domain, ip))

    if not rewrites:
        return

    # Write AdGuard format (youtube-rewrite.txt)
    with open(OUTPUT_YT_REWRITE, "w", encoding="utf-8") as f:
        f.write("! Title: HzzMonet YouTube Adblock Rewrite (AdGuard syntax)\n")
        f.write("! Description: Routes YouTube traffic to Albania SNI proxy to suppress ads on Smart TV & Mobile\n")
        f.write("! Homepage: https://github.com/hzzmonetvn/blacklist\n")
        f.write("! Author: hzzmonetvn\n")
        f.write(f"! Last Updated: {now_utc}\n")
        f.write(f"! Total Rules: {len(rewrites)}\n")
        f.write("!\n")
        for domain, ip in rewrites:
            f.write(f"||{domain}^$dnsrewrite={ip}\n")
    print(f"[Wrote] {OUTPUT_YT_REWRITE} ({len(rewrites)} rules)")

    # Write Hosts format (youtube-hosts.txt)
    with open(OUTPUT_YT_HOSTS, "w", encoding="utf-8") as f:
        f.write("# Title: HzzMonet YouTube Adblock Rewrite (Hosts syntax)\n")
        f.write("# Description: Routes YouTube traffic to Albania SNI proxy to suppress ads on Smart TV & Mobile\n")
        f.write("# Homepage: https://github.com/hzzmonetvn/blacklist\n")
        f.write("# Author: hzzmonetvn\n")
        f.write(f"# Last Updated: {now_utc}\n")
        f.write(f"# Total Entries: {len(rewrites)}\n")
        f.write("#\n")
        for domain, ip in rewrites:
            f.write(f"{ip} {domain}\n")
    print(f"[Wrote] {OUTPUT_YT_HOSTS} ({len(rewrites)} entries)")

def main():
    start_time = time.time()
    print("=== HzzMonet Blacklist Pipeline Started ===")

    sources = load_sources()
    print(f"Total sources configured: {len(sources)}")

    whitelist = load_whitelist()
    custom_domains = load_custom_rules()

    all_domains = set(custom_domains)

    # Fetch sources concurrently
    if sources:
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_url = {executor.submit(fetch_url, url): url for url in sources}
            for future in as_completed(future_to_url):
                lines = future.result()
                for line in lines:
                    d = extract_domain(line)
                    if d:
                        all_domains.add(d)

    print(f"Total raw unique domains collected: {len(all_domains)}")

    # Filter out whitelisted domains
    if whitelist:
        filtered_domains = {d for d in all_domains if not is_whitelisted(d, whitelist)}
        removed_count = len(all_domains) - len(filtered_domains)
        print(f"Filtered out {removed_count} whitelisted domains.")
        all_domains = filtered_domains

    sorted_domains = sorted(all_domains)
    total_count = len(sorted_domains)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"Final clean unique domains: {total_count}")

    # 1. Output blacklist.txt (Adblock / AdGuard syntax)
    with open(OUTPUT_BLACKLIST, "w", encoding="utf-8") as f:
        f.write("! Title: HzzMonet Blacklist\n")
        f.write("! Description: Unified, cleaned, and deduplicated DNS ad/tracker blocklist\n")
        f.write("! Homepage: https://github.com/hzzmonetvn/blacklist\n")
        f.write("! Author: hzzmonetvn\n")
        f.write(f"! Last Updated: {now_utc}\n")
        f.write(f"! Total Rules: {total_count}\n")
        f.write("!\n")
        for d in sorted_domains:
            f.write(f"||{d}^\n")
    print(f"[Wrote] {OUTPUT_BLACKLIST}")

    # 2. Output hosts.txt (0.0.0.0 format)
    with open(OUTPUT_HOSTS, "w", encoding="utf-8") as f:
        f.write("# Title: HzzMonet Blacklist (Hosts format)\n")
        f.write("# Description: Unified, cleaned, and deduplicated DNS blocklist for hosts/Pi-hole\n")
        f.write("# Homepage: https://github.com/hzzmonetvn/blacklist\n")
        f.write("# Author: hzzmonetvn\n")
        f.write(f"# Last Updated: {now_utc}\n")
        f.write(f"# Total Entries: {total_count}\n")
        f.write("#\n")
        for d in sorted_domains:
            f.write(f"0.0.0.0 {d}\n")
    print(f"[Wrote] {OUTPUT_HOSTS}")

    # 3. Output domains.txt (Plain domain format)
    with open(OUTPUT_DOMAINS, "w", encoding="utf-8") as f:
        f.write("# Title: HzzMonet Blacklist (Plain domains)\n")
        f.write("# Description: Raw unique domain list\n")
        f.write("# Homepage: https://github.com/hzzmonetvn/blacklist\n")
        f.write("# Author: hzzmonetvn\n")
        f.write(f"# Last Updated: {now_utc}\n")
        f.write(f"# Total Domains: {total_count}\n")
        f.write("#\n")
        for d in sorted_domains:
            f.write(f"{d}\n")
    print(f"[Wrote] {OUTPUT_DOMAINS}")

    # 4. Process and output DNS rewrites
    build_rewrites(now_utc)

    elapsed = round(time.time() - start_time, 2)
    print(f"=== Build finished successfully in {elapsed}s ===")

if __name__ == "__main__":
    main()
