from docarray import DocumentArray
from executors import PdfPreprocessor
from jina import Flow

data_dir = "./data"

docs = DocumentArray.from_files(f"{data_dir}/*.pdf", recursive=True)
docs.summary()  # shows 1 doc

print(f"Total PDFs in database: {len(docs)}")  # returns 1

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
        all_doc_chunks.append(chunk)

flow_encode = Flow().add(uses="jinahub://CLIPEncoder", install_requirements=True, name="encoder")

with flow_encode as flow:
    encoded_chunks = flow.index(all_doc_chunks)

for doc in encoded_chunks:
    print(doc.parent_id)
    print(doc.embedding)
