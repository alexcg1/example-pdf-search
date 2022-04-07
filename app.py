from docarray import DocumentArray
from jina import Flow
import os
import numpy

os.remove("pdf_database.db")

data_dir = "./data"

docs = DocumentArray(
    storage="sqlite", config={"connection": "pdf_database.db", "table_name": "pdfs"}
)

pdf_docs = DocumentArray.from_files(f"{data_dir}/*.pdf", recursive=True)
pdf_docs.summary()  # shows 1 doc
docs.extend(pdf_docs)

print(f"Total PDFs in database: {len(docs)}")  # returns 1

flow = (
    Flow().add(
        uses="jinahub://PDFSegmenter", install_requirements=True, name="segmenter"
    )
    .add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")
)

with flow:
    docs = flow.index(docs)


def preproc(doc):
    for chunk in doc.chunks:
        if isinstance(chunk.content, numpy.ndarray):
            chunk.set_image_tensor_shape((224, 224))
            chunk.set_image_tensor_normalization()


for doc in docs:
    preproc(doc)
