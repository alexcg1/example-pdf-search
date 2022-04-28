from config import METADATA_DIR
from jina import Executor, requests
import pikepdf
import subprocess
import os
import re
from dateutil.tz import tzutc, tzoffset
import datetime
import numpy as np
import yaml

CONFIG_FILE = "../config.yml"

with open(CONFIG_FILE) as file:
    config = yaml.safe_load(file.read())

pdf_date_pattern = re.compile(
    "".join(
        [
            r"(D:)?",
            r"(?P<year>\d\d\d\d)",
            r"(?P<month>\d\d)",
            r"(?P<day>\d\d)",
            r"(?P<hour>\d\d)",
            r"(?P<minute>\d\d)",
            r"(?P<second>\d\d)",
            r"(?P<tz_offset>[+-zZ])?",
            r"(?P<tz_hour>\d\d)?",
            r"'?(?P<tz_minute>\d\d)?'?",
        ]
    )
)


def transform_date(date_str):
    """
    Convert a pdf date such as "D:20120321183444+07'00'" into a usable datetime
    http://www.verypdf.com/pdfinfoeditor/pdf-date-format.htm
    (D:YYYYMMDDHHmmSSOHH'mm')
    :param date_str: pdf date string
    :return: datetime object
    """
    global pdf_date_pattern
    match = re.match(pdf_date_pattern, date_str)
    if match:
        date_info = match.groupdict()

        for k, v in date_info.items():  # transform values
            if v is None:
                pass
            elif k == "tz_offset":
                date_info[k] = v.lower()  # so we can treat Z as z
            else:
                date_info[k] = int(v)

        if date_info["tz_offset"] in ("z", None):  # UTC
            date_info["tzinfo"] = tzutc()
        else:
            multiplier = 1 if date_info["tz_offset"] == "+" else -1
            date_info["tzinfo"] = tzoffset(
                None,
                multiplier
                * (3600 * date_info["tz_hour"] + 60 * date_info["tz_minute"]),
            )

        for k in ("tz_offset", "tz_hour", "tz_minute"):  # no longer needed
            del date_info[k]

        return datetime.datetime(**date_info)


def uri_to_title(uri):
    title = uri.split(".")[-2].split("/")[-1]

    return title


class PdfPreprocessor(Executor):
    """
    - Generates cover and stores its uri in tag
    - Converts PDF to blob
    - Gets PDF metadata, stores as Document tags
    - Generates title from uri if it doesn't exist
    """

    @requests(on="/index")
    def preprocess_pdf(self, docs, **kwargs):
        covers_dir = f"{METADATA_DIR}/covers"
        if not os.path.isdir(covers_dir):
            os.makedirs(covers_dir)

        for doc in docs:
            # Load to blob
            if doc.uri:
                doc.load_uri_to_blob()

            pdf = pikepdf.Pdf.open(doc.uri)
            doc_info = dict(pdf.docinfo)
            for key, value in doc_info.items():
                new_key_name = str(key).lower()[1:]
                doc.tags[new_key_name] = str(value)

            # Convert weird PDF date to real date time
            datetime_keys = ["moddate", "creationdate"]
            for key, value in doc.tags.items():
                if key in datetime_keys:
                    doc.tags[key] = str(transform_date(value))

            if "title" not in doc.tags.keys():
                # Convert doc.uri to readable title
                doc.tags["title"] = uri_to_title(doc.uri)

            # Create cover image
            bare_filename = doc.uri.split("/")[-1]
            thumbnail_filename = f"{covers_dir}/{bare_filename}.png"
            subprocess.call(["convert", doc.uri + "[0]", thumbnail_filename])
            doc.tags["cover"] = thumbnail_filename


class RecurseTags(Executor):
    """
    Bubble Document tags to doc.chunk["parent"] dict
    """

    @requests(on="/index")
    def copy_doc_tags_to_chunk_tags(self, docs, **kwargs):
        for doc in docs:
            for chunk in doc.chunks["@c, cc, ccc"]:
                if not "parent" in chunk.tags:
                    chunk.tags["parent"] = doc.tags
                    chunk.tags["parent"]["uri"] = doc.uri


class ChunkSentencizer(Executor):
    """
    Cleans up and sentencizes a Document's chunks
    """

    @requests(on="/index")
    def sentencize_text_chunks(self, docs, **kwargs):
        for doc in docs:
            sentencizer = Executor.from_hub(
                "jinahub://SpacySentencizer/v0.4",
                install_requirements=True,
            )
            sentencizer.segment(doc.chunks, parameters={})


class ChunkMerger(Executor):
    """
    - Remove original chunk if doc.text exists (bc we only want the sentencized versions)
    - Merges all doc.chunks.chunks to doc.chunks
    """

    @requests(on="/index")
    def merge_chunks(self, docs, **kwargs):
        for doc in docs:  # level 0 document
            # Remove original text chunks from doc.chunks (non-recursive)
            # Because original text was from huge lumps, not sentencized
            for chunk in doc.chunks:
                if doc.text:
                    docs.pop(chunk.id)
            doc.chunks = doc.chunks[...]


class ImageNormalizer(Executor):
    @requests(on="/index")
    def normalize_chunks(self, docs, **kwargs):
        for doc in docs:
            for chunk in doc.chunks[...]:
                if chunk.blob:
                    chunk.convert_blob_to_image_tensor()

                if hasattr(chunk, "tensor"):
                    if chunk.tensor is not None:
                        image_chunk_dir = f"{config['data_dir']}/image_chunks"
                        if not os.path.isdir(image_chunk_dir):
                            os.makedirs(image_chunk_dir)
                        chunk.save_image_tensor_to_file(
                            f"{image_chunk_dir}/{chunk.id}.png"
                        )
                        chunk.tags["image_uri"] = f"{image_chunk_dir}/{chunk.id}.png"
                        chunk.tensor = chunk.tensor.astype(np.uint8)
                        chunk.set_image_tensor_shape((64, 64))
                        chunk.set_image_tensor_normalization()

    # @requests(on="/search")
    # def normalize_doc(self, docs, **kwargs):
    # for doc in docs:
    # if doc.blob:
    # doc.convert_blob_to_image_tensor().set_image_tensor_shape(
    # 64, 64
    # ).set_image_tensor_normalization()


class DebugChunkPrinter(Executor):
    """
    Print debug statements
    """

    @requests
    def print_chunks(self, docs, **kwargs):
        print(docs)
        print([doc for doc in docs])
        levels = ["@c"]
        for level in levels:
            print(f"Chunks at {level}")
            print("=" * 10)
            # print(level)
            for doc in docs[level]:
                print(doc)
                # print(f"Type: {type(doc.content)}")
                # print(f"Mimetype: {doc.mime_type}")
                try:
                    print(doc.tensor.shape)
                except:
                    pass
                # if doc.tensor:
                # print(doc.tensor.shape)
                # if doc.embedding:
                # print(f"Embedding shape: {doc.embedding.shape}")
                # else:
                # print("Embedding: None")
                # print(f"Tags: {doc.tags}")
                # # print(doc.content)
                print("-" * 10)


class EmptyDeleter(Executor):
    """
    Delete docs with empty embeddings. These shouldn't exist but sometimes they fall through the gaps
    """

    @requests
    def delete_empty(self, docs, **kwargs):
        for doc in docs:
            for chunk in doc.chunks:
                if chunk.embedding is None:
                    doc.chunks.pop(chunk.id)
