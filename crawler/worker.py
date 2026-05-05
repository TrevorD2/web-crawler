from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import requests
import scraper
from processing_utils import get_fingerprint
import time

class Worker(Thread):
    def __init__(self, worker_id, config, frontier, writer):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.writer = writer

        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            print(tbd_url)

            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            resp = None
            try:
                resp = download(tbd_url, self.config, self.logger)

                self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")

                if resp and is_parseable(resp):
                    text = scraper.text(resp)
                    fingerprint = get_fingerprint(text)
                    
                    self.writer.write(tbd_url, text, fingerprint)

                    scraped_urls = scraper.scraper(tbd_url, resp)

                    for scraped_url in scraped_urls:
                        self.frontier.add_url(scraped_url)
                else:
                    status = resp.status if resp else "No Response"
                    self.logger.info(f"Skipping non-parseable or error page: {tbd_url} with status: {status}")
                    scraper.add_to_deny(tbd_url)

            except requests.exceptions.ConnectionError as e:
                self.logger.info(f"Connection error occured whilst fetching {tbd_url} : {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing {tbd_url}: {e}")
            finally:
                self.frontier.mark_url_complete(tbd_url)


def is_parseable(resp):
    if resp.status != 200:
        return False
        
    content_type = resp.raw_response.headers.get("Content-Type", "").lower()
    
    if "text/html" not in content_type:
        return False
        
    size = int(resp.raw_response.headers.get("Content-Length", 0))
    if size > 10 * 1024 * 1024: # 10 MB
        return False
        
    return True