from config import (
    SERVER,
    PORT,
    TOP_K,
)
from jina import Client, Document
import yaml

CONFIG_FILE = "../config.yml"

with open(CONFIG_FILE) as file:
    config = yaml.safe_load(file.read())


def get_matches(
    input,
    server=config["host"],
    port=config["port"],
    limit=config["return_docs"],
    filters=None,
):
    client = Client(host=server, port=port)
    response = client.search(
        Document(text=input),
        return_results=True,
        parameters={"limit": limit, "filter": filters},
        show_progress=True,
    )

    return response[0].matches


def get_matches_from_image(
    input,
    server=config["host"],
    port=config["port"],
    limit=config["return_docs"],
    filters=None,
):
    data = input.read()
    query_doc = Document(blob=data)
    query_doc.convert_blob_to_image_tensor()
    query_doc.set_image_tensor_shape((80, 60))

    client = Client(host=server, protocol="http", port=port)
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


# def filename_to_title(filename: str) -> str:
    # title = filename.split("/")[-1]
    # title = title.split(".")[0]
