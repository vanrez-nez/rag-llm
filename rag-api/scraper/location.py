import json

class Location:
  def __init__(self, fields={}) -> None:
    self.id = fields.get('id', '')
    self.title = fields.get('title', '')
    self.description = fields.get('description', '')
    self.name = fields.get('name', '')
    self.aliases = fields.get('aliases', '')
    # location fields
    self.country = fields.get('country', '')
    self.state = fields.get('state', '')
    self.municipality = fields.get('municipality', '')
    self.city = fields.get('city', '')
    self.village = fields.get('village', '')
    self.town = fields.get('town', '')
    self.hamlet = fields.get('hamlet', '')

    # self.capital_of = fields.get('capital_of', '')
    # self.capital_city = fields.get('capital_city', '')
    self.borders = fields.get('borders', '')
    self.lat = fields.get('lat', 0)
    self.lon = fields.get('lon', 0)
    self.eswiki = fields.get('eswiki', '')

  @property
  def is_country(self):
    return self.country != ''

  @property
  def is_state(self):
    return self.state != ''

  @property
  def is_municipality(self):
    return self.municipality != ''

  @property
  def is_city(self):
    return self.city != ''

  @property
  def is_village(self):
    return self.village != ''

  @property
  def is_town(self):
    return self.town != ''

  @property
  def is_hamlet(self):
    return self.hamlet != ''

  @property
  def type(self):
    """maps place flags into type https://wiki.openstreetmap.org/wiki/Key:place"""
    loc_type = ''
    types = {
      "country": [self.is_country],
      "state": [self.is_state],
      "municipality": [self.is_municipality],
      "city": [self.is_city],
      "location": [self.is_village, self.is_town, self.is_hamlet]
    }
    for key, value in types.items():
      if any(value):
        loc_type = key
    return loc_type

  def __str__(self) -> str:
    return json.dumps(self.__dict__)
