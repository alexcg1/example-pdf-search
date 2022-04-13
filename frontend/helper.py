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


class facets:
    gender = ["Men", "Women"]
    season = ["Summer", "Spring", "Fall", "Winter"]
    color = [
        "Beige",
        "Black",
        "Blue",
        "Bronze",
        "Brown",
        "Burgundy",
        "Charcoal",
        "Coffee Brown",
        "Copper",
        "Cream",
        "Fluorescent Green",
        "Gold",
        "Green",
        "Grey",
        "Grey Melange",
        "Khaki",
        "Lavender",
        "Lime Green",
        "Magenta",
        "Maroon",
        "Mauve",
        "Metallic",
        "Multi",
        "Mushroom Brown",
        "Mustard",
        "NA",
        "Navy Blue",
        "Nude",
        "Off White",
        "Olive",
        "Orange",
        "Peach",
        "Pink",
        "Purple",
        "Red",
        "Rose",
        "Rust",
        "Sea Green",
        "Silver",
        "Skin",
        "Steel",
        "Tan",
        "Taupe",
        "Teal",
        "Turquoise Blue",
        "White",
        "Yellow",
    ]
    usage = [
        "",
        "Casual",
        "Ethnic",
        "Formal",
        "Home",
        "NA",
        "Party",
        "Smart Casual",
        "Sports",
        "Travel",
    ]
    masterCategory = [
        "Accessories",
        "Apparel",
        "Footwear",
        "Free Items",
        "Home",
        "Personal Care",
        "Sporting Goods",
    ]
