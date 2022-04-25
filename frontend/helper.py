from config import (
    SERVER,
    PORT,
    TOP_K,
)
from jina import Client, Document


def get_matches(
    input, server=SERVER, port=PORT, limit=TOP_K, filters=None
):
    client = Client(host=server, protocol="http", port=port)
    response = client.search(
        Document(text=input),
        return_results=True,
        parameters={"limit": limit, "filter": filters},
        show_progress=True,
    )

    return response[0].matches


def get_matches_from_image(
    input, server=SERVER, port=PORT, limit=TOP_K, filters=None
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
        show_progress=True,
    )

    return response[0].matches


def print_stars(rating, maximum=5):
    rating = int(rating)
    positive = "★"
    negative = "☆"

    string = rating * positive + (maximum - rating) * negative

    return string


def resize_image(filename, resize_factor=2):
    from PIL import Image

    image = Image.open(filename)
    w, h = image.size
    image = image.resize((w * resize_factor, h * resize_factor), Image.ANTIALIAS)

    return image

def filename_to_title(filename: str) -> str:
    title = filename.split("/")[-1]
    title = title.split(".")[0]
