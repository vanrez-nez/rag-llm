from typing import List
import re
from threading import Timer
from unidecode import unidecode

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

def replace_unicode_escapes(text: str):
  # replace unicode chars with their actual representation
  replacements = {
    "\\u00c1": "Á",
    "\\u00c9": "É",
    "\\u00cd": "Í",
    "\\u00d3": "Ó",
    "\\u00da": "Ú",
    "\\u00dc": "Ü",
    "\\u00e9": "é",
    "\\u00fa": "ú",
    "\\u00f3": "ó",
    "\\u00ed": "í",
    "\\u00e1": "á",
    "\\u00f1": "ñ",
    "\\u00fc": "ü",
    "\\u200b": "",
    "\\u00a0": " ",
    "\\u2019": "'",
    "\\u2018": "'",
    "\\u00b2": ""
  }
  for k, v in replacements.items():
    text = text.replace(k, v)
  return text

def normalize_str(str):
  str = unidecode(str).lower()
  return re.sub(r'[\s,.:;]', '', str)

def str_in_text(str, content) -> int:
  str = normalize_str(str)
  content = normalize_str(content)
  occurrences = re.findall(re.escape(str), content)
  return len(occurrences)

def split_text(text: str, max_length: int) -> List[str]:
  """ Split text into balanced sized chunks when <text> exceeds <max_length> characters """
  sentences = text.split('. ')
  # Calculate the number of chunks needed
  num_chunks = len(text) // max_length + (len(text) % max_length > 0)
  # Calculate the approximate length of each chunk
  approx_chunk_length = len(text) // num_chunks
  chunks = []
  current_chunk = ""
  current_length = 0
  for sentence in sentences:
    sentence_length = len(sentence) + 2  # Account for the dot and space
    if current_length + sentence_length > approx_chunk_length and len(chunks) < num_chunks - 1:
      chunks.append(current_chunk.strip())
      current_chunk = sentence + ". "
      current_length = sentence_length
    else:
      current_chunk += sentence + ". "
      current_length += sentence_length
  # Append the last chunk if it's not empty
  if current_chunk.strip():
    chunks.append(current_chunk.strip())
  return chunks
