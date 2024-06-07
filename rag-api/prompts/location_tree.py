from typing import List
from base.logger import log
from entities.article_location import ArticleLocation

class LocationTree:
  def __init__(self, locations: List[ArticleLocation] = None):
    self.locations = locations or []

  def add(self, location: ArticleLocation):
    self.locations.append(location)

  def get_children(self, location: ArticleLocation) -> List[ArticleLocation]:
    return [loc for loc in self.locations if self.is_location_child_of(loc, location)]

  def get_parent(self, location: ArticleLocation) -> ArticleLocation :
    return next((loc for loc in self.locations if self.is_location_parent_of(loc, location)), None)

  def is_location_child_of(self, location: ArticleLocation, parent: ArticleLocation) -> bool:
    loc_type = parent.get_lower_rank_type()
    same_type_value = location[loc_type] == parent[loc_type]
    return location.rank_address > parent.rank_address and same_type_value

  def is_location_parent_of(self, location: ArticleLocation, child: ArticleLocation) -> bool:
    loc_type = location.get_lower_rank_type()
    same_type_value = child[loc_type] == location[loc_type]
    return location.rank_address < child.rank_address and same_type_value

  def log_tree(self):
    formatter = lambda loc: f"{loc.name} - {loc.get_lower_rank_type()} ({loc.rank_address})"
    for location in self.locations:
      children = self.get_children(location)
      parent = self.get_parent(location)
      log(f"Location: {formatter(location)}")
      log(f" > Parent: {formatter(parent)}") if parent else log(" > Parent: None")
      log(f" > Children: count({len(children)})")
      for child in children:
        log(f"   > {formatter(child)}")