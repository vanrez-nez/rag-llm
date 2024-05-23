def build_prompt(*args, **kwargs):
  string_args = [str(value) for value in kwargs.values() if isinstance(value, str)]
  gen_args = [str(arg) for arg in args if isinstance(arg, str)]
  return " ".join(string_args + gen_args)