from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import requests
import scraper
import time

LARGE_FILE = 20_000_000_000 # 40 MB

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

            try:

                resp = download(tbd_url, self.config, self.logger)

                if resp.raw_response != None and len(resp.raw_response.content) > LARGE_FILE:
                    self.logger.info(f"Downloading large file: {tbd_url} of size {len(resp.raw_response.content)}")

            except requests.exceptions.ConnectionError as e:
                self.logger.info(f"Connection error occured whilst fetching {tbd_url} : {e}")

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            if resp.status == 200:
                text = scraper.text(resp)
                self.writer.write(tbd_url, text)

            scraped_urls = scraper.scraper(tbd_url, resp)

            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
