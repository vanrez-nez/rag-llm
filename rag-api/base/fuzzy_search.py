from typing import Any
from thefuzz import fuzz
from thefuzz import process
from base.logger import debug

class FuzzySearch:
  def __init__(self, config = {}) -> None:
    self.collections = {}
    self.config = config

  def add(self, type: str, items: list[str]):
      self.collections[type] = items

  def search(self, keyword: str, min_score: int = 99) -> Any:
    types = self.collections.keys()
    results = []
    for c_type in types:
      match = process.extractOne(keyword, self.collections[c_type])
      if not match:
        continue
      score = int(match[1] or 0)
      if match[0].startswith(keyword):
        score = 100
      if match and score >= min_score:
        debug(f"Match: {match[0]} with {match[1]} for {keyword}")
        results.append({
          'type': c_type,
          'value': match[0]
        })
    return results