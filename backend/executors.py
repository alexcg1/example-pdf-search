from config import METADATA_DIR
from jina import Executor, requests
from docarray import DocumentArray
import pikepdf
import numpy
import subprocess
import os


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
    def uri_to_blob(self, docs, **kwargs):
        for doc in docs:
            preproc(doc)
            if doc.uri:
                doc.load_uri_to_blob()

    @requests(on="/index")
    def metadata_to_tags(self, docs, **kwargs):
        for doc in docs:
            if "metadata" not in doc.tags.keys():
                doc.tags["metadata"] = {}

            pdf = pikepdf.Pdf.open(doc.uri)
            doc_info = pdf.docinfo
            for key, value in doc_info.items():
                print(key, ":", value)

    @requests(on="/index")
    def get_thumbnail(self, docs, **kwargs):
        covers_dir = f"{METADATA_DIR}/covers"
        if not os.path.isdir(covers_dir):
            os.makedirs(covers_dir)

        for doc in docs:
            if "metadata" not in doc.tags.keys():
                doc.tags["metadata"] = {}
            bare_filename = doc.uri.split("/")[-1]
            thumbnail_filename = f"{covers_dir}/{bare_filename}.png"
            subprocess.call(["convert", doc.uri + "[0]", thumbnail_filename])
            doc.tags["metadata"]["cover"] = thumbnail_filename


class TextChunkMerger(Executor):
    """
    Sentencizes a Document's chunks, then adds /those/ sentences to that Document's chunks (not the chunk's chunks)
    """

    @requests(on="/index")
    def sentencize_text_chunks(self, docs, **kwargs):
        for doc in docs:  # level 0 document
            chunks_lvl_1 = DocumentArray()  # level 0 is original Document
            for chunk in doc.chunks:
                if chunk.mime_type == "text/plain":
                    chunk.tags["parent"] = {}
                    chunk.tags["parent"]["uri"] = doc.uri
                    chunks_lvl_1.append(chunk)

            # Break chunks into sentences
            sentencizer = Executor.from_hub("jinahub://Sentencizer")
            sentencizer.segment(chunks_lvl_1, parameters={})

            # Extend level 1 chunk DocumentArray with the sentences
            for lvl_1_chunk in chunks_lvl_1:
                doc.chunks.extend(lvl_1_chunk.chunks)
