import json

class ArticleLocation:
  def __init__(self, fields = {}) -> None:
    self.place_id = fields.get('place_id', '')
    self.osm_type = fields.get('osm_type', '')
    self.osm_id = fields.get('osm_id', '')
    self.country = fields.get('country', '')
    self.city = fields.get('city', '')
    self.state = fields.get('state', '')
    self.state_district = fields.get('state_district', '')
    self.county = fields.get('county', '')
    self.town = fields.get('town', '')
    self.rank_address = fields.get('rank_address', '')
    self.lat = fields.get('lat', '')
    self.lon = fields.get('lon', '')

  @property
  def id(self):
    """
      place_id is nominatim's unique identifier for a location but can't be used externally as it changes each time
      database is rebuilt. Instead we use osm_type and osm_id for form a unique id. osm_id cannot be used alone
      as it is not unique across osm_types.
    """
    return f"{self.osm_type}-{self.osm_id}"

  def __str__(self) -> str:
    return json.dumps(self.__dict__)