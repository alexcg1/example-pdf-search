# from config import (
# SERVER,
# PORT,
# TOP_K,
# )
from jina import Client, Document
import yaml
import os
from pprint import pprint

# CONFIG_FILE = "../config.yml"

# with open(CONFIG_FILE) as file:
# config = yaml.safe_load(file.read())


def load_config():
    """
    Loads config from docker-compose variables or file in project root folder (i.e. folder above backend/frontend)
    """
    try:
        config = {
            "data_dir": os.getenv("DATA_DIR", "data"),
            "metadata_dir": os.getenv("METADATA_DIR", "data/metadata"),
            "port": int(os.getenv("PORT", 5689)),
            "num_docs": int(os.getenv("NUM_DOCS", 1000)),
            "return_docs": int(os.getenv("RETURN_DOCS", 10)),
            "host": os.getenv("HOST", "0.0.0.0"),
            "server": os.getenv("SERVER", "0.0.0.0"),
            "protocol": os.getenv("PROTOCOL", "http"),
            "debug": os.getenv("DEBUG", True),
        }
    except:
        CONFIG_FILE = "config.yml"
        with open(CONFIG_FILE) as file:
            config = yaml.safe_load(file.read())

    print("Frontend config")
    pprint(config)
    return config


config = load_config()


def get_matches(
    string,
    host=config["host"],
    port=config["port"],
    protocol=config["protocol"],
    limit=config["return_docs"],
    filters=None,
):
    client = Client(host=host, port=port, protocol=protocol)
    response = client.search(
        Document(text=string),
        return_results=True,
        parameters={"limit": limit, "filter": filters},
        show_progress=True,
    )

    return response[0].matches


# def get_matches(
    # input,
    # server=config["server"],
    # port=config["port"],
    # limit=config["return_docs"],
    # filters=None,
# ):
    # client = Client(host=server, protocol="http", port=port)
    # response = client.search(
        # Document(text=input),
        # return_results=True,
        # # parameters={"limit": limit, "filter": filters},
        # show_progress=True,
    # )

    # return response[0].matches


def get_matches_from_image(
    input_data,
    host=config["host"],
    port=config["port"],
    protocol=config["protocol"],
    limit=config["return_docs"],
    filters=None,
):
    data = input_data.read()
    query_doc = Document(blob=data)
    query_doc.convert_blob_to_image_tensor()
    query_doc.set_image_tensor_shape((64, 64))

    client = Client(host=host, protocol=protocol, port=port)
    response = client.search(
        query_doc,
        return_results=True,
        parameters={"limit": limit, "filter": filters},
    )

    return response[0].matches


def resize_image(filename, resize_factor=2):
    from PIL import Image

    image = Image.open(filename)
    w, h = image.size
    image = image.resize((w * resize_factor, h * resize_factor), Image.ANTIALIAS)

    return image
