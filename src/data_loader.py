import os

def get_parameters(filepath):
  filename = os.path.basename(filepath).split(".")[0]
  parameters = filename.split("-")[1:]
  return parameters

print(get_parameters("/home/maximeh/mcd-50-3-3-50-5-2.dat"))