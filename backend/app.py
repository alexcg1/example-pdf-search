import pretty_errors
from docarray import DocumentArray, Document
from executors import PdfPreprocessor, PdfMetaDataAdder
from jina import Flow
from config import PORT, DATA_DIR

flow = (
    Flow()
    .add(uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter")
    # .add(uses=PdfPreprocessor, name="processor")
    # .add(uses=PdfMetaDataAdder, name="metadata_adder")
    .add(
        uses="jinahub://CLIPEncoder",
        install_requirements=True,
        name="encoder",
        uses_with={"traversal_paths": "@c"},
    )
    .add(
        uses="jinahub://SimpleIndexer",
        install_requirements=True,
        name="indexer",
        uses_with={"traversal_right": "@c"},
    )
)


def index(data_dir=DATA_DIR):

    docs = DocumentArray.from_files(f"{data_dir}/*.pdf", recursive=True)
    docs.summary()  # shows 1 doc

    with flow:
        docs = flow.index(docs)

    for chunk in docs[0].chunks:
        print(chunk)


def search_grpc(string):
    search_doc = Document(text=string)
    flow = (
        Flow()
        .add(
            uses="jinahub://CLIPEncoder",
            install_requirements=True,
            name="encoder",
            uses_with={"traversal_paths": "@c"},
        )
        .add(
            uses="jinahub://SimpleIndexer",
            install_requirements=True,
            name="indexer",
            uses_with={"traversal_right:" "@c"},
        )
    )

    with flow:
        output = flow.search(search_doc)

    for match in output[0].matches:
        print(match)
        print(match.content)
        print(match.tags["uri"])

    return output[0].matches


def search():
    flow = (
        Flow(protocol="http", port=PORT)
        .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
        .add(uses="jinahub://SimpleIndexer", install_requirements=True, name="indexer")
    )

    with flow:
        flow.block()


print("=== INDEXING ===")
index()

print("=== SEARCHING ===")
search_grpc("community")
