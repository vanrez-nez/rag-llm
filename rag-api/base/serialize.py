import inspect
import json

class SerializableDict(dict):
  """
    Inherit from this class to create a serializable dictionary.
    Taking into account the properties of the class.
    Example:
    ```
    class MyClass(SerializableDict):
      def __init__(self, fields):
          # Set fields default
          fields = fields or {}
          # set properties or default values
          self.prop1 = fields.get('prop1', '')
          # call super to initialize the dictionary
          super().__init__(self.__dict__)

      @property
      def name(self):
          return self.get('prop', 'unknown')

    cls = MyClass({
        'prop1': 'value1',
        'prop2': 'value2'
    })
    print(json.dumps(cls))
    ```
  """

  def __getitem__(self, key):
    if hasattr(self.__class__, key) and isinstance(getattr(self.__class__, key), property):
      return getattr(self, key)
    return super().__getitem__(key)

  def __iter__(self):
    for key in super().__iter__():
      yield key
    for name, value in inspect.getmembers(self.__class__, lambda v: isinstance(v, property)):
      yield name

  def items(self):
    for key, value in super().items():
      yield key, value
    for name, value in inspect.getmembers(self.__class__, lambda v: isinstance(v, property)):
      yield name, getattr(self, name)

  def __str__(self) -> str:
    obj_dict = {key: self[key] for key in self}
    return json.dumps(obj_dict, ensure_ascii=False)

  def __repr__(self) -> str:
    return str(self)