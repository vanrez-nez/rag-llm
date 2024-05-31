from base.logger import log
from base.serialize import SerializableDict

class ArticleLocation(SerializableDict):
  def __init__(self, fields: dict = None) -> None:
    fields = fields or {}
    self.place_id = fields.get('place_id', '')
    self.osm_type = fields.get('osm_type', '')
    self.osm_id = fields.get('osm_id', '')
    self.country = fields.get('country', '')
    self.city = fields.get('city', '')
    self.state = fields.get('state', '')
    self.state_district = fields.get('state_district', '')
    self.county = fields.get('county', '')
    self.town = fields.get('town', '')
    self.village = fields.get('village', '')
    self.rank_address = fields.get('rank_address', '')
    self.lat = fields.get('lat', '')
    self.lon = fields.get('lon', '')
    super().__init__(self.__dict__)

  @property
  def id(self) -> str:
    """
      place_id is nominatim's unique identifier for a location but can't be used externally as it changes each time
      database is rebuilt. Instead we use osm_type and osm_id for form a unique id. osm_id cannot be used alone
      as it is not unique across osm_types.
    """
    return f"{self.osm_type}-{self.osm_id}"