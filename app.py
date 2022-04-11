from docarray import DocumentArray
from executors import PdfPreprocessor
from jina import Flow
import os
import numpy

data_dir = "./data"

docs = DocumentArray.from_files(f"{data_dir}/*.pdf", recursive=True)
docs.summary()  # shows 1 doc

print(f"Total PDFs in database: {len(docs)}")  # returns 1

flow = (
    Flow()
    .add(uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter")
    .add(uses=PdfPreprocessor, name="processor")
    .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
    # .add(uses="jinahub://SimpleIndexer", install_requirements=True, name="indexer")
)

with flow:
    docs = flow.index(docs)

for doc in docs:
    print(doc)
