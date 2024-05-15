import cProfile
import pstats
from functools import wraps
from io import StringIO
from base.logger import log

def profile_function(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats('cumulative')
    total_calls = ps.total_calls
    total_time = ps.total_tt
    log(f"*** {func.__name__}(): Total time: {total_time:.6f} seconds - Total calls: {total_calls} ***")
    return result
  return wrapper