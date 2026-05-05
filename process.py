import re
import json
from processing_utils import get_counter, remove_stops, is_duplicate
from urllib.parse import urlparse
from collections import Counter

"""
- I should note that it is possible to combine all of the following functions into one pass through data.jsonl.
- This was my original approach, but the result was highly messy and unreadible.
- Due to the relatively small compute time of the processing compared to the crawling, I decided to sacrifice efficiency
for the sake of readibility.
"""
def get_num_urls() -> int:
    urlcnt = 0

    with open("data.jsonl", 'r', encoding='utf-8') as f:
        for entry in f:
            urlcnt += 1

    return urlcnt

def get_longest() -> tuple[str, int]:
    longest = ""
    longest_cnt = 0

    with open("data.jsonl", 'r', encoding='utf-8') as f:
        for entry in f:
            page = json.loads(entry)
            url = page["url"]
            content = page["content"]

            counter = get_counter(content)

            if counter.total() > longest_cnt:
                longest = url
                longest_cnt = counter.total()

    return longest, longest_cnt

def most_common() -> list[tuple[str, int]]:
    total_cnt = Counter()
    fingerprints = {}

    with open("data.jsonl", 'r', encoding='utf-8') as f:
        for entry in f:

            page = json.loads(entry)
            url = page["url"]
            content = page["content"]
            current_print = page["fingerprint"]

            if dup:=_check_duplication(fingerprints, current_print, debug_mode=True):
                print(f"DUPLICATE FOUND: {url} matches {dup}")
                continue # This page is a duplicate, don't count it towards most common words

            _add_to_fingerprints(fingerprints, current_print, url=url)

            counter = get_counter(content)

            remove_stops(counter)

            total_cnt += counter

    return total_cnt.most_common(50)

def subdomains() -> dict[str, int]:
    subdomains = {}
    fingerprints = {}

    with open("data.jsonl", 'r', encoding='utf-8') as f:
        for entry in f:
            page = json.loads(entry)
            url = page["url"]
            current_print = page["fingerprint"]

            if dup:=_check_duplication(fingerprints, current_print, debug_mode=True):
                print(f"DUPLICATE FOUND: {url} matches {dup}")
                continue # This page is a duplicate, don't count it towards subdomain count

            _add_to_fingerprints(fingerprints, current_print, url=url)

            domain = urlparse(url).netloc

            if "uci.edu" not in domain:
                raise ValueError("SOMETHING IS WRONG")
            
            if not (domain in subdomains):
                subdomains[domain] = 0

            subdomains[domain] += 1

    return subdomains

def main():        
    print("Total URLS:", get_num_urls())
    print("Longest Page:", get_longest())
    print("---Most common words---")

    for word, cnt in most_common():
        print(word, cnt)

    print("---Subdomains---")
    for sub, cnt in sorted(subdomains().items(), key=lambda x: x[0]):
        print(sub, cnt)

def _split_print(fingerprint: int):
    chunk_size = 16 
    mask = (1 << chunk_size) - 1 # 0xFFFF
    prints = []

    for i in range(4):
        # Shift the fingerprint down, then mask the bottom 16 bits
        # This ensures the chunk is a value between 0 and 65535
        current_print = (fingerprint >> (i * chunk_size)) & mask
        prints.append(current_print)

    return prints


def _add_to_fingerprints(fingerprints: dict, current_print: int, url=None):
    prints = _split_print(current_print)

    for subprint in prints:
        if not (subprint in fingerprints):
            fingerprints[subprint] = []

        fingerprints[subprint].append(current_print if url == None else (current_print, url))

def _check_duplication(fingerprints: dict, current_print, debug_mode=False):
    prints = _split_print(current_print)

    for subprint in prints:
        if subprint in fingerprints:
            for other_print in fingerprints[subprint]:
                if is_duplicate(other_print if not debug_mode else other_print[0], current_print):
                    return other_print
                
    return False

if __name__ == '__main__':
    main()