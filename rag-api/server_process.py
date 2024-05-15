import os
import signal
import time
from base.logger import log
from base.logger import error
from base.logger import warn
LOCK_FILE = "server.lock"

def create_lock_file(pid: int):
  log(f'Creating new lock file with PID: {pid}')
  with open(LOCK_FILE, 'w') as f:
    f.write(str(pid))

def kill_previous_instance():
  if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, 'r') as f:
      pid = int(f.read().strip())
      log(f'Killing instance with PID: {pid}')
      try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(5)
      except OSError:
        error(f'Process not found PID: {pid}')
        return False
