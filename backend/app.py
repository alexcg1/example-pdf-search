import pretty_errors
from docarray import DocumentArray, Document
from executors import PdfPreprocessor, PdfMetaDataAdder, TextChunkMerger
from jina import Flow
from config import PORT, DATA_DIR

flow = (
    Flow(port=PORT, protocol="http")
    # .add(uses=PdfPreprocessor, name="processor")
    # .add(uses=PdfMetaDataAdder, name="metadata_adder")
    .add(uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter")
    .add(
        uses=TextChunkMerger, name="chunk_sentencizer"
    )  # Sentencizes text chunks and saves to doc.chunks
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

# docs = DocumentArray.from_files(f"../data/*.pdf", recursive=True)

# with flow:
# indexed_docs = flow.index(docs, show_progress=True)


def index(directory=DATA_DIR):
    docs = DocumentArray.from_files(f"{directory}/*.pdf", recursive=True)

    with flow:
        indexed_docs = flow.index(docs, show_progress=True)

    return indexed_docs


def search_grpc(string):
    search_doc = Document(text=string)
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

    with flow:
        output = flow.search(search_doc)

    for match in output[0].matches:
        print(match.content)
        print("================")


print("=== INDEXING ===")
index()

print("=== SEARCHING ===")
search_grpc("what license should i use?")
