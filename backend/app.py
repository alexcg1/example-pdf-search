import click
from docarray import DocumentArray, Document
from executors import PdfPreprocessor, ChunkSentencizer, DebugChunkPrinter, RecurseTags, ChunkMerger
from jina import Flow
from config import PORT, DATA_DIR, NUM_DOCS



def index(directory=DATA_DIR, num_docs=NUM_DOCS):
    docs = DocumentArray.from_files(f"{directory}/*.pdf", recursive=True, size=num_docs)

    flow = (
        Flow(port=PORT, protocol="http")
        .add(uses=PdfPreprocessor, name="processor")
        .add(uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter")
        # .add(uses=TextCleaner, name="cleaner")
        .add(
            uses=ChunkSentencizer, name="chunk_sentencizer"
        )  # Sentencizes text chunks and saves to doc.chunks
        .add(uses=RecurseTags) # add doc.tags to chunk.tags
        .add(uses=ChunkMerger) # copy doc.chunks.chunks to doc.chunks
        .add(
            uses="jinahub://CLIPEncoder",
            install_requirements=True,
            name="encoder",
            uses_with={"traversal_paths": "@c"},
        )
        .add(
            uses="jinahub://SimpleIndexer/v0.15",
            install_requirements=True,
            name="indexer",
            uses_with={"traversal_right": "@c"},
        )
    )

    with flow:
        indexed_docs = flow.index(docs, show_progress=True)

    # for doc in indexed_docs:
        # print(doc.tags)
        # for chunk in doc.chunks:
            # print(chunk.tags)

    return indexed_docs


def search_grpc():
    flow = (
        Flow()
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
    while True:
        string = input("What do you want to search for? > ")
        search_doc = Document(text=string)

        with flow:
            output = flow.search(search_doc)

        print(output)
        matches = output[0].matches

        for doc in matches:
            print(doc.text)
            print(doc.tags)
            print("-" * 10)

def search():
    flow = (
        Flow(protocol="http", port=PORT)
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
@click.option("--num_docs", "-n", default=NUM_DOCS)
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
