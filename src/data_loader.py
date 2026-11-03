import os

def get_parameters(filepath):
  filename = os.path.basename(filepath).split(".")[0]
  parameters = filename.split("-")[1:]
  return parameters