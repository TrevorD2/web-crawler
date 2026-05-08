import re
import hashlib
from collections import Counter

with open('stopwords.txt', 'r') as file:
    STOP_WORDS = set(map(lambda x: x.strip(), file.readlines()))

def tokenize(txt: str) -> list[str]:
    pattern = r"[A-Za-z0-9](?:[A-Za-z0-9-']*[A-Za-z0-9])?|[A-Za-z0-9]"
    return re.findall(pattern, txt.lower())

def remove_stops(cntr: Counter):
    for word in STOP_WORDS:
        if word in cntr:
            del cntr[word]

def get_counter(txt: str) -> Counter:
    return Counter(tokenize(txt))

def get_hash(token, k):
    return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % (2**k)

def get_fingerprint(txt, k=64) -> int:

    vector = [0 for _ in range(k)]
    cntr = get_counter(txt)
    remove_stops(cntr)

    for token, weight in cntr.items():
        hash = get_hash(token, k)

        for i in range(k):
            bitmask = 1 << i

            if hash & bitmask:
                vector[i] += weight
            else:
                vector[i] -= weight

    fingerprint = 0

    for i in range(k):
        if vector[i] >= 0:
            fingerprint |= (1 << i)

    return fingerprint

def is_duplicate(f1, f2, k=64, T=0.95):
    both = f1 & f2
    cnt = bin(both).count("1")

    return (cnt / k) > T

