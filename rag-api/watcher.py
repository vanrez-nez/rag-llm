import subprocess
import time
import os
import threading
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from base.utils import debounce
from base.logger import log

observer = None

def run():
    log("Starting process...")
    subprocess.run(["poetry", "run", "python", "index.py"])

@debounce(1)
def spawn_thread():
    thread = threading.Thread(target=run)
    thread.start()

def on_change(event):
    log(f"{event.event_type} - {event.src_path}")
    spawn_thread()

def get_event_handler():
    patterns = ["*.py"]
    event_handler = PatternMatchingEventHandler(patterns)
    event_handler.on_modified = on_change
    return event_handler

def start_observer():
    global observer
    event_handler = get_event_handler()
    observer = Observer()
    observer.schedule(event_handler, '.', recursive=True)
    observer.start()
    log("Watching for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_observer()

def stop_observer():
    global observer
    log("Exiting from watcher...")
    if observer is not None:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    log("Starting watcher...")
    spawn_thread()
    start_observer()
