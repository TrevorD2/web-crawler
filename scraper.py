import re
import time
from urllib.parse import urlparse, urldefrag, urljoin
from utils import get_logger
from bs4 import BeautifulSoup
from collections import Counter

scraper_log = get_logger("Scraper", "Worker")
cache = set()

DENY_STATUS = {404, 500}
MIN_VARIETY = 20
MIN_TOTAL = 30

with open('deny_rules.txt', 'r') as file:
    DENY_RULES = list(map(lambda x: x.strip(), file.readlines()))

with open('deny_urls.txt', 'r') as file:
    DENY_URLS = set(map(lambda x: x.strip(), file.readlines()))

with open('stopwords.txt', 'r') as file:
    STOP_WORDS = set(map(lambda x: x.strip(), file.readlines()))

def scraper(url, resp):
    cache.add(url)

    if resp.status != 200:
        scraper_log.info(f"Error occured whilst scraping {url} : {resp.error}")
        if resp.status in DENY_STATUS: 
            scraper_log.info(f"Failed status check, adding to deny : {url}")
            _add_to_deny(url)
        return []
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    if _check_information_value(soup): 
        scraper_log.info(f"Failed information value check, adding to deny : {url}")
        _add_to_deny(url)

    links = extract_next_links(url, soup)

    return [link for link in links if is_valid(link)]


def extract_next_links(url, soup):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = []

    for link in soup.find_all('a'):
        raw_link = link.get("href")

        full_url = urljoin(url, raw_link)
        clean_url, _ = urldefrag(full_url)

        links.append(clean_url)

    time.sleep(0.5)
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        try:
            parsed = urlparse(url)
        except ValueError: return False
        if parsed.scheme not in set(["http", "https"]):
            return False
        ext = re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        if ext: return False

        if url in DENY_URLS: 
            scraper_log.info(f"Denied via URL: {url}")
            return False

        for rule in DENY_RULES:
            if re.search(rule, url): 
                scraper_log.info(f"Denied via match rule: {url}, url matches {rule}")
                return False

        allowed_domains = [
            r".ics.uci.edu",
            r"|.cs.uci.edu",
            r"|.informatics.uci.edu",
            r"|.stat.uci.edu"
        ]
        return any(domain in parsed.netloc for domain in allowed_domains) and url not in cache

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def text(resp):
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    return soup.get_text()


def _tokenize(txt: str) -> list[str]:
    pattern = r"[A-Za-z0-9](?:[A-Za-z0-9-']*[A-Za-z0-9])?|[A-Za-z0-9]"
    return [tkn for tkn in re.findall(pattern, txt) if tkn not in STOP_WORDS]

def _add_to_deny(rule: str) -> None:
    with open('deny_urls.txt', 'a') as f:
        f.write(rule + '\n')

def _check_information_value(soup):

    text = soup.get_text()

    tkns = _tokenize(text)
    counter = Counter(tkns)

    return len(counter) > MIN_VARIETY and counter.total() > MIN_TOTAL