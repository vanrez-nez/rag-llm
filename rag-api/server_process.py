import os
import signal
import time
import psutil
from base.logger import log
from base.logger import error
from base.logger import warn
LOCK_FILE = "server.lock"

def find_pid_by_port(port):
  for conn in psutil.net_connections(kind='inet'):
    if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
      return conn.pid
  return None

def wait_for_port_to_be_freed(port, check_interval=1):
  log(f"Waiting for port {port} to be freed...")
  while find_pid_by_port(port) is not None:
    time.sleep(check_interval)
  log(f"Port {port} is now free.")

def kill_previous_instance():
  pid = find_pid_by_port(80)
  log(f'Killing instance with PID: {pid}')
  if not pid:
    return False
  log(f'Killing instance with PID: {pid}')
  try:
    os.kill(pid, signal.SIGTERM)
    wait_for_port_to_be_freed(80)
  except OSError:
    error(f'Process not found PID: {pid}')
    return False
