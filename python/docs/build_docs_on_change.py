import asyncore
import time
import os
import pyinotify
import subprocess


class EventHandler(pyinotify.ProcessEvent):
    """Mini event handler for pyinotify events"""
    def __init__(self):
        self.build_path = os.path.abspath("./build/html/index.html")

        self.devnull = open(os.devnull, "wb")
        self.silence_output = {
            "stdout": self.devnull,
            "stderr": self.devnull
        }

    def __del__(self):
        self.devnull.close()

    def curr_time(self):
        return time.strftime("%H:%M:%S", time.gmtime())

    def process_IN_MODIFY(self, event):
        print("[%s] Modified: %s" % (self.curr_time(), event.pathname))

        build = subprocess.call(["make", "clean", "html"],
                                **self.silence_output)
        if build == 0:
            print("[%s] Build success." % (self.curr_time()))
            subprocess.call(["sensible-browser", self.build_path],
                            **self.silence_output)
        else:
            print("[%s] Build failed (exit: %d)" % (self.curr_time(), build))

        print("")  # Blank line

if __name__ == "__main__":
    wm = pyinotify.WatchManager()
    notifier = pyinotify.AsyncNotifier(wm, EventHandler())

    # Watch directory for modifications
    mask = pyinotify.IN_MODIFY
    path = os.path.abspath("./source")
    wdd = wm.add_watch(path, mask, rec=True)

    asyncore.loop()
