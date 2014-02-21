from json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):
  """
  JSON encoder that uses an object's __json__() method to convert it to
  something JSON-compatible.
  """
  def default(self, obj):
    try:
      return obj.__json__()
    except AttributeError:
      pass
    return super().default(obj)
