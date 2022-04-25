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
            # if "metadata" not in doc.tags.keys():
            # doc.tags["metadata"] = {}
            bare_filename = doc.uri.split("/")[-1]
            thumbnail_filename = f"{covers_dir}/{bare_filename}.png"
            subprocess.call(["convert", doc.uri + "[0]", thumbnail_filename])
            doc.tags["cover"] = thumbnail_filename


class TextChunkMerger(Executor):
    """
    Sentencizes a Document's chunks, then adds /those/ sentences to that Document's chunks (not the chunk's chunks)
    """

    @requests(on="/index")
    def sentencize_text_chunks(self, docs, **kwargs):
        for doc in docs:  # level 0 document
            text_chunks = DocumentArray()  # level 0 is original Document
            for chunk in doc.chunks:
                # Set metadata on chunk level
                chunk.tags["parent"] = {"uri": doc.uri}
                chunk.tags["parent"] = chunk.tags["parent"] | doc.tags

                # Create a list of only text chunks
                if chunk.mime_type == "text/plain":
                    text_chunks.append(chunk)

            # Break chunks into sentences
            sentencizer = Executor.from_hub(
                "jinahub://Sentencizer",
                uses_with={
                    "punct_chars": ["\n\n", "\r\r", "."], 
                    "min_sent_len": 20
                },
            )
            sentencizer.segment(text_chunks, parameters={})

            # Extend level 1 chunk DocumentArray with the sentences
            for text_chunk in text_chunks:
                doc.chunks.extend(text_chunk.chunks)

            # Try to suck in metadata from the chunk's parent chunk (which should now be on same chunk-level)
            for chunk in doc.chunks:
                # Try to get metadata from higher-level chunks
                try:
                    parent = doc.chunks[chunk.parent_id]
                    chunk.tags = chunk.tags | parent.tags
                except:
                    pass


class DebugChunkPrinter(Executor):
    @requests
    def print_chunks(self, docs, **kwargs):
        for doc in docs:
            print(f"{doc.uri} has {len(doc.chunks)} chunks")
            for chunk in doc.chunks:
                print(f"{len(chunk.text)}: {chunk.text}")
                print(10 * "=")


class TextCleaner(Executor):
    @requests(on="/index")
    def clean_text(self, docs, **kwargs):
        """
        Substitute letters because of weirdness in PDF to text conversion
        """
        substitutions = [
            # pre-emptively convert deliberate paragraph breaks into sentence-ends so they dont get caught by next entry in the list
            {"old": "\n\n", "new": ". "},
            {"old": "\r\r", "new": ". "},

            # Remove incidental linebreaks caused by conversion
            {"old": "\n", "new": " "},
            {"old": "\r", "new": " "},
        ]
        for doc in docs:
            for chunk in doc.chunks:
                if chunk.text:
                    for sub in substitutions:
                        chunk.text = chunk.text.replace(sub["old"], sub["new"])
