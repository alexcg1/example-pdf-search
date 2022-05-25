import click
from docarray import DocumentArray, Document
from executors import (
    PdfPreprocessor,
    ChunkSentencizer,
    DebugChunkPrinter,
    RecurseTags,
    ChunkMerger,
    ImageNormalizer,
    EmptyDeleter,
)
from jina import Flow
from helper import load_config

# CONFIG_FILE = "config.yml"

# with open(CONFIG_FILE) as file:
# config = yaml.safe_load(file.read())

config = load_config()


# Hopefully this is an all-in-one Flow, since indexing and querying follow different rules. This doesn't work fwiw

# flow = (
# Flow(port=PORT, protocol="http")
# .add(uses=PdfPreprocessor, name="processor", uses_requests={"/index": "index"})
# .add(
# uses="jinahub://PDFSegmenter",
# install_requirements=True,
# name="segmenter",
# uses_requests={"/index": "index"},
# )
# .add(
# uses=ChunkSentencizer,
# name="chunk_sentencizer",
# uses_requests={"/index": "index"},
# )
# .add(
# uses=RecurseTags, uses_requests={"/index": "index"}
# )  # add doc.tags to chunk.tags
# .add(uses=ChunkMerger, uses_requests={"/index": "index"})  # flatten chunks
# .add(
# uses="jinahub://CLIPEncoder",
# install_requirements=True,
# name="encoder",
# uses_with={
# "traversal_paths": "@c"
# },  # on index we go on chunk-level not doc-level
# uses_requests={"/index": "index"},
# )
# .add(
# uses="jinahub://CLIPEncoder",
# install_requirements=True,
# name="encoder",
# uses_requests={"/search": "search"},
# )
# .add(
# uses="jinahub://SimpleIndexer/v0.15",
# install_requirements=True,
# name="indexer",
# uses_with={"traversal_right": "@c"},
# )
# )


def index(directory=config["data_dir"], num_docs=config["num_docs"]):
    docs = DocumentArray.from_files(f"{directory}/*.pdf", recursive=True, size=num_docs)

    flow = (
        Flow(port=config["port"], protocol="http")
        .add(uses=PdfPreprocessor, name="processor")
        .add(uses="jinahub://PDFSegmenter", install_requirements=True)
        .add(uses=ChunkSentencizer, name="chunk_sentencizer")
        .add(uses=ChunkMerger, name="chunk_merger")  # flatten chunks
        # .add(uses=ImageNormalizer, name="image_normalizer")
        .add(uses=RecurseTags, name="recurse_tags")  # add doc.tags to chunk.tags
        .add(
            uses="jinahub://SpacyTextEncoder",
            # uses="jinahub://CLIPEncoder",
            install_requirements=True,
            name="encoder",
            uses_with={"model_name": "en_core_web_md", "traversal_paths": "@c"},
        )
        .add(uses=EmptyDeleter, name="empty_deleter")
        .add(
            uses="jinahub://SimpleIndexer/v0.15",
            install_requirements=True,
            name="indexer",
            # uses_with={"traversal_right": "@c"},
        )
    )

    with flow:
        indexed_docs = flow.index(docs, show_progress=True, size=1)

    indexed_docs.summary()
    indexed_docs[0].chunks.summary()

    # for doc in indexed_docs[0].chunks:
        # print(len(doc.text))

    return indexed_docs


def search_grpc():
    flow = (
        Flow()
        .add(
            # uses="jinahub://CLIPEncoder",
            uses="jinahub://SpacyTextEncoder",
            uses_with={"model_name": "en_core_web_md"},
            install_requirements=True,
            name="encoder",
        )
        .add(
            uses="jinahub://SimpleIndexer/latest",
            install_requirements=True,
            name="indexer",
            uses_with={"traversal_right": "@c"},
        )
    )
    print("Type 'q' to quit!")
    while True:
        string = input("What do you want to search for? ")
        if string.lower() in ["q", "quit"]:
            print("Goodbye!")
            break

        search_doc = Document(text=string)

        with flow:
            output = flow.search(search_doc)

        print(output)
        matches = output[0].matches

        for doc in matches:
            print(doc.content)
            print(doc.tags)
            print("-" * 10)


def search():
    flow = (
        Flow(protocol="http", port=config["port"])
        .add(
            uses="jinahub://CLIPEncoder",
            install_requirements=True,
            name="encoder",
        )
        .add(
            uses="jinahub://SimpleIndexer/latest",
            install_requirements=True,
            name="indexer",
            uses_with={"traversal_right": "@c"},
        )
    )
    with flow:
        flow.block()


@click.command()
@click.option(
    "--task",
    "-t",
    type=click.Choice(["index", "search", "search_grpc"], case_sensitive=False),
)
@click.option("--num_docs", "-n", default=config["num_docs"])
def main(task: str, num_docs):
    if task == "index":
        index(num_docs=num_docs)
    elif task == "search":
        search()
    elif task == "search_grpc":
        search_grpc()
    else:
        print("Please add '-t index' or '-t search' to your command")


if __name__ == "__main__":
    main()
