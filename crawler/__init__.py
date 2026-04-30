from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker
from crawler.writer import Writer

class Crawler(object):
    def __init__(self, config, restart, writer: Writer, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.writer = writer
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier, self.writer)
            for worker_id in range(self.config.threads_count)]
        
        self.writer.start()
        for worker in self.workers:
            worker.start()


    def start(self):
        self.start_async()
        self.join()

    def join(self):
        for worker in self.workers:
            worker.join()

        self.writer.write(None, None, done=True)
        self.writer.join()

        self.logger.info("Closing Frontier database...")
        self.frontier.save.close()