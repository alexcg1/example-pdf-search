from docarray import DocumentArray, Document
from executors import PdfPreprocessor
from jina import Flow
from config import PORT, DATA_DIR


def index(data_dir=DATA_DIR):

    docs = DocumentArray.from_files(f"{data_dir}/*.pdf", recursive=True)
    docs.summary()  # shows 1 doc

    flow_chunkify = (
        Flow()
        .add(uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter")
        .add(uses=PdfPreprocessor, name="processor")
    )

    with flow_chunkify as flow:
        docs = flow.index(docs)

    all_doc_chunks = DocumentArray()

    for doc in docs:
        for chunk in doc.chunks:
            chunk.tags["uri"] = doc.uri
        all_doc_chunks.extend(doc.chunks)

    flow_encode = (
        Flow()
        .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
        .add(uses="jinahub://SimpleIndexer", install_requirements=True, name="indexer")
    )

    with flow_encode as flow:
        flow.index(all_doc_chunks)

def search_grpc(string):
    search_doc = Document(text=string)
    flow = (
        Flow()
        .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
        .add(uses="jinahub://SimpleIndexer", install_requirements=True, name="indexer")
    )

    with flow:
        output = flow.search(search_doc)

    for match in output[0].matches:
        print(match.content)
        print(match.tags["uri"])

def search():
    flow = (
        Flow(protocol="http", port=PORT)
        .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
        .add(uses="jinahub://SimpleIndexer", install_requirements=True, name="indexer")
    )

    with flow:
        flow.block()

index()
search_grpc("creative")
