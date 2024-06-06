from typing import Tuple
from base.logger import log

class LocationRelation():
  def __init__(self, parent: Tuple = None, child: Tuple = None) -> None:
    self.parent_name = None
    self.child_name = None
    self.parent_type = None
    self.child_type = None
    if parent:
      self.set_parent(parent[0], parent[1])
    if child:
      self.set_child(child[0], child[1])

  def set_parent(self, type: str, name: str) -> None:
    self.parent_name = name
    self.parent_type = type

  def set_child(self, type: str, name: str) -> None:
    self.child_name = name
    self.child_type = type

  def __eq__(self, value: object) -> bool:
    if not isinstance(value, LocationRelation):
      return False
    return str(self) == str(value)

  def __hash__(self) -> int:
    return hash(str(self))

  def __repr__(self) -> str:
    return str(self)

  def __str__(self) -> str:
    c = self.child_name or '?'
    p = self.parent_name or '?'
    return f"{c}, {p}"