import os

# data directory
DATA_DIR = "../data/images"

# client
TOP_K = 10
IMAGE_RESIZE_FACTOR = 3
DEBUG = True

# serving via REST
SERVER = os.getenv("SERVER", "0.0.0.0")
PORT = 12345
