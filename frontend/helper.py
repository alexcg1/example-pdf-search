import os
from jina import Client, Document
import yaml


def load_config():
    """
    Loads config from docker-compose variables or file in project root folder (i.e. folder above backend/frontend)
    """
    CONFIG_FILE = "config.yml"
    with open(CONFIG_FILE) as file:
        default_config = yaml.safe_load(file.read())

    config = {
        "data_dir": os.getenv("DATA_DIR", default_config["data_dir"]),
        "metadata_dir": os.getenv("METADATA_DIR", default_config["metadata_dir"]),
        "num_docs": int(os.getenv("NUM_DOCS", default_config["num_docs"])),
        "return_docs": int(os.getenv("RETURN_DOCS", default_config["return_docs"])),
        "host": os.getenv("HOST", default_config["host"]),
        "debug": os.getenv("DEBUG", default_config["debug"]),
        "port": int(os.getenv("PORT", default_config["port"])),
    }

    # protocol, server, port = config["host"].split(":")
    # port = int(port)
    # config["host"] = f"{protocol}:{server}:{port}"

    return config


config = load_config()


def get_matches(
    string,
    host=config["host"],
    port=config["port"],
    # protocol="http"
    limit=config["return_docs"],
    filters=None,
):
    client = Client(host=host, port=port)
    response = client.search(
        Document(text=string),
        return_results=True,
        parameters={"limit": limit, "filter": filters},
        show_progress=True,
    )

    return response[0].matches


def get_matches_from_image(
    input_data,
    host=config["host"],
    port=config["port"],
    # protocol=config["protocol"],
    limit=config["return_docs"],
    filters=None,
):
    data = input_data.read()
    query_doc = Document(blob=data)
    query_doc.convert_blob_to_image_tensor()
    query_doc.set_image_tensor_shape((64, 64))

    client = Client(host=host, port=port)
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
