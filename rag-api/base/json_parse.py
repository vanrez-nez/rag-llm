import json
from base.logger import log

def try_parse_json(json_str):
  try:
    json_str_1 = try_extract(json_str, token_start='{', token_end='}')
    json_str_2 = try_extract(json_str, token_start='[', token_end=']')
    result = json_str_1 if len(json_str_1) > len(json_str_2) else json_str_2
    return json.loads(result)
  except json.JSONDecodeError as e:
    log('Error parsing JSON', e)
    return None

def try_extract(input_str, token_start, token_end):
  try:
    json_str = extract_valid_json(input_str, token_start, token_end)
    json.loads(json_str)
    return json_str
  except:
    return ''

# https://github.com/chigwell/JsonExtractor/blob/main/json_extractor/extractor.py
def extract_valid_json(input_str, token_start, token_end):
  stack = []
  start_index = None
  for i, char in enumerate(input_str):
    if char == token_start:
      stack.append(char)
      if len(stack) == 1:
        # Mark the start of a potential JSON object
        start_index = i
    elif char == token_end:
      if stack:
        stack.pop()
        if len(stack) == 0 and start_index is not None:
          # Attempt to parse when we find a closing brace that matches the outermost opening brace
          try:
            return input_str[start_index:i+1]
          except:
            # Reset start_index if parsing fails
            start_index = None
  # If no valid JSON found
  return None