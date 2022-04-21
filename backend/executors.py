from jina import Executor, requests
from docarray import DocumentArray
import pikepdf
import numpy


def preproc(doc):
    for chunk in doc.chunks:
        if isinstance(chunk.content, numpy.ndarray):
            chunk.set_image_tensor_shape((224, 224))
            chunk.tensor = chunk.tensor.astype(numpy.uint8)
            chunk.set_image_tensor_normalization()
            chunk.convert_image_tensor_to_blob()
            chunk.tags["parent"] = {}
            chunk.tags["parent"]["uri"] = doc.uri


class PdfPreprocessor(Executor):
    @requests(on="/index")
    def process_pdf(self, docs, **kwargs):
        for doc in docs:
            preproc(doc)
            if doc.uri:
                doc.load_uri_to_blob()

class PdfMetaDataAdder(Executor):
    @requests
    def metadata_to_tags(self, docs, **kwargs):
        for doc in docs:
            pdf = pikepdf.Pdf.open(doc.uri)
            doc_info = pdf.docinfo
            for key, value in doc_info.items():
                print(key, ":", value)

class TextChunkMerger(Executor):
    """
    Sentencizes a Document's chunks, then adds /those/ sentences to the Document's chunks (not the chunk's chunks)
    """
    @requests
    def sentencize_text_chunks(self, docs, **kwargs):
        for doc in docs: # level 0 document
            chunks_lvl_1 = DocumentArray() # level 0 is original Document
            for chunk in doc.chunks:
                if chunk.mime_type == "text/plain":
                    chunks_lvl_1.append(chunk)

                    sentencizer = Executor.from_hub("jinahub://Sentencizer")
                    sentencizer.segment(chunks_lvl_1, parameters={})
                    for lvl_1_chunk in chunks_lvl_1:
                        doc.chunks.extend(lvl_1_chunk.chunks) # Extend level 1 chunk DocumentArray with level 2 chunks
