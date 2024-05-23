import re
from threading import Timer

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

def fix_punctuation_spaces(text: str) -> str:
  # remove double spaces
  text = re.sub(r'\s+', ' ', text)
  # remove space before punctuation using regex
  text = re.sub(r'\s+([,.])', r'\1', text)
  # trim spaces inside quotes
  text = re.sub(r'[“”‘’]', '"', text)
  text = re.sub(r'"(\s*)(.*?)(\s*)"', r'"\2"', text)
  # trim spaces inside parentheses
  text = re.sub(r'\((\s*)(.*?)(\s*)\)', r'(\2)', text)
  return text.strip()