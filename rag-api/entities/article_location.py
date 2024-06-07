from base.logger import log
from base.serialize import SerializableDict
from providers.overpass_provider import all_rank_place_types

ALL_TYPES_BY_RANK = all_rank_place_types(reversed=True)

class ArticleLocation(SerializableDict):
  def __init__(self, fields: dict = None) -> None:
    fields = fields or {}
    self.place_id = fields.get('place_id', '')
    self.osm_type = fields.get('osm_type', '')
    self.osm_id = fields.get('osm_id', '')
    self.continent = fields.get('continent', '')

    self.country = fields.get('country', '')
    self.state = fields.get('state', '')
    self.region = fields.get('region', '')
    self.province = fields.get('province', '')
    self.county = fields.get('county', '')
    self.city = fields.get('city', '')
    self.municipality = fields.get('municipality', '')
    self.island = fields.get('island', '')
    self.town = fields.get('town', '')
    self.borough = fields.get('borough', '')
    self.village = fields.get('village', '')
    self.suburb = fields.get('suburb', '')
    self.hamlet = fields.get('hamlet', '')
    self.rank_address = fields.get('rank_address', '')
    self.lat = fields.get('lat', '')
    self.lon = fields.get('lon', '')
    super().__init__(self.__dict__)

  def get_lower_rank_type(self) -> str:
    for type in ALL_TYPES_BY_RANK:
      if getattr(self, type, None):
        return type

  @property
  def name(self) -> str:
    # try get the most specific name using ALL_TYPES_BY_RANK
    for place in ALL_TYPES_BY_RANK:
      name = getattr(self, place, None)
      if name:
        return name

  @property
  def id(self) -> str:
    """
      place_id is nominatim's unique identifier for a location but can't be used externally as it changes each time
      database is rebuilt. Instead we use osm_type and osm_id for form a unique id. osm_id cannot be used alone
      as it is not unique across osm_types.
    """
    t = self.osm_type[0].upper() if self.osm_type else ''
    return f"{t}{self.osm_id}"