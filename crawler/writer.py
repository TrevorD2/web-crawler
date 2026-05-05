from threading import Thread
import queue
import json

class Writer(Thread):
    def __init__(self, filename):
        super().__init__(daemon=True)
        self.file = open(filename, "a", encoding="utf-8")
        self.queue = queue.Queue(maxsize=1000)


    def run(self):
        try:
            while True:
                item = self.queue.get()
                
                if item is None:
                    self.queue.task_done()
                    break
                
                try:
                    self.file.write(json.dumps(item) + "\n")
                    self.file.flush()

                except Exception as e:
                    print(f"Write Error: {e}")
                finally:
                    self.queue.task_done()
        finally:
            self.close()

    def write(self, url, text, fingerprint, done=False):
        if done:
            self.queue.put(None)
            return
        self.queue.put({"url": url, "content": text, "fingerprint": fingerprint})

    def close(self):
        self.file.close()