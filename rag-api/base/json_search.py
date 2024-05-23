from typing import Any
import json
from jmespath import search, visitor

class JSONSearch:
  def __init__(self, data: bytes|str, options: visitor.Options = None):
    self.json_data = json.loads(data)
    self.options = options

  def search(self, expression: str) -> Any:
    return search(expression, self.json_data, self.options)